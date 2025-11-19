import { useState } from 'react';
import { api } from '../services/api';

interface NicknameModalProps {
  show: boolean;
  onNicknameSet: (apodo: string) => void;
}

const NicknameModal = ({ show, onNicknameSet }: NicknameModalProps) => {
  const [apodo, setApodo] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await api.setNickname(apodo);
      onNicknameSet(response.apodo);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (!show) return null;

  return (
    <div
      className="modal d-block"
      tabIndex={-1}
      style={{ backgroundColor: 'rgba(0,0,0,0.8)' }}
    >
      <div className="modal-dialog modal-dialog-centered">
        <div
          className="modal-content"
          style={{ backgroundColor: '#1C1E21', color: '#fff', border: 'none' }}
        >
          <div className="modal-header border-0">
            <h5 className="modal-title" style={{ color: '#7416F0' }}>
              Establece tu apodo
            </h5>
          </div>
          <div className="modal-body">
            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}
            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label htmlFor="apodo" className="form-label">
                  ¿Cómo quieres que te llamen en el chat?
                </label>
                <input
                  type="text"
                  className="form-control"
                  id="apodo"
                  value={apodo}
                  onChange={(e) => setApodo(e.target.value)}
                  placeholder="Tu apodo"
                  required
                  minLength={2}
                  maxLength={50}
                  autoFocus
                  style={{
                    backgroundColor: '#22272B',
                    color: '#fff',
                    border: '1px solid #444',
                  }}
                />
                <small className="form-text" style={{ color: '#aaa' }}>
                  Entre 2 y 50 caracteres
                </small>
              </div>
              <button
                type="submit"
                className="btn w-100"
                disabled={isLoading || apodo.length < 2}
                style={{
                  backgroundColor: '#7416F0',
                  color: '#fff',
                  border: 'none',
                }}
              >
                {isLoading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Guardando...
                  </>
                ) : (
                  'Continuar'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NicknameModal;
