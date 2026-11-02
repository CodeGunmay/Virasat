import axios from 'axios';

export const api = axios.create({baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'});

api.interceptors.request.use(config => {
  const token = sessionStorage.getItem('virasat_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export interface AuthUser {id: number; email: string; role: string}
export interface AuthResponse {access_token: string; token_type: string; user: AuthUser}

export function setAuth(data: AuthResponse) {
  sessionStorage.setItem('virasat_token', data.access_token);
  sessionStorage.setItem('virasat_user', JSON.stringify(data.user));
  window.dispatchEvent(new Event('virasat-auth-changed'));
}

export function clearAuth() {
  sessionStorage.removeItem('virasat_token');
  sessionStorage.removeItem('virasat_user');
  window.dispatchEvent(new Event('virasat-auth-changed'));
}

export function getStoredUser(): AuthUser | null {
  try {
    const raw = sessionStorage.getItem('virasat_user');
    return raw ? JSON.parse(raw) as AuthUser : null;
  } catch {return null;}
}
