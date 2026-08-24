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
  onClick?: () => void;
}

interface AppState {
  currentPage: AppPage;
  isSidebarOpen: boolean;
  theme: 'dark' | 'light';
  toasts: ToastMessage[];
  chatInitialPrompt: string | null;
  setCurrentPage: (page: AppPage) => void;
  setChatInitialPrompt: (prompt: string | null) => void;
  navigateToChatWithPrompt: (prompt: string) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'dark' | 'light') => void;
  addToast: (message: string, type?: 'success' | 'info' | 'warning' | 'error', onClick?: () => void) => void;
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
  chatInitialPrompt: null,

  setChatInitialPrompt: (prompt) => set({ chatInitialPrompt: prompt }),

  navigateToChatWithPrompt: (prompt) => {
    localStorage.setItem('cornerstone_page', 'chat');
    const encoded = encodeURIComponent(prompt);
    window.history.pushState({ page: 'chat' }, '', `/chat?prompt=${encoded}`);
    set({ currentPage: 'chat', chatInitialPrompt: prompt });
  },

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

  addToast: (message, type = 'info', onClick?: () => void) => {
    const id = Math.random().toString(36).substring(2, 9);
    set((state) => ({ toasts: [...state.toasts, { id, type, message, onClick }] }));
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    }, 5000);
  },

  removeToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));
