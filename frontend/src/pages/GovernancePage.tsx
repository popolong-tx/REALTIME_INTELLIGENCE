import React, { useState, useEffect } from 'react';
import { PageHeader, Breadcrumb, LoadingSpinner } from '../components/MainLayout';

interface PendingApproval {
  modelId: string;
  name: string;
  modelType: string;
  version: string;
  status: string;
  createdBy: string;
  createdAt: string;
  metrics: {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1Score?: number;
  };
}

interface GovernanceStats {
  totalModels: number;
  approved: number;
  rejected: number;
  pendingApproval: number;
  deployed: number;
}

const GovernancePage: React.FC = () => {
  const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>([]);
  const [stats, setStats] = useState<GovernanceStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'pending' | 'history' | 'stats'>('pending');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [approvalsResponse, statsResponse] = await Promise.all([
        fetch('/api/v1/governance/pending'),
        fetch('/api/v1/governance/stats'),
      ]);

      const approvalsData = await approvalsResponse.json();
      const statsData = await statsResponse.json();

      setPendingApprovals(approvalsData.models || []);
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching governance data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (modelId: string) => {
    try {
      await fetch(`/api/v1/governance/approve/${modelId}`, { method: 'POST' });
      await fetchData();
    } catch (error) {
      console.error('Error approving model:', error);
    }
  };

  const handleReject = async (modelId: string) => {
    const reason = prompt('请输入拒绝原因:');
    if (!reason) return;

    try {
      await fetch(`/api/v1/governance/reject/${modelId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      });
      await fetchData();
    } catch (error) {
      console.error('Error rejecting model:', error);
    }
  };

  return (
    <div>
      <Breadcrumb items={[{ label: '模型治理' }]} />

      <PageHeader
        title="模型治理"
        description="审批和管理模型部署"
      />

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <StatsCard title="总模型数" value={stats.totalModels} icon="📊" />
          <StatsCard title="待审批" value={stats.pendingApproval} icon="⏳" color="yellow" />
          <StatsCard title="已批准" value={stats.approved} icon="✅" color="green" />
          <StatsCard title="已拒绝" value={stats.rejected} icon="❌" color="red" />
          <StatsCard title="已部署" value={stats.deployed} icon="🚀" color="purple" />
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'pending', label: '待审批', count: pendingApprovals.length },
            { id: 'history', label: '审批历史' },
            { id: 'stats', label: '统计信息' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {isLoading ? (
        <LoadingSpinner message="加载治理数据..." />
      ) : (
        <>
          {activeTab === 'pending' && (
            <div className="bg-white rounded-lg shadow">
              {pendingApprovals.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <p>暂无待审批模型</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {pendingApprovals.map((model) => (
                    <div key={model.modelId} className="p-6">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">
                            {model.name}
                          </h3>
                          <div className="mt-1 flex space-x-4 text-sm text-gray-500">
                            <span>类型: {model.modelType}</span>
                            <span>版本: {model.version}</span>
                            <span>创建者: {model.createdBy}</span>
                            <span>
                              创建时间: {new Date(model.createdAt).toLocaleString()}
                            </span>
                          </div>

                          {/* Metrics */}
                          <div className="mt-3 flex space-x-4">
                            {model.metrics.accuracy !== undefined && (
                              <MetricBadge
                                label="准确率"
                                value={`${(model.metrics.accuracy * 100).toFixed(1)}%`}
                              />
                            )}
                            {model.metrics.precision !== undefined && (
                              <MetricBadge
                                label="精确率"
                                value={`${(model.metrics.precision * 100).toFixed(1)}%`}
                              />
                            )}
                            {model.metrics.recall !== undefined && (
                              <MetricBadge
                                label="召回率"
                                value={`${(model.metrics.recall * 100).toFixed(1)}%`}
                              />
                            )}
                            {model.metrics.f1Score !== undefined && (
                              <MetricBadge
                                label="F1分数"
                                value={`${(model.metrics.f1Score * 100).toFixed(1)}%`}
                              />
                            )}
                          </div>
                        </div>

                        <div className="flex space-x-3">
                          <button
                            onClick={() => handleApprove(model.modelId)}
                            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                          >
                            批准
                          </button>
                          <button
                            onClick={() => handleReject(model.modelId)}
                            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                          >
                            拒绝
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'history' && (
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-500">审批历史记录将在此显示</p>
            </div>
          )}

          {activeTab === 'stats' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                治理统计
              </h3>
              {stats && (
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">模型状态分布</h4>
                    <dl className="space-y-2">
                      <div className="flex justify-between">
                        <dt className="text-gray-500">总模型数</dt>
                        <dd className="font-medium">{stats.totalModels}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">已批准</dt>
                        <dd className="font-medium text-green-600">{stats.approved}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">已拒绝</dt>
                        <dd className="font-medium text-red-600">{stats.rejected}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">已部署</dt>
                        <dd className="font-medium text-purple-600">{stats.deployed}</dd>
                      </div>
                    </dl>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">审批率</h4>
                    <div className="text-3xl font-bold text-blue-600">
                      {stats.approved + stats.rejected > 0
                        ? `${((stats.approved / (stats.approved + stats.rejected)) * 100).toFixed(1)}%`
                        : 'N/A'}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

// Helper Components
const StatsCard: React.FC<{
  title: string;
  value: number;
  icon: string;
  color?: string;
}> = ({ title, value, icon, color = 'gray' }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <div className="flex items-center">
      <span className="text-2xl mr-3">{icon}</span>
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className={`text-2xl font-bold text-${color}-600`}>{value}</p>
      </div>
    </div>
  </div>
);

const MetricBadge: React.FC<{ label: string; value: string }> = ({
  label,
  value,
}) => (
  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
    {label}: {value}
  </span>
);

export default GovernancePage;
