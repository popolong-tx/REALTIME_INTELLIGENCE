import React, { useState } from 'react';

interface RiskProfile {
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  maxDrawdown: number;
  volatilityTolerance: 'low' | 'medium' | 'high';
  lossCapacity: number;
  investmentExperience: 'beginner' | 'intermediate' | 'advanced';
  incomeStability: 'stable' | 'variable' | 'unstable';
  investmentGoals: string[];
}

interface RiskToleranceConfigProps {
  initialProfile?: Partial<RiskProfile>;
  onSave: (profile: RiskProfile) => void;
  className?: string;
}

const INVESTMENT_GOALS = [
  { id: 'capital_preservation', label: '资本保值', risk: 'low' },
  { id: 'income_generation', label: '收益生成', risk: 'low' },
  { id: 'balanced_growth', label: '均衡增长', risk: 'medium' },
  { id: 'capital_appreciation', label: '资本增值', risk: 'medium' },
  { id: 'aggressive_growth', label: '激进增长', risk: 'high' },
];

const RiskToleranceConfig: React.FC<RiskToleranceConfigProps> = ({
  initialProfile,
  onSave,
  className = '',
}) => {
  const [profile, setProfile] = useState<RiskProfile>({
    riskTolerance: initialProfile?.riskTolerance || 'moderate',
    maxDrawdown: initialProfile?.maxDrawdown || 20,
    volatilityTolerance: initialProfile?.volatilityTolerance || 'medium',
    lossCapacity: initialProfile?.lossCapacity || 10,
    investmentExperience: initialProfile?.investmentExperience || 'intermediate',
    incomeStability: initialProfile?.incomeStability || 'stable',
    investmentGoals: initialProfile?.investmentGoals || [],
  });

  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { title: '风险承受能力', description: '评估您的风险偏好' },
    { title: '投资经验', description: '了解您的投资背景' },
    { title: '财务状况', description: '评估您的财务稳定性' },
    { title: '投资目标', description: '明确您的投资目的' },
  ];

  const handleChange = (field: keyof RiskProfile, value: any) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
  };

  const handleGoalToggle = (goalId: string) => {
    const current = profile.investmentGoals;
    if (current.includes(goalId)) {
      handleChange('investmentGoals', current.filter((g) => g !== goalId));
    } else {
      handleChange('investmentGoals', [...current, goalId]);
    }
  };

  const calculateRiskScore = (): number => {
    let score = 0;

    // Risk tolerance
    if (profile.riskTolerance === 'conservative') score += 1;
    else if (profile.riskTolerance === 'moderate') score += 2;
    else score += 3;

    // Max drawdown tolerance
    if (profile.maxDrawdown <= 10) score += 1;
    else if (profile.maxDrawdown <= 20) score += 2;
    else score += 3;

    // Volatility tolerance
    if (profile.volatilityTolerance === 'low') score += 1;
    else if (profile.volatilityTolerance === 'medium') score += 2;
    else score += 3;

    // Loss capacity
    if (profile.lossCapacity <= 5) score += 1;
    else if (profile.lossCapacity <= 15) score += 2;
    else score += 3;

    // Investment experience
    if (profile.investmentExperience === 'beginner') score += 1;
    else if (profile.investmentExperience === 'intermediate') score += 2;
    else score += 3;

    // Income stability
    if (profile.incomeStability === 'stable') score += 1;
    else if (profile.incomeStability === 'variable') score += 2;
    else score += 3;

    return score;
  };

  const getRiskLevel = (): string => {
    const score = calculateRiskScore();
    if (score <= 10) return '保守型';
    if (score <= 15) return '稳健型';
    return '激进型';
  };

  const handleSubmit = () => {
    onSave(profile);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                您能承受的最大回撤是多少？
              </label>
              <div className="flex space-x-4">
                {[
                  { value: 10, label: '10%以内', desc: '保守' },
                  { value: 20, label: '10-20%', desc: '稳健' },
                  { value: 30, label: '20-30%', desc: '激进' },
                  { value: 50, label: '30%以上', desc: '高风险' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleChange('maxDrawdown', option.value)}
                    className={`flex-1 p-4 rounded-lg border text-center ${
                      profile.maxDrawdown === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium">{option.label}</div>
                    <div className="text-sm text-gray-500">{option.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                您对波动性的容忍度如何？
              </label>
              <div className="flex space-x-4">
                {[
                  { value: 'low', label: '低波动', desc: '偏好稳定' },
                  { value: 'medium', label: '中等波动', desc: '可接受' },
                  { value: 'high', label: '高波动', desc: '追求高收益' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleChange('volatilityTolerance', option.value)}
                    className={`flex-1 p-4 rounded-lg border text-center ${
                      profile.volatilityTolerance === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium">{option.label}</div>
                    <div className="text-sm text-gray-500">{option.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                您的投资经验如何？
              </label>
              <div className="flex space-x-4">
                {[
                  { value: 'beginner', label: '新手', desc: '刚开始投资' },
                  { value: 'intermediate', label: '有经验', desc: '3-5年经验' },
                  { value: 'advanced', label: '资深', desc: '5年以上经验' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleChange('investmentExperience', option.value)}
                    className={`flex-1 p-4 rounded-lg border text-center ${
                      profile.investmentExperience === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium">{option.label}</div>
                    <div className="text-sm text-gray-500">{option.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                您的收入稳定性如何？
              </label>
              <div className="flex space-x-4">
                {[
                  { value: 'stable', label: '稳定', desc: '固定收入' },
                  { value: 'variable', label: '波动', desc: '收入有变化' },
                  { value: 'unstable', label: '不稳定', desc: '收入不稳定' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleChange('incomeStability', option.value)}
                    className={`flex-1 p-4 rounded-lg border text-center ${
                      profile.incomeStability === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium">{option.label}</div>
                    <div className="text-sm text-gray-500">{option.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                您能承受的最大单笔亏损 (%)
              </label>
              <input
                type="number"
                value={profile.lossCapacity}
                onChange={(e) => handleChange('lossCapacity', parseFloat(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                您的投资目标是什么？（可多选）
              </label>
              <div className="grid grid-cols-2 gap-3">
                {INVESTMENT_GOALS.map((goal) => (
                  <button
                    key={goal.id}
                    onClick={() => handleGoalToggle(goal.id)}
                    className={`p-3 rounded-lg border text-left ${
                      profile.investmentGoals.includes(goal.id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium">{goal.label}</div>
                    <div className="text-xs text-gray-500">
                      风险等级: {goal.risk === 'low' ? '低' : goal.risk === 'medium' ? '中' : '高'}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Risk Assessment Summary */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-2">风险评估结果</h3>
              <div className="text-2xl font-bold text-blue-600">{getRiskLevel()}</div>
              <div className="text-sm text-gray-500 mt-1">
                综合得分: {calculateRiskScore()} / 18
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h2 className="text-lg font-semibold text-gray-900">风险承受能力评估</h2>
        <p className="text-sm text-gray-500">帮助我们了解您的风险偏好</p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={index} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                index <= currentStep
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-600'
              }`}
            >
              {index + 1}
            </div>
            <div className="ml-2 hidden sm:block">
              <div className="text-sm font-medium">{step.title}</div>
            </div>
            {index < steps.length - 1 && (
              <div className="flex-1 border-t border-gray-300 mx-4" />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      {renderStep()}

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <button
          onClick={() => setCurrentStep((prev) => Math.max(0, prev - 1))}
          disabled={currentStep === 0}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          上一步
        </button>

        {currentStep < steps.length - 1 ? (
          <button
            onClick={() => setCurrentStep((prev) => Math.min(steps.length - 1, prev + 1))}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            下一步
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            保存配置
          </button>
        )}
      </div>
    </div>
  );
};

export default RiskToleranceConfig;
