import React, { useState } from 'react';
import StockInput from './StockInput';
import InvestmentGoalsConfig from './InvestmentGoalsConfig';
import RiskToleranceConfig from './RiskToleranceConfig';
import { StockValidationResponse } from '../services/stockService';

interface PlanGenerationWizardProps {
  onComplete: (plan: any) => void;
  onCancel: () => void;
  className?: string;
}

interface WizardData {
  stock: StockValidationResponse | null;
  investmentGoals: any;
  riskProfile: any;
  planType: 'single' | 'portfolio';
  timeHorizon: 'short' | 'medium' | 'long';
}

const PlanGenerationWizard: React.FC<PlanGenerationWizardProps> = ({
  onComplete,
  onCancel,
  className = '',
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [wizardData, setWizardData] = useState<WizardData>({
    stock: null,
    investmentGoals: null,
    riskProfile: null,
    planType: 'single',
    timeHorizon: 'medium',
  });
  const [isGenerating, setIsGenerating] = useState(false);

  const steps = [
    { title: '选择股票', description: '选择要分析的股票' },
    { title: '投资目标', description: '设置您的投资目标' },
    { title: '风险评估', description: '评估您的风险承受能力' },
    { title: '计划配置', description: '配置交易计划参数' },
    { title: '生成计划', description: '生成并预览交易计划' },
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleStockSelect = (stock: StockValidationResponse) => {
    setWizardData((prev) => ({ ...prev, stock }));
  };

  const handleGoalsSave = (goals: any) => {
    setWizardData((prev) => ({ ...prev, investmentGoals: goals }));
    handleNext();
  };

  const handleRiskSave = (profile: any) => {
    setWizardData((prev) => ({ ...prev, riskProfile: profile }));
    handleNext();
  };

  const handleGenerate = async () => {
    setIsGenerating(true);

    try {
      // Call API to generate plan
      const response = await fetch('/api/v1/recommendations/generate-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: wizardData.stock?.symbol,
          user_profile: {
            ...wizardData.investmentGoals,
            ...wizardData.riskProfile,
            investment_horizon: wizardData.timeHorizon,
          },
        }),
      });

      const plan = await response.json();
      onComplete(plan);
    } catch (error) {
      console.error('Error generating plan:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0:
        return wizardData.stock !== null;
      case 1:
        return wizardData.investmentGoals !== null;
      case 2:
        return wizardData.riskProfile !== null;
      case 3:
        return true;
      default:
        return false;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">选择股票</h3>
            <p className="text-sm text-gray-500">
              输入您想要生成交易计划的股票代码
            </p>
            <StockInput onStockSelect={handleStockSelect} />
            {wizardData.stock && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">
                  已选择: {wizardData.stock.symbol} - {wizardData.stock.name}
                </p>
              </div>
            )}
          </div>
        );

      case 1:
        return (
          <InvestmentGoalsConfig
            initialGoals={wizardData.investmentGoals}
            onSave={handleGoalsSave}
          />
        );

      case 2:
        return (
          <RiskToleranceConfig
            initialProfile={wizardData.riskProfile}
            onSave={handleRiskSave}
          />
        );

      case 3:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">计划配置</h3>

            {/* Plan Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                计划类型
              </label>
              <div className="flex space-x-4">
                {[
                  { value: 'single', label: '单股票计划', desc: '针对单只股票的交易计划' },
                  { value: 'portfolio', label: '组合计划', desc: '多只股票的投资组合计划' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() =>
                      setWizardData((prev) => ({ ...prev, planType: option.value as any }))
                    }
                    className={`flex-1 p-4 rounded-lg border text-left ${
                      wizardData.planType === option.value
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

            {/* Time Horizon */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                投资期限
              </label>
              <div className="flex space-x-4">
                {[
                  { value: 'short', label: '短期', desc: '1-4周' },
                  { value: 'medium', label: '中期', desc: '1-3个月' },
                  { value: 'long', label: '长期', desc: '3-12个月' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() =>
                      setWizardData((prev) => ({ ...prev, timeHorizon: option.value as any }))
                    }
                    className={`flex-1 p-4 rounded-lg border text-center ${
                      wizardData.timeHorizon === option.value
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

      case 4:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">确认并生成计划</h3>

            {/* Summary */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <h4 className="font-medium text-gray-700">计划摘要</h4>
              <dl className="space-y-2">
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">股票</dt>
                  <dd className="text-sm font-medium">
                    {wizardData.stock?.symbol} - {wizardData.stock?.name}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">计划类型</dt>
                  <dd className="text-sm font-medium">
                    {wizardData.planType === 'single' ? '单股票计划' : '组合计划'}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">投资期限</dt>
                  <dd className="text-sm font-medium">
                    {wizardData.timeHorizon === 'short'
                      ? '短期 (1-4周)'
                      : wizardData.timeHorizon === 'medium'
                      ? '中期 (1-3个月)'
                      : '长期 (3-12个月)'}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">目标收益</dt>
                  <dd className="text-sm font-medium">
                    {wizardData.investmentGoals?.targetReturn || '-'}%
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">风险承受</dt>
                  <dd className="text-sm font-medium">
                    {wizardData.riskProfile?.riskTolerance === 'conservative'
                      ? '保守型'
                      : wizardData.riskProfile?.riskTolerance === 'moderate'
                      ? '稳健型'
                      : '激进型'}
                  </dd>
                </div>
              </dl>
            </div>

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isGenerating ? (
                <span className="flex items-center justify-center">
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
                  生成中...
                </span>
              ) : (
                '生成交易计划'
              )}
            </button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-bold text-gray-900">生成交易计划</h2>
        <p className="text-sm text-gray-500 mt-1">
          按照步骤生成个性化的交易计划
        </p>
      </div>

      {/* Progress Steps */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={index} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  index < currentStep
                    ? 'bg-green-500 text-white'
                    : index === currentStep
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {index < currentStep ? '✓' : index + 1}
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
      </div>

      {/* Step Content */}
      <div className="p-6">{renderStepContent()}</div>

      {/* Footer */}
      <div className="p-6 bg-gray-50 border-t border-gray-200 rounded-b-lg">
        <div className="flex justify-between">
          <button
            onClick={currentStep === 0 ? onCancel : handleBack}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            {currentStep === 0 ? '取消' : '上一步'}
          </button>

          {currentStep < steps.length - 1 && (
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一步
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlanGenerationWizard;
