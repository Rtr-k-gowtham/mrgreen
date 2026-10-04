"""
MR.GREEN — Database Models

All SQLAlchemy ORM models for the application.
Uses pgvector for semantic memory embeddings.
"""

import enum
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# ============================================================
# Enums
# ============================================================

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MemoryType(str, enum.Enum):
    PREFERENCE = "preference"
    FACT = "fact"
    STYLE = "style"
    PROJECT = "project"
    WORKFLOW = "workflow"


class AgentRunStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


# ============================================================
# Conversations & Messages
# ============================================================

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(26), primary_key=True)  # ULID
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSONB, default=dict)

    # Relationships
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(26), primary_key=True)  # ULID
    conversation_id = Column(String(26), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    token_count = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"


# ============================================================
# Memory
# ============================================================

class Memory(Base):
    __tablename__ = "memories"

    id = Column(String(26), primary_key=True)  # ULID
    memory_type = Column(Enum(MemoryType), nullable=False, index=True)
    key = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    source_message_id = Column(String(26), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Memory(id={self.id}, type={self.memory_type}, key={self.key})>"


class MemoryEmbedding(Base):
    __tablename__ = "memory_embeddings"

    id = Column(String(26), primary_key=True)  # ULID
    memory_id = Column(String(26), ForeignKey("memories.id"), nullable=False, index=True)
    embedding = Column(JSONB, nullable=False)  # Stores vector embedding as JSON array of floats
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<MemoryEmbedding(id={self.id}, memory_id={self.memory_id})>"



# ============================================================
# Daily Logs
# ============================================================

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(String(26), primary_key=True)  # ULID
    session_id = Column(String(26), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    tool_name = Column(String(100), nullable=True)
    success = Column(Boolean, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metadata_ = Column("metadata", JSONB, default=dict)

    __table_args__ = (
        Index("ix_daily_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<DailyLog(id={self.id}, event={self.event_type})>"


# ============================================================
# Agent Runs & Steps
# ============================================================

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(26), primary_key=True)  # ULID
    conversation_id = Column(String(26), ForeignKey("conversations.id"), nullable=False, index=True)
    trigger_message_id = Column(String(26), nullable=True)
    status = Column(Enum(AgentRunStatus), default=AgentRunStatus.RUNNING, nullable=False)
    iterations = Column(Integer, default=0)
    max_iterations = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)

    # Relationships
    steps = relationship("AgentStep", back_populates="agent_run", order_by="AgentStep.step_number")

    def __repr__(self) -> str:
        return f"<AgentRun(id={self.id}, status={self.status})>"


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id = Column(String(26), primary_key=True)  # ULID
    agent_run_id = Column(String(26), ForeignKey("agent_runs.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    action_type = Column(String(100), nullable=False)  # "think", "tool_call", "respond"
    input_data = Column(JSONB, default=dict)
    output_data = Column(JSONB, default=dict)
    tool_name = Column(String(100), nullable=True)
    success = Column(Boolean, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    agent_run = relationship("AgentRun", back_populates="steps")

    def __repr__(self) -> str:
        return f"<AgentStep(id={self.id}, step={self.step_number}, action={self.action_type})>"


# ============================================================
# Tools & Capabilities
# ============================================================

class ToolRecord(Base):
    __tablename__ = "tools"

    id = Column(String(26), primary_key=True)  # ULID
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    input_schema = Column(JSONB, default=dict)
    permissions = Column(JSONB, default=list)
    is_builtin = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<ToolRecord(name={self.name})>"


class Capability(Base):
    __tablename__ = "capabilities"

    id = Column(String(26), primary_key=True)  # ULID
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    version = Column(String(20), nullable=False)
    is_approved = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True)
    manifest = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Capability(name={self.name}, version={self.version})>"


class CapabilityVersion(Base):
    __tablename__ = "capability_versions"

    id = Column(String(26), primary_key=True)  # ULID
    capability_id = Column(String(26), ForeignKey("capabilities.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    code_hash = Column(String(64), nullable=False)
    test_passed = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    changelog = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CapabilityVersion(capability_id={self.capability_id}, version={self.version})>"


# ============================================================
# Tool Calls (audit trail)
# ============================================================

class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(String(26), primary_key=True)  # ULID
    agent_step_id = Column(String(26), ForeignKey("agent_steps.id"), nullable=True, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    input_data = Column(JSONB, default=dict)
    output_data = Column(JSONB, default=dict)
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<ToolCall(id={self.id}, tool={self.tool_name})>"


# ============================================================
# Tasks
# ============================================================

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(26), primary_key=True)  # ULID
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending", index=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title})>"


# ============================================================
# Approvals
# ============================================================

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(26), primary_key=True)  # ULID
    resource_type = Column(String(100), nullable=False)  # "capability", "tool_call", etc.
    resource_id = Column(String(26), nullable=False)
    action = Column(String(100), nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    reason = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metadata_ = Column("metadata", JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Approval(id={self.id}, resource={self.resource_type}, status={self.status})>"
