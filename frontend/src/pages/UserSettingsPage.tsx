import React, { useState, useEffect } from 'react';
import InvestmentGoalsConfig from '../components/InvestmentGoalsConfig';
import RiskToleranceConfig from '../components/RiskToleranceConfig';
import PortfolioConfig from '../components/PortfolioConfig';
import NotificationPreferences from '../components/NotificationPreferences';
import { PageHeader, Breadcrumb, LoadingSpinner } from '../components/MainLayout';

const UserSettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('goals');
  const [isLoading, setIsLoading] = useState(true);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch('/api/v1/user/profile');
      const data = await response.json();
      setUserProfile(data);
    } catch (error) {
      console.error('Error fetching user profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveGoals = async (goals: any) => {
    setSaveStatus('saving');
    try {
      await fetch('/api/v1/user/goals', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(goals),
      });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      console.error('Error saving goals:', error);
      setSaveStatus('error');
    }
  };

  const handleSaveRiskProfile = async (profile: any) => {
    setSaveStatus('saving');
    try {
      await fetch('/api/v1/user/risk-profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      console.error('Error saving risk profile:', error);
      setSaveStatus('error');
    }
  };

  const handleSavePortfolio = async (settings: any) => {
    setSaveStatus('saving');
    try {
      await fetch('/api/v1/user/portfolio', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      console.error('Error saving portfolio:', error);
      setSaveStatus('error');
    }
  };

  const handleSaveNotifications = async (settings: any) => {
    setSaveStatus('saving');
    try {
      await fetch('/api/v1/user/notifications', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      console.error('Error saving notifications:', error);
      setSaveStatus('error');
    }
  };

  const handleExportConfig = async () => {
    try {
      const response = await fetch('/api/v1/user/export');
      const data = await response.json();

      // Create download
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `quant-advisor-config-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting config:', error);
    }
  };

  const handleImportConfig = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const config = JSON.parse(text);

      await fetch('/api/v1/user/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      await fetchUserProfile();
    } catch (error) {
      console.error('Error importing config:', error);
    }
  };

  const tabs = [
    { id: 'goals', label: '投资目标', icon: '🎯' },
    { id: 'risk', label: '风险偏好', icon: '⚖️' },
    { id: 'portfolio', label: '投资组合', icon: '📊' },
    { id: 'notifications', label: '通知设置', icon: '🔔' },
    { id: 'export', label: '导入导出', icon: '💾' },
  ];

  if (isLoading) {
    return <LoadingSpinner message="加载设置..." />;
  }

  return (
    <div>
      <Breadcrumb items={[{ label: '用户设置' }]} />

      <PageHeader
        title="用户设置"
        description="管理您的投资偏好和系统配置"
      />

      {/* Save Status */}
      {saveStatus === 'saved' && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-800">✓ 设置已保存</p>
        </div>
      )}
      {saveStatus === 'error' && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">保存失败，请重试</p>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {activeTab === 'goals' && (
          <InvestmentGoalsConfig
            initialGoals={userProfile?.goals}
            onSave={handleSaveGoals}
          />
        )}

        {activeTab === 'risk' && (
          <RiskToleranceConfig
            initialProfile={userProfile?.riskProfile}
            onSave={handleSaveRiskProfile}
          />
        )}

        {activeTab === 'portfolio' && (
          <PortfolioConfig
            initialSettings={userProfile?.portfolioSettings}
            onSave={handleSavePortfolio}
          />
        )}

        {activeTab === 'notifications' && (
          <NotificationPreferences
            initialSettings={userProfile?.notificationSettings}
            onSave={handleSaveNotifications}
          />
        )}

        {activeTab === 'export' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                导入导出配置
              </h3>
              <p className="text-sm text-gray-500 mb-6">
                导出您的配置以便备份，或导入之前保存的配置
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Export */}
              <div className="border border-gray-200 rounded-lg p-6">
                <h4 className="font-medium text-gray-900 mb-2">导出配置</h4>
                <p className="text-sm text-gray-500 mb-4">
                  将当前配置导出为JSON文件
                </p>
                <button
                  onClick={handleExportConfig}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  导出配置
                </button>
              </div>

              {/* Import */}
              <div className="border border-gray-200 rounded-lg p-6">
                <h4 className="font-medium text-gray-900 mb-2">导入配置</h4>
                <p className="text-sm text-gray-500 mb-4">
                  从JSON文件导入配置
                </p>
                <label className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 cursor-pointer inline-block text-center">
                  选择文件
                  <input
                    type="file"
                    accept=".json"
                    onChange={handleImportConfig}
                    className="hidden"
                  />
                </label>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserSettingsPage;
