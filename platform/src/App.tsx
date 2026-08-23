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

    const handlePopState = () => {
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
      if (validPages.includes(path)) {
        setCurrentPage(path);
      } else if (!path) {
        setCurrentPage('home');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
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

  const isChatPage = currentPage === 'chat' && isAuthenticated;

  return (
    <div className="h-screen w-screen bg-slate-950 flex flex-col overflow-hidden selection:bg-indigo-500 selection:text-white">
      <Navbar />
      <div className="flex-1 flex overflow-hidden relative">
        <Sidebar />
        <main
          className={`flex-1 min-w-0 bg-slate-950/40 ${
            isChatPage
              ? 'h-full w-full flex flex-col overflow-hidden p-0'
              : 'overflow-y-auto p-4 sm:p-6 lg:p-8'
          }`}
        >
          {isChatPage ? (
            renderPage()
          ) : (
            <div className="max-w-7xl mx-auto w-full">{renderPage()}</div>
          )}
        </main>
      </div>
      <ToastContainer />
    </div>
  );
};

export default App;
