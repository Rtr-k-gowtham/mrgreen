import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GreenOrb } from '../components/voice/GreenOrb';
import { Header } from '../components/layout/Header';
import { ChatInput } from '../components/chat/ChatInput';
import { ChatMessage } from '../components/chat/ChatMessage';
import { HistoryDrawer } from '../components/layout/HistoryDrawer';

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
