/**
 * App Navigation & UI State Store (platform/src/stores/useAppStore.ts)
 */

import { create } from 'zustand';

export type AppPage =
  | 'home'
  | 'properties'
  | 'showcase'
  | 'status'
  | 'dashboard'
  | 'chat'
  | 'stateGraph'
  | 'admin'
  | 'login';

export interface ToastMessage {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  message: string;
}

interface AppState {
  currentPage: AppPage;
  isSidebarOpen: boolean;
  theme: 'dark' | 'light';
  toasts: ToastMessage[];
  setCurrentPage: (page: AppPage) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'dark' | 'light') => void;
  addToast: (message: string, type?: 'success' | 'info' | 'warning' | 'error') => void;
  removeToast: (id: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentPage: (() => {
    const path = window.location.pathname.replace(/^\//, '').split('/')[0] as AppPage;
    const validPages: AppPage[] = [
      'home',
      'properties',
      'showcase',
      'status',
      'dashboard',
      'chat',
      'stateGraph',
      'admin',
      'login',
    ];
    if (validPages.includes(path)) return path;
    const stored = localStorage.getItem('cornerstone_page') as AppPage;
    return validPages.includes(stored) ? stored : 'home';
  })(),
  isSidebarOpen: (() => {
    const saved = localStorage.getItem('cornerstone_sidebar_open');
    return saved !== null ? saved === 'true' : true;
  })(),
  theme: 'dark',
  toasts: [],

  setCurrentPage: (page) => {
    localStorage.setItem('cornerstone_page', page);
    const targetPath = page === 'home' ? '/' : `/${page}`;
    if (window.location.pathname !== targetPath) {
      window.history.pushState({ page }, '', targetPath);
    }
    set({ currentPage: page });
  },

  toggleSidebar: () =>
    set((state) => {
      const next = !state.isSidebarOpen;
      localStorage.setItem('cornerstone_sidebar_open', String(next));
      return { isSidebarOpen: next };
    }),

  setTheme: (theme) => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    set({ theme });
  },

  addToast: (message, type = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    set((state) => ({ toasts: [...state.toasts, { id, type, message }] }));
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    }, 3000);
  },

  removeToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));
