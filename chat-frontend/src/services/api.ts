const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export interface User {
  id: number;
  email: string;
  google_id: string | null;
  nombre_google: string | null;
  apodo: string | null;
  fecha_registro: string;
  foto_perfil_url: string | null;
}

export interface LoginResponse {
  success: boolean;
  message: string;
  token: string;
  user: User;
}

export interface RegisterResponse {
  success: boolean;
  message: string;
  user: User;
}

export interface SetNicknameResponse {
  success: boolean;
  message: string;
  apodo: string;
}

export interface GeneratePDFResponse {
  success: boolean;
  message: string;
  pdf_base64: string;
}

export interface SignPDFResponse {
  success: boolean;
  message: string;
  filename: string;
  drive_link?: string;
}

class ApiService {
  private readonly TIMEOUT = 10000; // 10 segundos

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const token = localStorage.getItem('token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private async fetchWithTimeout(url: string, options: RequestInit): Promise<Response> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.TIMEOUT);

    try {
      console.log(`[API] ${options.method || 'GET'} ${url}`);
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      console.log(`[API] Response ${response.status} from ${url}`);
      return response;
    } catch (error: any) {
      if (error.name === 'AbortError') {
        throw new Error(`Tiempo de espera agotado. El servidor no responde en ${API_URL}`);
      }
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error(`No se puede conectar al servidor en ${API_URL}. Verifica que el backend esté ejecutándose.`);
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  async register(email: string, password: string): Promise<RegisterResponse> {
    try {
      const response = await this.fetchWithTimeout(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al registrar');
      }

      return response.json();
    } catch (error: any) {
      console.error('[API] Error en registro:', error);
      throw error;
    }
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    try {
      const response = await this.fetchWithTimeout(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al iniciar sesión');
      }

      return response.json();
    } catch (error: any) {
      console.error('[API] Error en login:', error);
      throw error;
    }
  }

  async googleLogin(email: string, googleId: string, nombreGoogle: string, fotoPerfil?: string): Promise<LoginResponse> {
    try {
      const response = await this.fetchWithTimeout(`${API_URL}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          google_id: googleId,
          nombre_google: nombreGoogle,
          foto_perfil_url: fotoPerfil,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al iniciar sesión con Google');
      }

      return response.json();
    } catch (error: any) {
      console.error('[API] Error en Google login:', error);
      throw error;
    }
  }

  async setNickname(apodo: string): Promise<SetNicknameResponse> {
    try {
      const response = await this.fetchWithTimeout(`${API_URL}/api/auth/set-nickname`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ apodo }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al establecer apodo');
      }

      return response.json();
    } catch (error: any) {
      console.error('[API] Error al establecer apodo:', error);
      throw error;
    }
  }

  async getMe(): Promise<{ success: boolean; user: User }> {
    try {
      const response = await this.fetchWithTimeout(`${API_URL}/api/auth/me`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al obtener datos del usuario');
      }

      return response.json();
    } catch (error: any) {
      console.error('[API] Error al obtener datos del usuario:', error);
      throw error;
    }
  }

  async generatePDF(titulo: string, contenido?: string): Promise<GeneratePDFResponse> {
    try {
      const response = await this.fetchWithTimeout(`${API_URL}/api/pdf/generate`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ titulo, contenido }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al generar PDF');
      }

      return response.json();
    } catch (error: any) {
      console.error('[API] Error al generar PDF:', error);
      throw error;
    }
  }

  async signPDF(pdfBase64: string, signatureImageBase64: string, signerName: string, signerEmail: string): Promise<SignPDFResponse> {
    try {
      const response = await this.fetchWithTimeout(`${API_URL}/api/pdf/sign`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          pdf_base64: pdfBase64,
          signature_image_base64: signatureImageBase64,
          signer_name: signerName,
          signer_email: signerEmail,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al firmar PDF');
      }

      return response.json();
    } catch (error: any) {
      console.error('[API] Error al firmar PDF:', error);
      throw error;
    }
  }

  getWebSocketURL(): string {
    return API_URL.replace('http', 'ws') + '/ws/chat';
  }
}

export const api = new ApiService();
