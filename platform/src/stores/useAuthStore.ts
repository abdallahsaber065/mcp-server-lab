/**
 * Zustand Authentication & Role State Store (platform/src/stores/useAuthStore.ts)
 */

import { create } from 'zustand';
import { User, UserRole } from '../types';
import { apiClient } from '../services/api';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  role: UserRole;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  quickLoginAs: (role: 'executive_admin' | 'property_manager' | 'tenant') => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: JSON.parse(localStorage.getItem('cornerstone_user') || 'null'),
  accessToken: localStorage.getItem('cornerstone_access_token'),
  isAuthenticated: !!localStorage.getItem('cornerstone_access_token'),
  role: (JSON.parse(localStorage.getItem('cornerstone_user') || '{}').role as UserRole) || 'public',
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const data = await apiClient<{
        access_token: string;
        refresh_token: string;
        user: User;
      }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
        skipAuth: true,
      });

      localStorage.setItem('cornerstone_access_token', data.access_token);
      localStorage.setItem('cornerstone_refresh_token', data.refresh_token);
      localStorage.setItem('cornerstone_user', JSON.stringify(data.user));

      set({
        user: data.user,
        accessToken: data.access_token,
        isAuthenticated: true,
        role: data.user.role,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  quickLoginAs: async (role: 'executive_admin' | 'property_manager' | 'tenant') => {
    const creds = {
      executive_admin: { email: 'admin@cornerstonerealty.eg', password: 'AdminPass123!' },
      property_manager: { email: 'abdallahsaber065@gmail.com', password: 'ManagerPass123!' },
      tenant: { email: 'tarek.mahdy@cairomed.org', password: 'TenantPass123!' },
    }[role];

    await get().login(creds.email, creds.password);
  },

  logout: async () => {
    try {
      await apiClient('/api/auth/logout', { method: 'POST' }).catch(() => {});
    } finally {
      localStorage.removeItem('cornerstone_access_token');
      localStorage.removeItem('cornerstone_refresh_token');
      localStorage.removeItem('cornerstone_user');
      set({ user: null, accessToken: null, isAuthenticated: false, role: 'public' });
    }
  },

  checkAuth: async () => {
    const token = localStorage.getItem('cornerstone_access_token');
    if (!token) {
      set({ user: null, isAuthenticated: false, role: 'public' });
      return;
    }
    try {
      const res = await apiClient<{ user: User }>('/api/auth/me');
      set({ user: res.user, isAuthenticated: true, role: res.user.role });
    } catch {
      localStorage.removeItem('cornerstone_access_token');
      localStorage.removeItem('cornerstone_user');
      set({ user: null, isAuthenticated: false, role: 'public' });
    }
  },
}));
