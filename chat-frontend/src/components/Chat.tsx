import { useState, useEffect, useRef } from 'react';
import { api, type User } from '../services/api';
import SignPDFModal from './SignPDFModal';

interface ChatProps {
  user: User;
  token: string;
  onLogout: () => void;
}

interface ChatMessage {
  type: string;
  apodo?: string;
  message?: string;
  timestamp?: string;
  [key: string]: any;
}

const Chat = ({ user, token, onLogout }: ChatProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showSignModal, setShowSignModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const websocket = new WebSocket(`${api.getWebSocketURL()}?token=${token}`);

    websocket.onopen = () => {
      console.log('WebSocket conectado');
      setIsConnected(true);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Mensaje recibido:', data);

      if (data.type === 'welcome') {
        if (data.history) {
          setMessages(data.history);
        }
      } else {
        setMessages((prev) => [...prev, data]);
      }
    };

    websocket.onerror = (error) => {
      console.error('Error en WebSocket:', error);
    };

    websocket.onclose = () => {
      console.log('WebSocket desconectado');
      setIsConnected(false);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, [token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputMessage.trim() || !ws || !isConnected) return;

    ws.send(
      JSON.stringify({
        type: 'chat',
        message: inputMessage,
      })
    );

    setInputMessage('');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    if (ws) {
      ws.close();
    }
    onLogout();
  };

  return (
    <div className="vh-100 d-flex flex-column" style={{ backgroundColor: '#131313' }}>
      <nav className="navbar navbar-dark px-3 py-2" style={{ backgroundColor: '#22272B', minHeight: '60px' }}>
        <div className="container-fluid">
          <div className="d-flex align-items-center">
            <img src="/src/assets/img/logo_mini.png" alt="CHATSEC" height="35" className="me-2" />
            <span className="navbar-brand mb-0 h1" style={{ color: '#7416F0' }}>
              CHATSEC
            </span>
          </div>

          <div className="d-flex align-items-center">
            <div className="dropdown">
              <button className="btn btn-link text-decoration-none d-flex align-items-center p-0" onClick={() => setShowUserMenu(!showUserMenu)} style={{ color: '#fff' }}>
                <span className="me-2">{user.apodo || user.nombre_google || user.email}</span>
                <div
                  className="rounded-circle d-flex align-items-center justify-content-center me-2"
                  style={{
                    width: '35px',
                    height: '35px',
                    backgroundColor: '#7416F0',
                    color: '#fff',
                    fontWeight: 'bold',
                    fontSize: '16px',
                  }}
                >
                  {(user.apodo || user.nombre_google || user.email)[0].toUpperCase()}
                </div>
                <i className="bi bi-chevron-down"></i>
              </button>

              {showUserMenu && (
                <div
                  className="dropdown-menu dropdown-menu-end show"
                  style={{
                    backgroundColor: '#1C1E21',
                    border: '1px solid #444',
                    marginTop: '10px',
                  }}
                >
                  <button className="dropdown-item" onClick={handleLogout} style={{ color: '#fff' }}>
                    <i className="bi bi-box-arrow-right me-2"></i>
                    Cerrar sesión
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      <div className="container-fluid flex-grow-1 overflow-hidden">
        <div className="row h-100">
          <div className="col-3 h-100 p-0" style={{ backgroundColor: '#1C1E21' }}>
            <div className="p-3">
              <h6 className="text-white mb-3">Grupo de Chat 1</h6>
              <div className="d-flex align-items-center text-white-50">
                <i className="bi bi-circle-fill me-2" style={{ fontSize: '8px', color: isConnected ? '#28a745' : '#dc3545' }}></i>
                <small>{isConnected ? 'Conectado' : 'Desconectado'}</small>
              </div>
            </div>
          </div>

          <div className="col-9 h-100 d-flex flex-column">
            <div className="flex-grow-1 overflow-auto p-3" style={{ backgroundColor: '#131313' }}>
              {messages.map((msg, index) => {
                const isCurrentUser = msg.apodo === user.apodo || msg.apodo === user.nombre_google;
                const avatarColor = isCurrentUser ? '#7416F0' : '#7C148C';
                const nameColor = isCurrentUser ? '#7416F0' : '#B84DFF';

                return (
                  <div key={index} className="mb-3">
                    {msg.type === 'chat' && (
                      <div className="d-flex">
                        <div
                          className="rounded-circle d-flex align-items-center justify-content-center me-2 flex-shrink-0"
                          style={{
                            width: '40px',
                            height: '40px',
                            backgroundColor: avatarColor,
                            color: '#fff',
                            fontWeight: 'bold',
                          }}
                        >
                          {(msg.apodo || '?')[0].toUpperCase()}
                        </div>
                        <div className="flex-grow-1">
                          <div className="d-flex align-items-baseline mb-1">
                            <span className="fw-bold me-2" style={{ color: nameColor }}>
                              {msg.apodo}
                            </span>
                            <small style={{ color: '#666' }}>
                              {msg.timestamp
                                ? new Date(msg.timestamp).toLocaleTimeString('es-ES', {
                                    hour: '2-digit',
                                    minute: '2-digit',
                                  })
                                : ''}
                            </small>
                          </div>
                          <div style={{ color: '#fff' }}>{msg.message}</div>
                        </div>
                      </div>
                    )}

                    {msg.type === 'user_joined' && (
                      <div className="text-center">
                        <small style={{ color: '#666' }}>
                          <i className="bi bi-box-arrow-in-right me-1"></i>
                          {msg.apodo} se unió al chat
                        </small>
                      </div>
                    )}

                    {msg.type === 'user_left' && (
                      <div className="text-center">
                        <small style={{ color: '#666' }}>
                          <i className="bi bi-box-arrow-left me-1"></i>
                          {msg.apodo} salió del chat
                        </small>
                      </div>
                    )}

                    {msg.type === 'system' && (
                      <div className="text-center">
                        <small style={{ color: '#7416F0' }}>{msg.message}</small>
                      </div>
                    )}
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>

            <div className="p-3" style={{ backgroundColor: '#1C1E21' }}>
              <form onSubmit={handleSendMessage}>
                <div className="input-group">
                  <button
                    type="button"
                    className="btn"
                    style={{
                      backgroundColor: '#7416F0',
                      color: '#fff',
                      border: 'none',
                    }}
                    onClick={() => setShowSignModal(true)}
                  >
                    <i className="bi bi-plus-lg"></i>
                  </button>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Enviar mensaje..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    disabled={!isConnected}
                    style={{
                      backgroundColor: '#22272B',
                      color: '#fff',
                      border: '1px solid #444',
                    }}
                  />
                  <button
                    type="submit"
                    className="btn"
                    disabled={!isConnected || !inputMessage.trim()}
                    style={{
                      backgroundColor: '#7416F0',
                      color: '#fff',
                      border: 'none',
                    }}
                  >
                    <i className="bi bi-send"></i>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      {showSignModal && <SignPDFModal user={user} onClose={() => setShowSignModal(false)} />}
    </div>
  );
};

export default Chat;
