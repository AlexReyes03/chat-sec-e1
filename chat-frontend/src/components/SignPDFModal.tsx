import { useState, useRef, useEffect } from 'react';
import { api, type User } from '../services/api';

interface SignPDFModalProps {
  user: User;
  onClose: () => void;
}

const SignPDFModal = ({ user, onClose }: SignPDFModalProps) => {
  const [step, setStep] = useState<'generate' | 'sign' | 'success'>('generate');
  const [pdfBase64, setPdfBase64] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [driveLink, setDriveLink] = useState('');
  const [isDrawing, setIsDrawing] = useState(false);

  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }, [step]);

  const handleGeneratePDF = async () => {
    setError('');
    setIsLoading(true);

    try {
      const response = await api.generatePDF('DOCUMENTO DE PRUEBA');
      setPdfBase64(response.pdf_base64);
      setStep('sign');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDrawing(true);
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
  };

  const handleClearSignature = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  };

  const handleSign = async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    setError('');
    setIsLoading(true);

    try {
      const signatureImageBase64 = canvas.toDataURL('image/png').split(',')[1];

      const response = await api.signPDF(
        pdfBase64,
        signatureImageBase64,
        user.apodo || user.nombre_google || user.email,
        user.email
      );

      if (response.drive_link) {
        setDriveLink(response.drive_link);
      }

      setStep('success');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="modal d-block"
      tabIndex={-1}
      style={{ backgroundColor: 'rgba(0,0,0,0.8)' }}
    >
      <div className="modal-dialog modal-dialog-centered modal-lg">
        <div
          className="modal-content"
          style={{ backgroundColor: '#1C1E21', color: '#fff', border: 'none' }}
        >
          <div className="modal-header border-0">
            <h5 className="modal-title" style={{ color: '#ffffffff' }}>
              Firmar Documento PDF
            </h5>
            <button
              type="button"
              className="btn-close btn-close-white"
              onClick={onClose}
            ></button>
          </div>
          <div className="modal-body">
            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}

            {step === 'generate' && (
              <div className="text-center py-5">
                <i
                  className="bi bi-file-earmark-pdf mb-3"
                  style={{ fontSize: '64px', color: '#7416F0' }}
                ></i>
                <h5 className="mb-3">Generar PDF de Prueba</h5>
                <p className="text-center mb-4" style={{ color: '#838383ff'}}>
                  Se generará un documento PDF de prueba que podrás firmar digitalmente
                </p>
                <button
                  className="btn btn-lg"
                  onClick={handleGeneratePDF}
                  disabled={isLoading}
                  style={{
                    backgroundColor: '#7416F0',
                    color: '#fff',
                    border: 'none',
                  }}
                >
                  {isLoading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Generando...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-file-earmark-plus me-2"></i>
                      Generar PDF
                    </>
                  )}
                </button>
              </div>
            )}

            {step === 'sign' && (
              <div>
                <h6 className="mb-3">Dibuja tu firma con el mouse:</h6>
                <div className="mb-3">
                  <canvas
                    ref={canvasRef}
                    width={600}
                    height={200}
                    className="border w-100"
                    style={{
                      backgroundColor: '#fff',
                      cursor: 'crosshair',
                      borderRadius: '8px',
                    }}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                  />
                </div>
                <div className="d-flex gap-2">
                  <button
                    className="btn btn-outline-light"
                    onClick={handleClearSignature}
                  >
                    <i className="bi bi-arrow-counterclockwise me-2"></i>
                    Limpiar
                  </button>
                  <button
                    className="btn flex-grow-1"
                    onClick={handleSign}
                    disabled={isLoading}
                    style={{
                      backgroundColor: '#7416F0',
                      color: '#fff',
                      border: 'none',
                    }}
                  >
                    {isLoading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2"></span>
                        Firmando y subiendo a Drive...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-check-circle me-2"></i>
                        Firmar y Guardar en Drive
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {step === 'success' && (
              <div className="text-center py-5">
                <i
                  className="bi bi-check-circle mb-3"
                  style={{ fontSize: '64px', color: '#28a745' }}
                ></i>
                <h5 className="mb-3">Documento Firmado Exitosamente</h5>
                <p className="text-muted mb-4">
                  El documento ha sido firmado y guardado en Google Drive
                </p>
                {driveLink && (
                  <a
                    href={driveLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn"
                    style={{
                      backgroundColor: '#7416F0',
                      color: '#fff',
                      border: 'none',
                    }}
                  >
                    <i className="bi bi-box-arrow-up-right me-2"></i>
                    Abrir en Drive
                  </a>
                )}
                <div className="mt-3">
                  <button
                    className="btn btn-outline-light"
                    onClick={onClose}
                  >
                    Cerrar
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignPDFModal;
