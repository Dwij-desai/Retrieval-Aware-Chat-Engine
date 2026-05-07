import { useState, useEffect, useRef } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatSession {
  id: string;
  lastMessage: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [chatId, setChatId] = useState<string>(() => {
    return localStorage.getItem('activeChatId') || 'session-' + Math.floor(Math.random() * 1000);
  });
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    const saved = localStorage.getItem('chatSessions');
    return saved ? JSON.parse(saved) : [];
  });
  const [isLoading, setIsLoading] = useState(false);
  
  const chatLogRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    localStorage.setItem('activeChatId', chatId);
  }, [chatId]);

  useEffect(() => {
    localStorage.setItem('chatSessions', JSON.stringify(sessions));
  }, [sessions]);

  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMessage, chat_id: chatId }),
      });

      if (!response.ok) throw new Error('Failed to fetch');

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
      
      setSessions(prev => {
        const existing = prev.find(s => s.id === chatId);
        if (existing) {
          return prev.map(s => s.id === chatId ? { ...s, lastMessage: userMessage } : s);
        } else {
          return [{ id: chatId, lastMessage: userMessage }, ...prev];
        }
      });
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'SYSTEM_ERROR: CONNECTION_FAILED' }]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const startNewChat = () => {
    const newId = 'session-' + Date.now().toString().slice(-4);
    setChatId(newId);
    setMessages([]);
    inputRef.current?.focus();
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', background: 'transparent' }}>
      <aside className="sidebar">
        <div style={{ padding: '30px 20px 10px', fontSize: '10px', fontWeight: '900', letterSpacing: '0.3em', color: '#555' }}>TERMINAL_INDEX</div>
        <button className="new-chat-btn" onClick={startNewChat}>+ INITIALIZE_NEW</button>
        <nav className="chat-list">
          {sessions.map(s => (
            <div 
              key={s.id} 
              className={'chat-item ' + (s.id === chatId ? 'active' : '')}
              onClick={() => {
                setChatId(s.id);
                setMessages([]); 
              }}
            >
              <span style={{ opacity: 0.3, marginRight: '8px' }}>#</span>
              {s.lastMessage ? (s.lastMessage.slice(0, 20) + '...') : s.id}
            </div>
          ))}
        </nav>
      </aside>

      <main className="main-container">
        <header className="header">
          <div>STATUS: ACTIVE // ID: {chatId}</div>
          <div>CORE_V1.0.0</div>
        </header>

        <div className="chat-log" ref={chatLogRef}>
          {messages.length === 0 && !isLoading && (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.2, fontSize: '12px', letterSpacing: '0.5em' }}>
              WAITING_FOR_INPUT
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className="message-wrapper">
              <div className="message-label">{m.role}</div>
              <div className={'chat-message ' + (m.role === 'user' ? 'user-message' : 'assistant-message')}>
                {m.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message-wrapper">
              <div className="message-label">assistant</div>
              <div className="chat-message assistant-message">
                <span className="cursor"></span>
              </div>
            </div>
          )}
        </div>

        <div className="input-dock">
          <div className="input-container">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter prompt..."
              rows={1}
            />
          </div>
          <div style={{ marginTop: '10px', fontSize: '9px', color: '#444', letterSpacing: '0.1em' }}>
            PRESS [ENTER] TO TRANSMIT // [SHIFT+ENTER] FOR NEWLINE
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;