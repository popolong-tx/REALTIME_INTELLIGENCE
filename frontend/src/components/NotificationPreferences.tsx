import React, { useState } from 'react';

interface NotificationSettings {
  enabled: boolean;
  channels: {
    email: boolean;
    sms: boolean;
    push: boolean;
    inApp: boolean;
  };
  frequency: 'immediate' | 'daily' | 'weekly';
  quietHours: {
    enabled: boolean;
    start: string;
    end: string;
  };
  alertTypes: {
    priceAlerts: boolean;
    recommendationUpdates: boolean;
    planMilestones: boolean;
    marketNews: boolean;
    portfolioSummary: boolean;
  };
}

interface NotificationPreferencesProps {
  initialSettings?: Partial<NotificationSettings>;
  onSave: (settings: NotificationSettings) => void;
  className?: string;
}

const NotificationPreferences: React.FC<NotificationPreferencesProps> = ({
  initialSettings,
  onSave,
  className = '',
}) => {
  const [settings, setSettings] = useState<NotificationSettings>({
    enabled: initialSettings?.enabled ?? true,
    channels: initialSettings?.channels || {
      email: true,
      sms: false,
      push: true,
      inApp: true,
    },
    frequency: initialSettings?.frequency || 'immediate',
    quietHours: initialSettings?.quietHours || {
      enabled: false,
      start: '22:00',
      end: '08:00',
    },
    alertTypes: initialSettings?.alertTypes || {
      priceAlerts: true,
      recommendationUpdates: true,
      planMilestones: true,
      marketNews: false,
      portfolioSummary: true,
    },
  });

  const handleChannelToggle = (channel: keyof NotificationSettings['channels']) => {
    setSettings((prev) => ({
      ...prev,
      channels: {
        ...prev.channels,
        [channel]: !prev.channels[channel],
      },
    }));
  };

  const handleAlertTypeToggle = (alertType: keyof NotificationSettings['alertTypes']) => {
    setSettings((prev) => ({
      ...prev,
      alertTypes: {
        ...prev.alertTypes,
        [alertType]: !prev.alertTypes[alertType],
      },
    }));
  };

  const handleQuietHoursChange = (field: keyof NotificationSettings['quietHours'], value: any) => {
    setSettings((prev) => ({
      ...prev,
      quietHours: {
        ...prev.quietHours,
        [field]: value,
      },
    }));
  };

  const handleSubmit = () => {
    onSave(settings);
  };

  const channels = [
    { key: 'email', label: '邮件', icon: '📧', description: '发送到注册邮箱' },
    { key: 'sms', label: '短信', icon: '📱', description: '发送到手机' },
    { key: 'push', label: '推送通知', icon: '🔔', description: '应用内推送' },
    { key: 'inApp', label: '站内消息', icon: '💬', description: '应用内消息中心' },
  ];

  const alertTypes = [
    { key: 'priceAlerts', label: '价格提醒', description: '股票价格达到设定阈值时提醒' },
    { key: 'recommendationUpdates', label: '推荐更新', description: '交易建议变化时提醒' },
    { key: 'planMilestones', label: '计划里程碑', description: '交易计划达到关键节点时提醒' },
    { key: 'marketNews', label: '市场新闻', description: '重要市场新闻和公告' },
    { key: 'portfolioSummary', label: '组合摘要', description: '定期投资组合表现摘要' },
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h2 className="text-lg font-semibold text-gray-900">通知偏好配置</h2>
        <p className="text-sm text-gray-500">设置您希望接收的通知类型和方式</p>
      </div>

      {/* Master Toggle */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div>
          <span className="font-medium text-gray-900">启用通知</span>
          <span className="text-sm text-gray-500 block">接收所有重要更新</span>
        </div>
        <button
          onClick={() => setSettings((prev) => ({ ...prev, enabled: !prev.enabled }))}
          className={`relative inline-flex h-6 w-11 items-center rounded-full ${
            settings.enabled ? 'bg-blue-600' : 'bg-gray-200'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
              settings.enabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      {settings.enabled && (
        <>
          {/* Notification Channels */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              通知渠道
            </label>
            <div className="grid grid-cols-2 gap-3">
              {channels.map((channel) => (
                <button
                  key={channel.key}
                  onClick={() => handleChannelToggle(channel.key as keyof NotificationSettings['channels'])}
                  className={`p-4 rounded-lg border text-left ${
                    settings.channels[channel.key as keyof NotificationSettings['channels']]
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">{channel.icon}</span>
                    <div>
                      <div className="font-medium">{channel.label}</div>
                      <div className="text-xs text-gray-500">{channel.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Notification Frequency */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              通知频率
            </label>
            <div className="flex space-x-4">
              {[
                { value: 'immediate', label: '即时', description: '立即发送' },
                { value: 'daily', label: '每日摘要', description: '每天汇总' },
                { value: 'weekly', label: '每周摘要', description: '每周汇总' },
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => setSettings((prev) => ({ ...prev, frequency: option.value as any }))}
                  className={`flex-1 p-3 rounded-lg border text-center ${
                    settings.frequency === option.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium">{option.label}</div>
                  <div className="text-xs text-gray-500">{option.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Alert Types */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              提醒类型
            </label>
            <div className="space-y-3">
              {alertTypes.map((alertType) => (
                <div
                  key={alertType.key}
                  className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg"
                >
                  <div>
                    <span className="font-medium text-gray-900">{alertType.label}</span>
                    <span className="text-sm text-gray-500 block">{alertType.description}</span>
                  </div>
                  <button
                    onClick={() => handleAlertTypeToggle(alertType.key as keyof NotificationSettings['alertTypes'])}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                      settings.alertTypes[alertType.key as keyof NotificationSettings['alertTypes']]
                        ? 'bg-blue-600'
                        : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        settings.alertTypes[alertType.key as keyof NotificationSettings['alertTypes']]
                          ? 'translate-x-6'
                          : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Quiet Hours */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium text-gray-700">
                免打扰时段
              </label>
              <button
                onClick={() => handleQuietHoursChange('enabled', !settings.quietHours.enabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                  settings.quietHours.enabled ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                    settings.quietHours.enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {settings.quietHours.enabled && (
              <div className="flex items-center space-x-4">
                <div>
                  <label className="text-xs text-gray-500">开始时间</label>
                  <input
                    type="time"
                    value={settings.quietHours.start}
                    onChange={(e) => handleQuietHoursChange('start', e.target.value)}
                    className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
                <span className="text-gray-500">至</span>
                <div>
                  <label className="text-xs text-gray-500">结束时间</label>
                  <input
                    type="time"
                    value={settings.quietHours.end}
                    onChange={(e) => handleQuietHoursChange('end', e.target.value)}
                    className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          保存配置
        </button>
      </div>
    </div>
  );
};

export default NotificationPreferences;
