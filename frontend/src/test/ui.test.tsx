import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GreenOrb } from '../components/voice/GreenOrb';
import { MrGreenAssistantVisual } from '../components/voice/MrGreenAssistantVisual';
import { BottomVoiceControl } from '../components/voice/BottomVoiceControl';
import { Header } from '../components/layout/Header';
import { ChatInput } from '../components/chat/ChatInput';
import { ChatMessage } from '../components/chat/ChatMessage';
import { HistoryDrawer } from '../components/layout/HistoryDrawer';

describe('UI — MrGreenAssistantVisual Component', () => {
  it('renders in IDLE state with "Ready when you are" status', () => {
    render(<MrGreenAssistantVisual voiceState="IDLE" />);
    expect(screen.getByText('Ready when you are')).toBeInTheDocument();
  });

  it('renders in LISTENING state with transcript caption', () => {
    render(
      <MrGreenAssistantVisual
        voiceState="LISTENING"
        isListening={true}
        interimTranscript="Hello Green"
      />
    );
    expect(screen.getByText('Listening...')).toBeInTheDocument();
    expect(screen.getByText('"Hello Green"')).toBeInTheDocument();
  });

  it('renders in THINKING state', () => {
    render(<MrGreenAssistantVisual voiceState="THINKING" isProcessing={true} />);
    expect(screen.getByText('Thinking...')).toBeInTheDocument();
  });

  it('renders in SPEAKING state with response caption', () => {
    render(
      <MrGreenAssistantVisual
        voiceState="ASSISTANT_SPEAKING"
        isSpeaking={true}
        lastResponse="I am online and ready."
      />
    );
    expect(screen.getByText('Speaking...')).toBeInTheDocument();
    expect(screen.getByText('I am online and ready.')).toBeInTheDocument();
  });

  it('renders in ERROR state with retry button', () => {
    const onRetry = vi.fn();
    render(
      <MrGreenAssistantVisual
        voiceState="ERROR"
        isOnline={false}
        onRetry={onRetry}
      />
    );
    expect(screen.getByText('Connection issue')).toBeInTheDocument();
    const retryBtn = screen.getByRole('button', { name: /retry connection/i });
    expect(retryBtn).toBeInTheDocument();
    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalled();
  });
});

describe('UI — BottomVoiceControl Component', () => {
  it('renders circular mic button and toggles voice on click', () => {
    const onToggle = vi.fn();
    render(
      <BottomVoiceControl
        isListening={false}
        isSpeaking={false}
        isProcessing={false}
        speechSupported={true}
        onToggleListen={onToggle}
        onStopSpeaking={() => {}}
        onSendMessage={() => {}}
      />
    );

    const micBtn = screen.getByRole('button', { name: /start listening/i });
    expect(micBtn).toBeInTheDocument();
    fireEvent.click(micBtn);
    expect(onToggle).toHaveBeenCalled();
  });

  it('renders stop button when speaking and calls onStopSpeaking', () => {
    const onStop = vi.fn();
    render(
      <BottomVoiceControl
        isListening={false}
        isSpeaking={true}
        isProcessing={false}
        speechSupported={true}
        onToggleListen={() => {}}
        onStopSpeaking={onStop}
        onSendMessage={() => {}}
      />
    );

    const stopBtn = screen.getByRole('button', { name: /stop speaking/i });
    expect(stopBtn).toBeInTheDocument();
    fireEvent.click(stopBtn);
    expect(onStop).toHaveBeenCalled();
  });

  it('reveals text fallback input and sends message', () => {
    const onSend = vi.fn();
    render(
      <BottomVoiceControl
        isListening={false}
        isSpeaking={false}
        isProcessing={false}
        speechSupported={true}
        onToggleListen={() => {}}
        onStopSpeaking={() => {}}
        onSendMessage={onSend}
      />
    );

    const toggleBtn = screen.getByRole('button', { name: /toggle text entry fallback/i });
    fireEvent.click(toggleBtn);

    const input = screen.getByPlaceholderText(/type a message to mr.green/i);
    expect(input).toBeInTheDocument();
    fireEvent.change(input, { target: { value: 'Testing message' } });

    const sendBtn = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(sendBtn);
    expect(onSend).toHaveBeenCalledWith('Testing message');
  });
});

describe('UI — GreenOrb Component', () => {
  it('renders GreenOrb in IDLE state with accessible button', () => {
    render(
      <GreenOrb
        state="IDLE"
        isListening={false}
        onToggleListen={() => {}}
      />
    );

    expect(screen.getByText('READY')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /start voice input/i })).toBeInTheDocument();
  });

  it('renders GreenOrb in LISTENING state with stop button', () => {
    render(
      <GreenOrb
        state="LISTENING"
        isListening={true}
        interimTranscript="Testing voice"
        onToggleListen={() => {}}
      />
    );

    expect(screen.getByText('LISTENING...')).toBeInTheDocument();
    expect(screen.getByText('"Testing voice"')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /stop voice input/i })).toBeInTheDocument();
  });

  it('renders GreenOrb in THINKING and SPEAKING states', () => {
    const { rerender } = render(
      <GreenOrb
        state="THINKING"
        isListening={false}
      />
    );
    expect(screen.getByText('THINKING...')).toBeInTheDocument();

    rerender(
      <GreenOrb
        state="SPEAKING"
        isListening={false}
      />
    );
    expect(screen.getByText('SPEAKING...')).toBeInTheDocument();
  });

  it('renders GreenOrb in ERROR and OFFLINE states', () => {
    const { rerender } = render(
      <GreenOrb
        state="ERROR"
        isListening={false}
      />
    );
    expect(screen.getByText('ATTENTION')).toBeInTheDocument();

    rerender(
      <GreenOrb
        state="OFFLINE"
        isListening={false}
      />
    );
    expect(screen.getByText('OFFLINE')).toBeInTheDocument();
  });
});

describe('UI — Header & Connection Status', () => {
  it('displays ONLINE status pill when healthy', () => {
    render(
      <Header
        isOnline={true}
        onNewChat={() => {}}
        onOpenHistory={() => {}}
        onOpenSettings={() => {}}
      />
    );

    expect(screen.getByText('LIVE')).toBeInTheDocument();
    expect(screen.getByText('MR.GREEN')).toBeInTheDocument();
  });

  it('displays OFFLINE status pill when server is unreachable', () => {
    render(
      <Header
        isOnline={false}
        onNewChat={() => {}}
        onOpenHistory={() => {}}
        onOpenSettings={() => {}}
      />
    );

    expect(screen.getByText('OFFLINE')).toBeInTheDocument();
  });

  it('triggers new chat callback when clicked', () => {
    const onNewChat = vi.fn();
    render(
      <Header
        isOnline={true}
        onNewChat={onNewChat}
        onOpenHistory={() => {}}
        onOpenSettings={() => {}}
      />
    );

    const newChatBtn = screen.getByRole('button', { name: /start new chat/i });
    fireEvent.click(newChatBtn);
    expect(onNewChat).toHaveBeenCalled();
  });
});

describe('UI — Chat Input & Voice Controls', () => {
  it('renders input field and sends typed message', () => {
    const onSendMessage = vi.fn();
    render(
      <ChatInput
        onSendMessage={onSendMessage}
        isListening={false}
        isSpeaking={false}
        isProcessing={false}
        speechSupported={true}
        onToggleListen={() => {}}
        onStopSpeaking={() => {}}
        voiceEnabled={true}
        onToggleVoice={() => {}}
        activeLanguage="en-IN"
        onChangeLanguage={() => {}}
      />
    );

    const input = screen.getByLabelText('Type message to MR.GREEN');
    fireEvent.change(input, { target: { value: 'Hello MR.GREEN' } });

    const sendBtn = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(sendBtn);

    expect(onSendMessage).toHaveBeenCalledWith('Hello MR.GREEN');
  });

  it('shows Stop Speaking button when TTS is playing', () => {
    const onStopSpeaking = vi.fn();
    render(
      <ChatInput
        onSendMessage={() => {}}
        isListening={false}
        isSpeaking={true}
        isProcessing={false}
        speechSupported={true}
        onToggleListen={() => {}}
        onStopSpeaking={onStopSpeaking}
        voiceEnabled={true}
        onToggleVoice={() => {}}
        activeLanguage="en-IN"
        onChangeLanguage={() => {}}
      />
    );

    const stopBtn = screen.getByRole('button', { name: /stop speaking/i });
    expect(stopBtn).toBeInTheDocument();
    fireEvent.click(stopBtn);
    expect(onStopSpeaking).toHaveBeenCalled();
  });
});

describe('UI — Chat Messages & Tool Activity', () => {
  it('renders user and assistant messages with timestamps', () => {
    const userMsg = {
      id: '1',
      role: 'user' as const,
      content: 'What is 250 * 40?',
      timestamp: '10:00 AM',
    };
    const asstMsg = {
      id: '2',
      role: 'assistant' as const,
      content: '250 * 40 = 10,000',
      timestamp: '10:01 AM',
      toolActivities: [
        {
          id: 'tool-1',
          toolName: 'calculator',
          durationMs: 14,
        },
      ],
    };

    render(
      <div>
        <ChatMessage message={userMsg} />
        <ChatMessage message={asstMsg} />
      </div>
    );

    expect(screen.getByText('What is 250 * 40?')).toBeInTheDocument();
    expect(screen.getByText('250 * 40 = 10,000')).toBeInTheDocument();
    expect(screen.getByText(/Used 1 tool/i)).toBeInTheDocument();
  });
});

describe('UI — History Drawer', () => {
  it('renders history drawer and handles conversation selection', () => {
    const onClose = vi.fn();
    const onNewChat = vi.fn();

    render(
      <HistoryDrawer
        isOpen={true}
        onClose={onClose}
        activeConversationId={null}
        onSelectConversation={() => {}}
        onNewChat={onNewChat}
      />
    );

    expect(screen.getByText('Conversations')).toBeInTheDocument();
    const newChatBtn = screen.getByRole('button', { name: /\+ new chat/i });
    fireEvent.click(newChatBtn);
    expect(onNewChat).toHaveBeenCalled();
  });
});
