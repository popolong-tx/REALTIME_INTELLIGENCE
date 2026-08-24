import React, { useState, useEffect, useCallback } from 'react';

interface Notification {
  id: string;
  type: 'price_alert' | 'recommendation' | 'plan_milestone' | 'system' | 'news';
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
  data?: any;
  priority: 'low' | 'medium' | 'high';
}

interface NotificationCenterProps {
  className?: string;
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({
  className = '',
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  // Fetch notifications
  const fetchNotifications = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/notifications');
      const data = await response.json();
      setNotifications(data.notifications || []);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  }, []);

  // Poll for updates
  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  // Mark as read
  const markAsRead = async (notificationId: string) => {
    try {
      await fetch(`/api/v1/notifications/${notificationId}/read`, {
        method: 'POST',
      });
      setNotifications((prev) =>
        prev.map((n) =>
          n.id === notificationId ? { ...n, read: true } : n
        )
      );
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    try {
      await fetch('/api/v1/notifications/read-all', { method: 'POST' });
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  // Delete notification
  const deleteNotification = async (notificationId: string) => {
    try {
      await fetch(`/api/v1/notifications/${notificationId}`, {
        method: 'DELETE',
      });
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  // Filter notifications
  const filteredNotifications = notifications.filter((n) => {
    if (filter === 'unread') return !n.read;
    return true;
  });

  // Unread count
  const unreadCount = notifications.filter((n) => !n.read).length;

  // Notification icon
  const NotificationIcon: React.FC<{ type: Notification['type'] }> = ({ type }) => {
    const icons = {
      price_alert: '💰',
      recommendation: '💡',
      plan_milestone: '🎯',
      system: '⚙️',
      news: '📰',
    };

    return <span className="text-lg">{icons[type]}</span>;
  };

  // Priority indicator
  const PriorityIndicator: React.FC<{ priority: Notification['priority'] }> = ({
    priority,
  }) => {
    const colors = {
      low: 'bg-gray-400',
      medium: 'bg-yellow-400',
      high: 'bg-red-400',
    };

    return <div className={`w-2 h-2 rounded-full ${colors[priority]}`} />;
  };

  // Time ago
  const timeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return '刚刚';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟前`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时前`;
    return `${Math.floor(seconds / 86400)}天前`;
  };

  return (
    <div className={`relative ${className}`}>
      {/* Notification Bell */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none"
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
          <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
        </svg>
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">通知</h3>
              <div className="flex space-x-2">
                <button
                  onClick={() => setFilter(filter === 'all' ? 'unread' : 'all')}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  {filter === 'all' ? '只看未读' : '查看全部'}
                </button>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="text-sm text-gray-600 hover:text-gray-800"
                  >
                    全部已读
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Notification List */}
          <div className="max-h-96 overflow-y-auto">
            {filteredNotifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <p>{filter === 'unread' ? '没有未读通知' : '暂无通知'}</p>
              </div>
            ) : (
              filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-b border-gray-100 hover:bg-gray-50 ${
                    !notification.read ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <NotificationIcon type={notification.type} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <PriorityIndicator priority={notification.priority} />
                        <h4 className="text-sm font-medium text-gray-900 truncate">
                          {notification.title}
                        </h4>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        {notification.message}
                      </p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-400">
                          {timeAgo(notification.createdAt)}
                        </span>
                        <div className="flex space-x-2">
                          {!notification.read && (
                            <button
                              onClick={() => markAsRead(notification.id)}
                              className="text-xs text-blue-600 hover:text-blue-800"
                            >
                              标为已读
                            </button>
                          )}
                          <button
                            onClick={() => deleteNotification(notification.id)}
                            className="text-xs text-red-600 hover:text-red-800"
                          >
                            删除
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-gray-200 bg-gray-50 rounded-b-lg">
            <a
              href="/notifications"
              className="block text-center text-sm text-blue-600 hover:text-blue-800"
            >
              查看所有通知
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

// Price Alert Component
export const PriceAlert: React.FC<{
  symbol: string;
  currentPrice: number;
  targetPrice: number;
  direction: 'above' | 'below';
  onDismiss: () => void;
}> = ({ symbol, currentPrice, targetPrice, direction, onDismiss }) => {
  const isTriggered =
    direction === 'above'
      ? currentPrice >= targetPrice
      : currentPrice <= targetPrice;

  if (!isTriggered) return null;

  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <span className="text-2xl">💰</span>
        </div>
        <div className="ml-3">
          <p className="text-sm text-yellow-700">
            <span className="font-medium">{symbol}</span> 价格{' '}
            {direction === 'above' ? '突破' : '跌破'} ${targetPrice.toFixed(2)}
            (当前: ${currentPrice.toFixed(2)})
          </p>
        </div>
        <div className="ml-auto pl-3">
          <button
            onClick={onDismiss}
            className="text-yellow-700 hover:text-yellow-900"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotificationCenter;
