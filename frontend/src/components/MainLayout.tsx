import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import RoleBasedNavigation, { RoleBasedSidebar } from './RoleBasedNavigation';
import NotificationCenter from './NotificationCenter';
import Disclaimer from './Disclaimer';

type UserRole = 'viewer' | 'analyst' | 'researcher' | 'trader' | 'admin';

interface MainLayoutProps {
  userRole?: UserRole;
  userName?: string;
}

const MainLayout: React.FC<MainLayoutProps> = ({
  userRole = 'viewer',
  userName = '用户',
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Skip to main content link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded"
      >
        跳转到主要内容
      </a>

      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and mobile menu */}
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
                aria-label="打开菜单"
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path d="M4 6h16M4 12h16M4 18h16"></path>
                </svg>
              </button>

              <Link to="/" className="flex items-center ml-4 lg:ml-0">
                <span className="text-2xl mr-2">📈</span>
                <span className="text-xl font-bold text-gray-900">
                  量化交易系统
                </span>
              </Link>
            </div>

            {/* Navigation */}
            <div className="hidden lg:flex lg:flex-1 lg:justify-center">
              <RoleBasedNavigation userRole={userRole} />
            </div>

            {/* Right side */}
            <div className="flex items-center space-x-4">
              <NotificationCenter />

              {/* User menu */}
              <div className="relative">
                <button className="flex items-center space-x-2 p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500">
                  <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium">
                    {userName.charAt(0)}
                  </div>
                  <span className="hidden md:block text-sm font-medium">
                    {userName}
                  </span>
                  <span className="hidden md:block text-xs text-gray-500">
                    ({userRole})
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-gray-600 bg-opacity-75"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 w-64">
            <RoleBasedSidebar userRole={userRole} />
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex">
        {/* Desktop sidebar */}
        <div className="hidden lg:block lg:w-64 lg:flex-shrink-0">
          <div className="sticky top-16 h-[calc(100vh-4rem)]">
            <RoleBasedSidebar userRole={userRole} />
          </div>
        </div>

        {/* Main content area */}
        <main id="main-content" className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            {/* Disclaimer banner */}
            <Disclaimer type="general" compact />

            {/* Page content */}
            <div className="mt-6">
              <Outlet />
            </div>
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4 px-6">
        <div className="max-w-7xl mx-auto">
          <p className="text-xs text-gray-500 text-center">
            免责声明：本软件提供的所有信息仅供参考，不构成任何投资建议。
            投资有风险，入市需谨慎。在做出任何投资决策之前，请咨询专业的投资顾问。
            本软件不对任何投资损失承担责任。
          </p>
          <p className="text-xs text-gray-400 text-center mt-2">
            © {new Date().getFullYear()} 量化交易建议系统. 保留所有权利.
          </p>
        </div>
      </footer>
    </div>
  );
};

// Page header component
export const PageHeader: React.FC<{
  title: string;
  description?: string;
  actions?: React.ReactNode;
}> = ({ title, description, actions }) => (
  <div className="mb-6">
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-gray-500">{description}</p>
        )}
      </div>
      {actions && <div className="flex space-x-3">{actions}</div>}
    </div>
  </div>
);

// Breadcrumb component
export const Breadcrumb: React.FC<{
  items: Array<{ label: string; path?: string }>;
}> = ({ items }) => (
  <nav className="mb-4" aria-label="面包屑导航">
    <ol className="flex items-center space-x-2 text-sm text-gray-500">
      <li>
        <Link to="/" className="hover:text-gray-700">
          首页
        </Link>
      </li>
      {items.map((item, index) => (
        <li key={index} className="flex items-center">
          <span className="mx-2">/</span>
          {item.path ? (
            <Link to={item.path} className="hover:text-gray-700">
              {item.label}
            </Link>
          ) : (
            <span className="text-gray-900">{item.label}</span>
          )}
        </li>
      ))}
    </ol>
  </nav>
);

// Loading spinner
export const LoadingSpinner: React.FC<{ message?: string }> = ({
  message = '加载中...',
}) => (
  <div className="flex flex-col items-center justify-center py-12">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
    <p className="mt-4 text-sm text-gray-500">{message}</p>
  </div>
);

// Error message
export const ErrorMessage: React.FC<{
  title?: string;
  message: string;
  onRetry?: () => void;
}> = ({ title = '出错了', message, onRetry }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
    <h3 className="text-lg font-medium text-red-800">{title}</h3>
    <p className="mt-2 text-sm text-red-600">{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
      >
        重试
      </button>
    )}
  </div>
);

export default MainLayout;
