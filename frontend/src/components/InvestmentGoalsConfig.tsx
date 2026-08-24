import React, { useState } from 'react';

interface InvestmentGoals {
  targetReturn: number;
  investmentHorizon: 'short' | 'medium' | 'long';
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  availableCapital: number;
  maxPositionSize: number;
  maxLossPerTrade: number;
  preferredSectors: string[];
  excludedSectors: string[];
}

interface InvestmentGoalsConfigProps {
  initialGoals?: Partial<InvestmentGoals>;
  onSave: (goals: InvestmentGoals) => void;
  className?: string;
}

const SECTORS = [
  '科技', '金融', '医疗健康', '消费品', '工业',
  '能源', '材料', '通信', '公用事业', '房地产',
];

const InvestmentGoalsConfig: React.FC<InvestmentGoalsConfigProps> = ({
  initialGoals,
  onSave,
  className = '',
}) => {
  const [goals, setGoals] = useState<InvestmentGoals>({
    targetReturn: initialGoals?.targetReturn || 15,
    investmentHorizon: initialGoals?.investmentHorizon || 'medium',
    riskTolerance: initialGoals?.riskTolerance || 'moderate',
    availableCapital: initialGoals?.availableCapital || 100000,
    maxPositionSize: initialGoals?.maxPositionSize || 20,
    maxLossPerTrade: initialGoals?.maxLossPerTrade || 3,
    preferredSectors: initialGoals?.preferredSectors || [],
    excludedSectors: initialGoals?.excludedSectors || [],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (field: keyof InvestmentGoals, value: any) => {
    setGoals((prev) => ({ ...prev, [field]: value }));
    // Clear error when field changes
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleSectorToggle = (sector: string, type: 'preferred' | 'excluded') => {
    const field = type === 'preferred' ? 'preferredSectors' : 'excludedSectors';
    const current = goals[field];

    if (current.includes(sector)) {
      handleChange(field, current.filter((s) => s !== sector));
    } else {
      handleChange(field, [...current, sector]);
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (goals.targetReturn <= 0 || goals.targetReturn > 100) {
      newErrors.targetReturn = '目标收益率应在1-100%之间';
    }

    if (goals.availableCapital <= 0) {
      newErrors.availableCapital = '可用资金必须大于0';
    }

    if (goals.maxPositionSize <= 0 || goals.maxPositionSize > 50) {
      newErrors.maxPositionSize = '最大仓位应在1-50%之间';
    }

    if (goals.maxLossPerTrade <= 0 || goals.maxLossPerTrade > 10) {
      newErrors.maxLossPerTrade = '最大单笔亏损应在1-10%之间';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validate()) {
      onSave(goals);
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h2 className="text-lg font-semibold text-gray-900">投资目标配置</h2>
        <p className="text-sm text-gray-500">设置您的投资偏好和风险参数</p>
      </div>

      {/* Target Return */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          目标年化收益率 (%)
        </label>
        <input
          type="number"
          value={goals.targetReturn}
          onChange={(e) => handleChange('targetReturn', parseFloat(e.target.value))}
          className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
            errors.targetReturn ? 'border-red-300' : 'border-gray-300'
          }`}
        />
        {errors.targetReturn && (
          <p className="mt-1 text-sm text-red-600">{errors.targetReturn}</p>
        )}
      </div>

      {/* Investment Horizon */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          投资期限
        </label>
        <div className="flex space-x-4">
          {[
            { value: 'short', label: '短期 (1-4周)' },
            { value: 'medium', label: '中期 (1-3月)' },
            { value: 'long', label: '长期 (3-12月)' },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => handleChange('investmentHorizon', option.value)}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                goals.investmentHorizon === option.value
                  ? 'bg-blue-100 text-blue-700 border border-blue-300'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Risk Tolerance */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          风险承受能力
        </label>
        <div className="flex space-x-4">
          {[
            { value: 'conservative', label: '保守型', color: 'green' },
            { value: 'moderate', label: '稳健型', color: 'yellow' },
            { value: 'aggressive', label: '激进型', color: 'red' },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => handleChange('riskTolerance', option.value)}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                goals.riskTolerance === option.value
                  ? `bg-${option.color}-100 text-${option.color}-700 border border-${option.color}-300`
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Available Capital */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          可用资金 (元)
        </label>
        <input
          type="number"
          value={goals.availableCapital}
          onChange={(e) => handleChange('availableCapital', parseFloat(e.target.value))}
          className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
            errors.availableCapital ? 'border-red-300' : 'border-gray-300'
          }`}
        />
        {errors.availableCapital && (
          <p className="mt-1 text-sm text-red-600">{errors.availableCapital}</p>
        )}
      </div>

      {/* Risk Parameters */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            最大单仓位 (%)
          </label>
          <input
            type="number"
            value={goals.maxPositionSize}
            onChange={(e) => handleChange('maxPositionSize', parseFloat(e.target.value))}
            className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
              errors.maxPositionSize ? 'border-red-300' : 'border-gray-300'
            }`}
          />
          {errors.maxPositionSize && (
            <p className="mt-1 text-sm text-red-600">{errors.maxPositionSize}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            最大单笔亏损 (%)
          </label>
          <input
            type="number"
            value={goals.maxLossPerTrade}
            onChange={(e) => handleChange('maxLossPerTrade', parseFloat(e.target.value))}
            className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
              errors.maxLossPerTrade ? 'border-red-300' : 'border-gray-300'
            }`}
          />
          {errors.maxLossPerTrade && (
            <p className="mt-1 text-sm text-red-600">{errors.maxLossPerTrade}</p>
          )}
        </div>
      </div>

      {/* Sector Preferences */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          行业偏好
        </label>
        <div className="flex flex-wrap gap-2">
          {SECTORS.map((sector) => {
            const isPreferred = goals.preferredSectors.includes(sector);
            const isExcluded = goals.excludedSectors.includes(sector);

            return (
              <div key={sector} className="flex space-x-1">
                <button
                  onClick={() => handleSectorToggle(sector, 'preferred')}
                  className={`px-3 py-1 rounded-full text-sm ${
                    isPreferred
                      ? 'bg-green-100 text-green-700 border border-green-300'
                      : 'bg-gray-100 text-gray-600 border border-gray-200'
                  }`}
                >
                  {sector}
                </button>
                <button
                  onClick={() => handleSectorToggle(sector, 'excluded')}
                  className={`px-2 py-1 rounded-full text-sm ${
                    isExcluded
                      ? 'bg-red-100 text-red-700 border border-red-300'
                      : 'bg-gray-50 text-gray-600 border border-gray-200'
                  }`}
                >
                  ×
                </button>
              </div>
            );
          })}
        </div>
        <p className="mt-1 text-xs text-gray-500">
          绿色表示偏好，红色表示排除
        </p>
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

export default InvestmentGoalsConfig;
