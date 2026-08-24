import React, { useState, useEffect } from 'react';
import ModelSelector, { ModelConfig } from '../components/ModelSelector';
import { PageHeader, Breadcrumb, LoadingSpinner } from '../components/MainLayout';

interface Model {
  id: string;
  name: string;
  type: string;
  status: 'draft' | 'training' | 'trained' | 'validated' | 'approved' | 'deployed';
  version: string;
  accuracy?: number;
  createdAt: string;
}

const ModelTrainingPage: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelConfig | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'list' | 'train' | 'evaluate'>('list');

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await fetch('/api/v1/models');
      const data = await response.json();
      setModels(data.models || []);
    } catch (error) {
      console.error('Error fetching models:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleModelSelect = (config: ModelConfig) => {
    setSelectedModel(config);
  };

  const handleTrainModel = async () => {
    if (!selectedModel) return;

    setIsTraining(true);
    try {
      const response = await fetch('/api/v1/models/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: selectedModel.name,
          type: selectedModel.type,
          hyperparameters: selectedModel.hyperparameters,
        }),
      });

      if (response.ok) {
        await fetchModels();
        setActiveTab('list');
      }
    } catch (error) {
      console.error('Error training model:', error);
    } finally {
      setIsTraining(false);
    }
  };

  const handleApproveModel = async (modelId: string) => {
    try {
      await fetch(`/api/v1/models/${modelId}/approve`, { method: 'POST' });
      await fetchModels();
    } catch (error) {
      console.error('Error approving model:', error);
    }
  };

  const handleDeployModel = async (modelId: string) => {
    try {
      await fetch(`/api/v1/models/${modelId}/deploy`, { method: 'POST' });
      await fetchModels();
    } catch (error) {
      console.error('Error deploying model:', error);
    }
  };

  const StatusBadge: React.FC<{ status: Model['status'] }> = ({ status }) => {
    const config = {
      draft: { label: '草稿', color: 'gray' },
      training: { label: '训练中', color: 'yellow' },
      trained: { label: '已训练', color: 'blue' },
      validated: { label: '已验证', color: 'indigo' },
      approved: { label: '已批准', color: 'green' },
      deployed: { label: '已部署', color: 'purple' },
    };

    const { label, color } = config[status];

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${color}-100 text-${color}-800`}
      >
        {status === 'training' && (
          <svg
            className="animate-spin -ml-1 mr-1.5 h-3 w-3"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
        )}
        {label}
      </span>
    );
  };

  return (
    <div>
      <Breadcrumb items={[{ label: '模型管理' }]} />

      <PageHeader
        title="模型管理"
        description="训练、评估和管理量化模型"
        actions={
          <button
            onClick={() => setActiveTab('train')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            训练新模型
          </button>
        }
      />

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'list', label: '模型列表' },
            { id: 'train', label: '训练模型' },
            { id: 'evaluate', label: '模型评估' },
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
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'list' && (
        <div className="bg-white rounded-lg shadow">
          {isLoading ? (
            <LoadingSpinner message="加载模型列表..." />
          ) : models.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p>暂无模型，点击"训练新模型"开始</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      模型名称
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      类型
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      版本
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      状态
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      准确率
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      创建时间
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {models.map((model) => (
                    <tr key={model.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {model.name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{model.type}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{model.version}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusBadge status={model.status} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {model.accuracy
                            ? `${(model.accuracy * 100).toFixed(1)}%`
                            : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          {new Date(model.createdAt).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end space-x-2">
                          {model.status === 'trained' && (
                            <button
                              onClick={() => handleApproveModel(model.id)}
                              className="text-green-600 hover:text-green-900"
                            >
                              批准
                            </button>
                          )}
                          {model.status === 'approved' && (
                            <button
                              onClick={() => handleDeployModel(model.id)}
                              className="text-purple-600 hover:text-purple-900"
                            >
                              部署
                            </button>
                          )}
                          <button className="text-blue-600 hover:text-blue-900">
                            详情
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'train' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            训练新模型
          </h2>
          <ModelSelector onModelSelect={handleModelSelect} />

          {selectedModel && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-700">
                    已选择模型配置
                  </h3>
                  <p className="text-sm text-gray-500">
                    {selectedModel.name} ({selectedModel.type})
                  </p>
                </div>
                <button
                  onClick={handleTrainModel}
                  disabled={isTraining}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {isTraining ? '训练中...' : '开始训练'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'evaluate' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            模型评估
          </h2>
          <p className="text-gray-500">选择一个模型进行评估和回测</p>
        </div>
      )}
    </div>
  );
};

export default ModelTrainingPage;
