"""
MR.GREEN — Agent Core

The main agent loop that orchestrates understanding, planning,
execution, observation, and verification.

Agent Loop:
    USER REQUEST → UNDERSTAND → PLAN → EXECUTE → OBSERVE → VERIFY → DONE/REPLAN

Every agent run has:
- Maximum iterations (prevents infinite loops)
- Timeout
- Execution logging
- Error handling
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from app.agent.executor import Executor
from app.agent.observer import Observer
from app.agent.planner import ActionType, Planner
from app.agent.verifier import Verifier
from app.ai.provider import AIMessage, AIProvider
from app.config import get_settings
from app.database.models import (
    AgentRun,
    AgentRunStatus,
    AgentStep,
    Conversation,
    Message,
    MessageRole,
)
from app.memory.memory_manager import MemoryManager
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

# System prompt that defines MR.GREEN's identity and behavior
SYSTEM_PROMPT = """You are MR.GREEN, a personal AI assistant created by Gowtham.

Your core traits:
- You are helpful, direct, and intelligent
- You remember user preferences and adapt your responses accordingly
- You are honest about your limitations
- You respond in a way that matches the user's communication style

Your name is MR.GREEN (or Green). When introducing yourself, use this name.

{memory_context}

Current date: {current_date}
"""


@dataclass
class AgentResponse:
    """The final response from the agent."""
    content: str
    conversation_id: str
    message_id: str
    extracted_memories: list[dict[str, Any]] = field(default_factory=list)
    agent_run_id: str | None = None
    iterations: int = 0
    duration_ms: int = 0


class Agent:
    """
    The main MR.GREEN agent.

    Orchestrates the full agent loop:
    1. Receive user message
    2. Load memory context
    3. Plan response strategy
    4. Execute (generate response / call tools)
    5. Observe results
    6. Verify quality
    7. Return response or replan

    Safety:
    - Maximum iteration limit
    - Timeout enforcement
    - Full execution logging
    - Error handling at every step
    """

    def __init__(
        self,
        ai_provider: AIProvider,
        tool_registry: ToolRegistry,
        db_session: AsyncSession,
        memory_manager: MemoryManager,
    ):
        self.ai_provider = ai_provider
        self.tool_registry = tool_registry
        self.db = db_session
        self.memory = memory_manager

        settings = get_settings()
        self.max_iterations = settings.max_agent_iterations
        self.timeout_seconds = settings.agent_timeout_seconds

        # Sub-components
        self.planner = Planner()
        self.executor = Executor(ai_provider, tool_registry, settings.tool_timeout_seconds)
        self.observer = Observer()
        self.verifier = Verifier()

    async def process_message(
        self,
        user_message: str,
        conversation_id: str | None = None,
    ) -> AgentResponse:
        """
        Process a user message through the full agent loop.

        Args:
            user_message: The user's input text.
            conversation_id: Existing conversation ID, or None for a new conversation.

        Returns:
            AgentResponse with the final response and metadata.
        """
        start_time = time.monotonic()

        # Get or create conversation
        conversation_id = conversation_id or str(ULID())
        conversation = await self._get_or_create_conversation(conversation_id)

        # Store user message
        user_msg_id = str(ULID())
        user_msg = Message(
            id=user_msg_id,
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_message,
        )
        self.db.add(user_msg)
        await self.db.flush()

        # Create agent run record
        agent_run = AgentRun(
            id=str(ULID()),
            conversation_id=conversation_id,
            trigger_message_id=user_msg_id,
            status=AgentRunStatus.RUNNING,
            max_iterations=self.max_iterations,
        )
        self.db.add(agent_run)
        await self.db.flush()

        # Process through memory system (extracts memories from user message)
        extracted_memories = await self.memory.add_user_message(
            content=user_message,
            message_id=user_msg_id,
            session_id=conversation_id,
        )

        try:
            # Run the agent loop
            response_content = await self._run_loop(
                user_message=user_message,
                agent_run=agent_run,
                conversation_id=conversation_id,
            )

            # Store assistant response
            assistant_msg_id = str(ULID())
            assistant_msg = Message(
                id=assistant_msg_id,
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=response_content,
            )
            self.db.add(assistant_msg)

            # Add to short-term memory
            await self.memory.add_assistant_message(response_content, assistant_msg_id)

            # Log the interaction
            duration_ms = int((time.monotonic() - start_time) * 1000)
            await self.memory.daily_logger.log_chat(
                session_id=conversation_id,
                user_message=user_message,
                assistant_response=response_content,
                duration_ms=duration_ms,
            )

            # Update agent run status
            agent_run.status = AgentRunStatus.COMPLETED
            agent_run.completed_at = datetime.now(timezone.utc)

            # Update conversation timestamp
            conversation.updated_at = datetime.now(timezone.utc)

            return AgentResponse(
                content=response_content,
                conversation_id=conversation_id,
                message_id=assistant_msg_id,
                extracted_memories=extracted_memories,
                agent_run_id=agent_run.id,
                iterations=agent_run.iterations,
                duration_ms=duration_ms,
            )

        except Exception as e:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error_message = str(e)
            agent_run.completed_at = datetime.now(timezone.utc)

            await self.memory.daily_logger.log_error(
                description="Agent loop failed",
                error=str(e),
                session_id=conversation_id,
            )

            logger.error("Agent loop failed: %s", str(e))
            raise

    async def _run_loop(
        self,
        user_message: str,
        agent_run: AgentRun,
        conversation_id: str,
    ) -> str:
        """
        The core agent loop with iteration limits and safety checks.

        Returns the final response content.
        """
        for iteration in range(self.max_iterations):
            agent_run.iterations = iteration + 1

            # Step 1: Plan
            plan = await self.planner.plan(
                user_message=user_message,
                available_tools=self.tool_registry.list_names(),
            )

            # Log the planning step
            step = AgentStep(
                id=str(ULID()),
                agent_run_id=agent_run.id,
                step_number=iteration + 1,
                action_type="plan",
                input_data={"user_message": user_message},
                output_data={"reasoning": plan.reasoning},
            )
            self.db.add(step)

            if plan.is_simple_response:
                # Step 2: Execute — generate AI response
                response = await self._generate_response(user_message, conversation_id)

                # Step 3: Observe
                observation = await self.observer.observe_response(response)

                if not observation.success and observation.should_continue:
                    logger.warning("Response observation failed, retrying: %s", observation.error)
                    continue

                # Step 4: Verify
                verification = await self.verifier.verify_response(user_message, response)

                if not verification.is_valid:
                    logger.warning("Response verification failed: %s", verification.reason)
                    continue

                # Log the response step
                response_step = AgentStep(
                    id=str(ULID()),
                    agent_run_id=agent_run.id,
                    step_number=iteration + 1,
                    action_type="respond",
                    output_data={"response_length": len(response)},
                    success=True,
                )
                self.db.add(response_step)

                return response

            if plan.has_tool_calls:
                for action in plan.actions:
                    if action.action_type == ActionType.TOOL_CALL and action.tool_name:
                        tool_step = AgentStep(
                            id=str(ULID()),
                            agent_run_id=agent_run.id,
                            step_number=iteration + 1,
                            action_type="tool_call",
                            tool_name=action.tool_name,
                            input_data=action.tool_args or {},
                        )
                        self.db.add(tool_step)

                        tool_res = await self.executor.execute_tool(
                            tool_name=action.tool_name,
                            arguments=action.tool_args or {},
                            db_session=self.db,
                            conversation_id=conversation_id,
                            agent_run_id=agent_run.id,
                            agent_step_id=tool_step.id,
                        )

                        tool_step.output_data = tool_res.output if isinstance(tool_res.output, dict) else {"output": tool_res.output}
                        tool_step.success = tool_res.success
                        tool_step.duration_ms = tool_res.duration_ms

                        if not tool_res.success:
                            if "requires approval" in (tool_res.error or "").lower():
                                return f"⚠️ This operation requires explicit human approval before execution: {tool_res.error}"
                            return f"I encountered an error using tool '{action.tool_name}': {tool_res.error}"

                        # Generate informed response incorporating tool results
                        response = await self._generate_response_with_tool_result(
                            user_message=user_message,
                            conversation_id=conversation_id,
                            tool_name=action.tool_name,
                            tool_input=action.tool_args or {},
                            tool_output=tool_res.output,
                        )

                        # Log final response step
                        final_step = AgentStep(
                            id=str(ULID()),
                            agent_run_id=agent_run.id,
                            step_number=iteration + 2,
                            action_type="respond",
                            output_data={"response_length": len(response), "tool_used": action.tool_name},
                            success=True,
                        )
                        self.db.add(final_step)

                        return response

        # If we exhaust all iterations, return a fallback
        logger.warning("Agent exhausted max iterations (%d)", self.max_iterations)
        return "I apologize, but I'm having difficulty processing your request. Could you try rephrasing it?"

    async def _generate_response_with_tool_result(
        self,
        user_message: str,
        conversation_id: str,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
    ) -> str:
        """Generate an AI response synthesizing tool execution results."""
        import json

        # Direct formatters for quick mathematical & time answers
        if tool_name == "calculator" and isinstance(tool_output, dict):
            expr = tool_output.get("expression")
            res = tool_output.get("result")
            if expr is not None and res is not None:
                return f"{expr} = {res}"

        if tool_name == "time" and isinstance(tool_output, dict):
            formatted = tool_output.get("formatted")
            tz = tool_output.get("timezone", "UTC")
            return f"The current time is {formatted} ({tz})."

        # General LLM synthesis with memory context
        memory_context = await self.memory.get_context_for_ai()
        system_prompt = SYSTEM_PROMPT.format(
            memory_context=memory_context or "No stored memories yet.",
            current_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        )
        system_prompt += (
            f"\n\nYou have just executed the '{tool_name}' tool with input: {json.dumps(tool_input)}.\n"
            f"Tool Output:\n{json.dumps(tool_output, default=str)}\n\n"
            "Use this tool output to provide a concise, direct, and helpful answer to the user's question."
        )

        ai_messages = [
            AIMessage(role="user", content=user_message),
        ]

        try:
            ai_resp = await self.executor.generate_response(
                messages=ai_messages,
                system_prompt=system_prompt,
            )
            return ai_resp.content
        except Exception as e:
            logger.warning("AI synthesis failed, falling back to direct tool output format: %s", str(e))
            return f"Tool '{tool_name}' result:\n{json.dumps(tool_output, indent=2, default=str)}"

    async def _generate_response(
        self,
        user_message: str,
        conversation_id: str,
    ) -> str:
        """Generate an AI response with full context injection."""
        # Build memory context
        memory_context = await self.memory.get_context_for_ai()

        # Build system prompt with memory
        system_prompt = SYSTEM_PROMPT.format(
            memory_context=memory_context or "No stored memories yet.",
            current_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        )

        # Get conversation messages
        conversation_messages = await self.memory.get_conversation_messages()

        # Convert to AIMessage objects
        ai_messages = [
            AIMessage(role=msg["role"], content=msg["content"])
            for msg in conversation_messages
        ]

        # Generate response
        response = await self.executor.generate_response(
            messages=ai_messages,
            system_prompt=system_prompt,
        )

        return response.content

    async def _get_or_create_conversation(self, conversation_id: str) -> Conversation:
        """Get an existing conversation or create a new one."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if conversation is None:
            conversation = Conversation(
                id=conversation_id,
                title=None,  # Will be set from first message later
                is_active=True,
            )
            self.db.add(conversation)
            await self.db.flush()

        return conversation
