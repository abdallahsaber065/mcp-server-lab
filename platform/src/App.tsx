/**
 * Main Application Orchestrator (platform/src/App.tsx)
 */

import React, { useEffect } from 'react';
import { useAuthStore } from './stores/useAuthStore';
import { useAppStore, AppPage } from './stores/useAppStore';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { ToastContainer } from './components/layout/Toast';

import { LandingPage } from './pages/public/LandingPage';
import { PropertyCatalogPage } from './pages/public/PropertyCatalogPage';
import { ShowcasePage } from './pages/public/ShowcasePage';
import { SystemStatusPage } from './pages/public/SystemStatusPage';
import { LoginPage } from './pages/auth/LoginPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { ChatStudioPage } from './pages/chat/ChatStudioPage';
import { StateGraphPage } from './pages/stateGraph/StateGraphPage';
import { AdminCenterPage } from './pages/admin/AdminCenterPage';

export const App: React.FC = () => {
  const { checkAuth, isAuthenticated } = useAuthStore();
  const { currentPage, setCurrentPage } = useAppStore();

  useEffect(() => {
    checkAuth();

    const handleHashChange = () => {
      const hash = window.location.hash.replace('#/', '');
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
      if (validPages.includes(hash as AppPage)) {
        setCurrentPage(hash as AppPage);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    if (window.location.hash) {
      handleHashChange();
    }

    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <LandingPage />;
      case 'properties':
        return <PropertyCatalogPage />;
      case 'showcase':
        return <ShowcasePage />;
      case 'status':
        return <SystemStatusPage />;
      case 'login':
        return <LoginPage />;
      case 'dashboard':
        return <DashboardPage />;
      case 'chat':
        return isAuthenticated ? <ChatStudioPage /> : <LoginPage />;
      case 'stateGraph':
        return isAuthenticated ? <StateGraphPage /> : <LoginPage />;
      case 'admin':
        return isAuthenticated ? <AdminCenterPage /> : <LoginPage />;
      default:
        return <LandingPage />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col selection:bg-indigo-500 selection:text-white">
      <Navbar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-4 sm:p-8 max-w-7xl mx-auto w-full">
          {renderPage()}
        </main>
      </div>
      <ToastContainer />
    </div>
  );
};

export default App;
