import React from 'react';
import { Link, useLocation } from 'react-router-dom';

type UserRole = 'viewer' | 'analyst' | 'researcher' | 'trader' | 'admin';

interface NavigationItem {
  path: string;
  label: string;
  icon: string;
  roles: UserRole[];
}

const NAVIGATION_ITEMS: NavigationItem[] = [
  // Common items
  { path: '/dashboard', label: '仪表板', icon: '📊', roles: ['viewer', 'analyst', 'researcher', 'trader', 'admin'] },
  { path: '/stocks', label: '股票查询', icon: '🔍', roles: ['viewer', 'analyst', 'researcher', 'trader', 'admin'] },
  { path: '/recommendations', label: '交易建议', icon: '💡', roles: ['viewer', 'analyst', 'researcher', 'trader', 'admin'] },
  { path: '/portfolio', label: '投资组合', icon: '📈', roles: ['viewer', 'analyst', 'researcher', 'trader', 'admin'] },

  // Analyst items
  { path: '/analysis', label: '技术分析', icon: '📉', roles: ['analyst', 'researcher', 'trader', 'admin'] },
  { path: '/news', label: '市场新闻', icon: '📰', roles: ['analyst', 'researcher', 'trader', 'admin'] },

  // Researcher items
  { path: '/models', label: '模型管理', icon: '🤖', roles: ['researcher', 'admin'] },
  { path: '/backtesting', label: '回测系统', icon: '🔬', roles: ['researcher', 'admin'] },
  { path: '/experiments', label: '实验管理', icon: '🧪', roles: ['researcher', 'admin'] },

  // Trader items
  { path: '/trading-plan', label: '交易计划', icon: '📋', roles: ['trader', 'admin'] },
  { path: '/alerts', label: '提醒管理', icon: '🔔', roles: ['trader', 'admin'] },

  // Admin items
  { path: '/governance', label: '模型治理', icon: '⚖️', roles: ['admin'] },
  { path: '/users', label: '用户管理', icon: '👥', roles: ['admin'] },
  { path: '/audit', label: '审计日志', icon: '📝', roles: ['admin'] },
  { path: '/system', label: '系统设置', icon: '⚙️', roles: ['admin'] },
];

interface RoleBasedNavigationProps {
  userRole: UserRole;
  className?: string;
}

const RoleBasedNavigation: React.FC<RoleBasedNavigationProps> = ({
  userRole,
  className = '',
}) => {
  const location = useLocation();

  // Filter navigation items based on user role
  const allowedItems = NAVIGATION_ITEMS.filter((item) =>
    item.roles.includes(userRole)
  );

  // Group items by category
  const categories = [
    {
      label: '概览',
      items: allowedItems.filter((item) =>
        ['/dashboard', '/stocks', '/recommendations', '/portfolio'].includes(item.path)
      ),
    },
    {
      label: '分析',
      items: allowedItems.filter((item) =>
        ['/analysis', '/news'].includes(item.path)
      ),
    },
    {
      label: '研究',
      items: allowedItems.filter((item) =>
        ['/models', '/backtesting', '/experiments'].includes(item.path)
      ),
    },
    {
      label: '交易',
      items: allowedItems.filter((item) =>
        ['/trading-plan', '/alerts'].includes(item.path)
      ),
    },
    {
      label: '管理',
      items: allowedItems.filter((item) =>
        ['/governance', '/users', '/audit', '/system'].includes(item.path)
      ),
    },
  ].filter((category) => category.items.length > 0);

  return (
    <nav className={`bg-white shadow-sm ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-8 overflow-x-auto">
          {categories.map((category) => (
            <div key={category.label} className="flex-shrink-0">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider py-2">
                {category.label}
              </div>
              <div className="flex space-x-4">
                {category.items.map((item) => {
                  const isActive = location.pathname === item.path;

                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                      }`}
                    >
                      <span className="mr-2">{item.icon}</span>
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </nav>
  );
};

// Sidebar navigation variant
export const RoleBasedSidebar: React.FC<RoleBasedNavigationProps> = ({
  userRole,
  className = '',
}) => {
  const location = useLocation();

  const allowedItems = NAVIGATION_ITEMS.filter((item) =>
    item.roles.includes(userRole)
  );

  return (
    <aside className={`bg-gray-900 text-white w-64 min-h-screen ${className}`}>
      <div className="p-4">
        <h1 className="text-xl font-bold">量化交易系统</h1>
        <p className="text-sm text-gray-400 mt-1">
          {userRole === 'admin' ? '管理员' :
           userRole === 'researcher' ? '研究员' :
           userRole === 'trader' ? '交易员' :
           userRole === 'analyst' ? '分析师' : '查看者'}
        </p>
      </div>

      <nav className="mt-4">
        {allowedItems.map((item) => {
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center px-4 py-3 text-sm transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <span className="mr-3">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
};

// User role badge
export const UserRoleBadge: React.FC<{ role: UserRole }> = ({ role }) => {
  const roleConfig = {
    viewer: { label: '查看者', color: 'gray' },
    analyst: { label: '分析师', color: 'blue' },
    researcher: { label: '研究员', color: 'purple' },
    trader: { label: '交易员', color: 'green' },
    admin: { label: '管理员', color: 'red' },
  };

  const config = roleConfig[role];

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${config.color}-100 text-${config.color}-800`}>
      {config.label}
    </span>
  );
};

export default RoleBasedNavigation;
