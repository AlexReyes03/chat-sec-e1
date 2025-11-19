import { useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { api, type User } from '../services/api';

interface LoginProps {
  onLoginSuccess: (token: string, user: User) => void;
}

const Login = ({ onLoginSuccess }: LoginProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [error, setError] = useState('');
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [isGoogleHovered, setIsGoogleHovered] = useState(false);

  const isFormValid = () => {
    const emailTrimmed = email.trim();
    const passwordTrimmed = password.trim();

    if (!emailTrimmed || !passwordTrimmed) {
      return false;
    }

    if (isRegisterMode) {
      const confirmPasswordTrimmed = confirmPassword.trim();
      return confirmPasswordTrimmed && password === confirmPassword;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (isRegisterMode) {
        await api.register(email, password);
        const loginResponse = await api.login(email, password);
        localStorage.setItem('token', loginResponse.token);
        onLoginSuccess(loginResponse.token, loginResponse.user);
      } else {
        const response = await api.login(email, password);
        localStorage.setItem('token', response.token);
        onLoginSuccess(response.token, response.user);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleMode = () => {
    setIsRegisterMode(!isRegisterMode);
    setConfirmPassword('');
    setError('');
  };

  const googleLogin = useGoogleLogin({
    flow: 'implicit',
    onSuccess: async (tokenResponse) => {
      setIsGoogleLoading(true);
      setError('');

      try {
        // Obtener información del usuario desde Google
        const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: {
            Authorization: `Bearer ${tokenResponse.access_token}`,
          },
        });

        if (!userInfoResponse.ok) {
          throw new Error('Error al obtener información del usuario de Google');
        }

        const userInfo = await userInfoResponse.json();

        // Enviar al backend para autenticar/registrar
        const response = await api.googleLogin(
          userInfo.email,
          userInfo.sub,
          userInfo.name,
          userInfo.picture
        );

        localStorage.setItem('token', response.token);
        onLoginSuccess(response.token, response.user);
      } catch (err: any) {
        setError(err.message || 'Error al iniciar sesión con Google');
      } finally {
        setIsGoogleLoading(false);
      }
    },
    onError: (error) => {
      console.error('Google Login Error:', error);
      setError('Error al iniciar sesión con Google. Verifica la configuración de OAuth en Google Cloud Console.');
    },
  });

  const handleGoogleLogin = () => {
    googleLogin();
  };

  return (
    <div className="min-vh-100 d-flex align-items-center justify-content-center position-relative" style={{ backgroundColor: '#131313', overflow: 'hidden' }}>
      {/* Efecto de dots en el fondo */}
      <div
        className="position-absolute w-100 h-100"
        style={{
          top: 0,
          left: 0,
          backgroundImage: `radial-gradient(circle, rgba(136, 136, 136, 0.15) 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
          zIndex: 1,
        }}
      />

      <div className="container position-relative" style={{ zIndex: 2 }}>
        <div className="row justify-content-center">
          <div className="col-12 col-md-6 col-lg-5">
            <div className="text-center mb-4">
              <img
                src="/src/assets/img/logo_completo.png"
                alt="CHATSEC"
                className="img-fluid mb-3"
                style={{ maxWidth: '300px' }}
              />
            </div>

            <div className="card shadow-lg border-0" style={{ backgroundColor: '#1C1E21', color: '#fff' }}>
              <div className="card-body p-4">
                <h2 className="text-center mb-2" style={{ color: '#7416F0' }}>
                  ¡Bienvenido!
                </h2>
                <p className="text-center mb-4" style={{ color: '#838383ff'}}>
                  Ingresa tus credenciales para empezar a usar el chat
                </p>

                {error && (
                  <div className="alert alert-danger alert-dismissible fade show" role="alert">
                    {error}
                    <button
                      type="button"
                      className="btn-close btn-close-white"
                      onClick={() => setError('')}
                    ></button>
                  </div>
                )}

                <form onSubmit={handleSubmit}>
                  <div className="form-floating mb-3">
                    <input
                      type="email"
                      className="form-control"
                      id="email"
                      placeholder="correo@ejemplo.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      style={{
                        backgroundColor: '#22272B',
                        color: '#fff',
                        border: '1px solid #444',
                      }}
                    />
                    <label htmlFor="email" style={{ color: '#aaa' }}>
                      Correo Electrónico
                    </label>
                  </div>

                  <div className="form-floating mb-3 position-relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      className="form-control"
                      id="password"
                      placeholder="Contraseña"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      style={{
                        backgroundColor: '#22272B',
                        color: '#fff',
                        border: '1px solid #444',
                      }}
                    />
                    <label htmlFor="password" style={{ color: '#aaa' }}>
                      Contraseña
                    </label>
                    <button
                      type="button"
                      className="btn btn-link position-absolute end-0 top-50 translate-middle-y"
                      onClick={() => setShowPassword(!showPassword)}
                      style={{ color: '#7416F0', textDecoration: 'none', zIndex: 10 }}
                    >
                      <i className={`bi bi-eye${showPassword ? '-slash' : ''}`}></i>
                    </button>
                  </div>

                  {isRegisterMode && (
                    <div className="form-floating mb-3 position-relative">
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        className="form-control"
                        id="confirmPassword"
                        placeholder="Confirma tu contraseña"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        style={{
                          backgroundColor: '#22272B',
                          color: '#fff',
                          border: `1px solid ${
                            confirmPassword && password !== confirmPassword ? '#dc3545' : '#444'
                          }`,
                        }}
                      />
                      <label htmlFor="confirmPassword" style={{ color: '#aaa' }}>
                        Confirma tu contraseña
                      </label>
                      <button
                        type="button"
                        className="btn btn-link position-absolute end-0 top-50 translate-middle-y"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        style={{ color: '#7416F0', textDecoration: 'none', zIndex: 10 }}
                      >
                        <i className={`bi bi-eye${showConfirmPassword ? '-slash' : ''}`}></i>
                      </button>
                      {confirmPassword && password !== confirmPassword && (
                        <div className="text-danger mt-1" style={{ fontSize: '14px' }}>
                          Las contraseñas no coinciden
                        </div>
                      )}
                    </div>
                  )}

                  <button
                    type="submit"
                    className="btn w-100 mb-3"
                    disabled={isLoading || !isFormValid()}
                    style={{
                      backgroundColor: isLoading || !isFormValid() ? '#555' : '#7416F0',
                      color: '#fff',
                      border: 'none',
                      padding: '12px',
                      fontSize: '16px',
                      fontWeight: 'bold',
                      cursor: isLoading || !isFormValid() ? 'not-allowed' : 'pointer',
                      opacity: isLoading || !isFormValid() ? 0.6 : 1,
                    }}
                  >
                    {isLoading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2"></span>
                        {isRegisterMode ? 'Registrando...' : 'Iniciando sesión...'}
                      </>
                    ) : (
                      <>{isRegisterMode ? 'Registrarse' : 'Iniciar Sesión'}</>
                    )}
                  </button>
                </form>

                <div className="text-center mb-3">
                  <button
                    type="button"
                    className="btn btn-link text-decoration-none"
                    onClick={handleToggleMode}
                    style={{ color: '#7C148C' }}
                  >
                    {isRegisterMode
                      ? '¿Ya tienes cuenta? Inicia sesión'
                      : '¿No tienes cuenta? Regístrate'}
                  </button>
                </div>

                <div className="position-relative mb-3">
                  <hr style={{ borderColor: '#444' }} />
                  <span
                    className="position-absolute top-50 start-50 translate-middle px-2"
                    style={{ backgroundColor: '#1C1E21', color: '#aaa' }}
                  >
                    o
                  </span>
                </div>

                <button
                  type="button"
                  className="btn btn-outline-light w-100"
                  onClick={handleGoogleLogin}
                  onMouseEnter={() => setIsGoogleHovered(true)}
                  onMouseLeave={() => setIsGoogleHovered(false)}
                  disabled={isGoogleLoading}
                  style={{
                    borderColor: isGoogleHovered && !isGoogleLoading ? '#7C148C' : '#444',
                    backgroundColor: isGoogleHovered && !isGoogleLoading ? '#7C148C' : 'transparent',
                    color: '#fff',
                    transition: 'all 0.3s ease',
                    cursor: isGoogleLoading ? 'not-allowed' : 'pointer',
                    opacity: isGoogleLoading ? 0.6 : 1,
                  }}
                >
                  {isGoogleLoading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Conectando con Google...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-google me-2"></i>
                      Ingresa con Google
                    </>
                  )}
                </button>
              </div>
            </div>

            <p className="text-center mt-3" style={{ color: '#666', fontSize: '12px' }}>
              CHATSEC v5.0 - Copyright © 2025 Seguridad Informática UTEZ
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
