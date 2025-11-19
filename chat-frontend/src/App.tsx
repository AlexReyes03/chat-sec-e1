import { useState, useEffect } from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import Login from './components/Login';
import NicknameModal from './components/NicknameModal';
import Chat from './components/Chat';
import { api } from './services/api';
import type { User } from './services/api';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

const App = () => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [showNicknameModal, setShowNicknameModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      loadUserData(savedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  const loadUserData = async (tokenValue: string) => {
    try {
      // Verificar que el token exista y no esté vacío
      if (!tokenValue || tokenValue.trim() === '') {
        throw new Error('Token inválido');
      }

      const response = await api.getMe();

      if (!response.success || !response.user) {
        throw new Error('Respuesta inválida del servidor');
      }

      setUser(response.user);
      setToken(tokenValue);

      if (!response.user.apodo) {
        setShowNicknameModal(true);
      }
    } catch (error: any) {
      console.error('Error al cargar datos del usuario:', error);
      // Limpiar el estado de autenticación
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoginSuccess = async (tokenValue: string, userData: User) => {
    setToken(tokenValue);
    setUser(userData);

    if (!userData.apodo) {
      setShowNicknameModal(true);
    }
  };

  const handleNicknameSet = (apodo: string) => {
    if (user) {
      setUser({ ...user, apodo });
    }
    setShowNicknameModal(false);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  };

  if (isLoading) {
    return (
      <div
        className="vh-100 d-flex align-items-center justify-content-center"
        style={{ backgroundColor: '#131313' }}
      >
        <div className="text-center">
          <div className="spinner-border" style={{ color: '#7416F0' }} role="status">
            <span className="visually-hidden">Cargando...</span>
          </div>
          <p className="mt-3" style={{ color: '#fff' }}>
            Cargando CHATSEC...
          </p>
        </div>
      </div>
    );
  }

  if (!token || !user) {
    return (
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <Login onLoginSuccess={handleLoginSuccess} />
      </GoogleOAuthProvider>
    );
  }

  return (
    <>
      <NicknameModal
        show={showNicknameModal}
        onNicknameSet={handleNicknameSet}
      />
      {!showNicknameModal && (
        <Chat
          user={user}
          token={token}
          onLogout={handleLogout}
        />
      )}
    </>
  );
};

export default App;
