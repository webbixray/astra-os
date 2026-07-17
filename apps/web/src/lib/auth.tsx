'use client';

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { api } from './api';

interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
}

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

const AuthContext = createContext<AuthContextType | null>(null);

function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  try {
    const stored = localStorage.getItem('astra_user');
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function setStoredUser(user: User) {
  localStorage.setItem('astra_user', JSON.stringify(user));
}

function clearStoredUser() {
  localStorage.removeItem('astra_user');
  localStorage.removeItem('astra_orgs');
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(getStoredUser);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get<User>('/auth/me')
      .then((u) => {
        setUser(u);
        setStoredUser(u);
      })
      .catch(() => {
        clearStoredUser();
        setUser(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data = await api.post<AuthResponse>('/auth/signin', { email, password }, true);
    setStoredUser(data.user);
    setUser(data.user);
  }, []);

  const signup = useCallback(async (email: string, password: string, name: string) => {
    const data = await api.post<AuthResponse>('/auth/signup', { email, password, name }, true);
    setStoredUser(data.user);
    setUser(data.user);
  }, []);

  const logout = useCallback(() => {
    clearStoredUser();
    setUser(null);
    api.post('/auth/logout', {}).catch(() => {});
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
