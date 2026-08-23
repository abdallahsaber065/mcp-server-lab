/**
 * Role-Adaptive Dashboard Dispatcher (platform/src/pages/dashboard/DashboardPage.tsx)
 */

import React from 'react';
import { useAuthStore } from '../../stores/useAuthStore';
import { TenantDashboard } from './TenantDashboard';
import { ManagerDashboard } from './ManagerDashboard';
import { ExecutiveDashboard } from './ExecutiveDashboard';
import { LoginPage } from '../auth/LoginPage';

export const DashboardPage: React.FC = () => {
  const { isAuthenticated, role } = useAuthStore();

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  switch (role) {
    case 'executive_admin':
      return <ExecutiveDashboard />;
    case 'property_manager':
      return <ManagerDashboard />;
    case 'tenant':
      return <TenantDashboard />;
    default:
      return <ManagerDashboard />;
  }
};
