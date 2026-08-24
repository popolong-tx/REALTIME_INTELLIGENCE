import React, { useState } from 'react';

interface PortfolioSettings {
  name: string;
  description: string;
  isDefault: boolean;
  targetAllocation: {
    stocks: number;
    bonds: number;
    cash: number;
    commodities: number;
    crypto: number;
  };
  rebalancingFrequency: 'monthly' | 'quarterly' | 'annually' | 'never';
  autoRebalance: boolean;
}

interface PortfolioConfigProps {
  initialSettings?: Partial<PortfolioSettings>;
  onSave: (settings: PortfolioSettings) => void;
  className?: string;
}

const PortfolioConfig: React.FC<PortfolioConfigProps> = ({
  initialSettings,
  onSave,
  className = '',
}) => {
  const [settings, setSettings] = useState<PortfolioSettings>({
    name: initialSettings?.name || '默认投资组合',
    description: initialSettings?.description || '',
    isDefault: initialSettings?.isDefault ?? true,
    targetAllocation: initialSettings?.targetAllocation || {
      stocks: 60,
      bonds: 20,
      cash: 10,
      commodities: 5,
      crypto: 5,
    },
    rebalancingFrequency: initialSettings?.rebalancingFrequency || 'quarterly',
    autoRebalance: initialSettings?.autoRebalance ?? false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (field: keyof PortfolioSettings, value: any) => {
    setSettings((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleAllocationChange = (asset: keyof PortfolioSettings['targetAllocation'], value: number) => {
    setSettings((prev) => ({
      ...prev,
      targetAllocation: {
        ...prev.targetAllocation,
        [asset]: value,
      },
    }));
  };

  const getTotalAllocation = (): number => {
    return Object.values(settings.targetAllocation).reduce((sum, val) => sum + val, 0);
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!settings.name.trim()) {
      newErrors.name = '组合名称不能为空';
    }

    const total = getTotalAllocation();
    if (Math.abs(total - 100) > 0.01) {
      newErrors.allocation = `资产配置总和必须为100%，当前为${total}%`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validate()) {
      onSave(settings);
    }
  };

  const assetClasses = [
    { key: 'stocks', label: '股票', color: 'blue', description: '权益类资产' },
    { key: 'bonds', label: '债券', color: 'green', description: '固定收益类' },
    { key: 'cash', label: '现金', color: 'gray', description: '现金及等价物' },
    { key: 'commodities', label: '商品', color: 'yellow', description: '大宗商品' },
    { key: 'crypto', label: '加密货币', color: 'purple', description: '数字资产' },
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h2 className="text-lg font-semibold text-gray-900">投资组合配置</h2>
        <p className="text-sm text-gray-500">设置您的投资组合参数和资产配置</p>
      </div>

      {/* Portfolio Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          组合名称
        </label>
        <input
          type="text"
          value={settings.name}
          onChange={(e) => handleChange('name', e.target.value)}
          className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
            errors.name ? 'border-red-300' : 'border-gray-300'
          }`}
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name}</p>
        )}
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          描述（可选）
        </label>
        <textarea
          value={settings.description}
          onChange={(e) => handleChange('description', e.target.value)}
          rows={2}
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>

      {/* Target Allocation */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          目标资产配置
        </label>
        <div className="space-y-4">
          {assetClasses.map((asset) => (
            <div key={asset.key} className="flex items-center space-x-4">
              <div className="w-24">
                <span className="text-sm font-medium text-gray-700">{asset.label}</span>
                <span className="text-xs text-gray-500 block">{asset.description}</span>
              </div>
              <div className="flex-1">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={settings.targetAllocation[asset.key as keyof PortfolioSettings['targetAllocation']]}
                  onChange={(e) => handleAllocationChange(
                    asset.key as keyof PortfolioSettings['targetAllocation'],
                    parseInt(e.target.value)
                  )}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
              </div>
              <div className="w-16 text-right">
                <span className="text-sm font-medium">
                  {settings.targetAllocation[asset.key as keyof PortfolioSettings['targetAllocation']]}%
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Total Allocation */}
        <div className={`mt-4 p-3 rounded-lg ${
          Math.abs(getTotalAllocation() - 100) < 0.01
            ? 'bg-green-50 border border-green-200'
            : 'bg-red-50 border border-red-200'
        }`}>
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">总计</span>
            <span className={`text-lg font-bold ${
              Math.abs(getTotalAllocation() - 100) < 0.01
                ? 'text-green-600'
                : 'text-red-600'
            }`}>
              {getTotalAllocation()}%
            </span>
          </div>
          {errors.allocation && (
            <p className="mt-1 text-sm text-red-600">{errors.allocation}</p>
          )}
        </div>
      </div>

      {/* Rebalancing Settings */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          再平衡频率
        </label>
        <div className="flex space-x-4">
          {[
            { value: 'monthly', label: '每月' },
            { value: 'quarterly', label: '每季度' },
            { value: 'annually', label: '每年' },
            { value: 'never', label: '手动' },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => handleChange('rebalancingFrequency', option.value)}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                settings.rebalancingFrequency === option.value
                  ? 'bg-blue-100 text-blue-700 border border-blue-300'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Auto Rebalance Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-medium text-gray-700">自动再平衡</span>
          <span className="text-xs text-gray-500 block">偏离目标时自动调整</span>
        </div>
        <button
          onClick={() => handleChange('autoRebalance', !settings.autoRebalance)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full ${
            settings.autoRebalance ? 'bg-blue-600' : 'bg-gray-200'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
              settings.autoRebalance ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      {/* Default Portfolio Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-medium text-gray-700">设为默认组合</span>
          <span className="text-xs text-gray-500 block">新推荐将使用此组合</span>
        </div>
        <button
          onClick={() => handleChange('isDefault', !settings.isDefault)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full ${
            settings.isDefault ? 'bg-blue-600' : 'bg-gray-200'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
              settings.isDefault ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

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

export default PortfolioConfig;
