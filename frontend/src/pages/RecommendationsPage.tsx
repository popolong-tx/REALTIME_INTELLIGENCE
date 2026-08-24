import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import StockInput from '../components/StockInput';
import { PageHeader, Breadcrumb, LoadingSpinner } from '../components/MainLayout';
import { InlineDisclaimer } from '../components/Disclaimer';
import { StockValidationResponse } from '../services/stockService';

interface Recommendation {
  symbol: string;
  name?: string;
  recommendation: 'buy' | 'sell' | 'hold';
  confidence: number;
  riskLevel: 'low' | 'medium' | 'high' | 'very_high';
  targetPrice?: number;
  stopLoss?: number;
  reasoning: string;
  generatedAt: string;
}

const RecommendationsPage: React.FC = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedStock, setSelectedStock] = useState<StockValidationResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    try {
      const response = await fetch('/api/v1/recommendations');
      const data = await response.json();
      setRecommendations(data.recommendations || []);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateRecommendation = async () => {
    if (!selectedStock) return;

    setIsGenerating(true);
    try {
      const response = await fetch('/api/v1/recommendations/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: selectedStock.symbol }),
      });

      const data = await response.json();
      if (data.recommendation) {
        setRecommendations((prev) => [data.recommendation, ...prev]);
        setSelectedStock(null);
      }
    } catch (error) {
      console.error('Error generating recommendation:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const RecommendationBadge: React.FC<{ type: string }> = ({ type }) => {
    const config = {
      buy: { label: '买入', color: 'green', icon: '📈' },
      sell: { label: '卖出', color: 'red', icon: '📉' },
      hold: { label: '持有', color: 'yellow', icon: '⏸️' },
    };

    const { label, color, icon } = config[type as keyof typeof config] || config.hold;

    return (
      <span
        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-${color}-100 text-${color}-800`}
      >
        <span className="mr-1">{icon}</span>
        {label}
      </span>
    );
  };

  const RiskBadge: React.FC<{ level: string }> = ({ level }) => {
    const config = {
      low: { label: '低风险', color: 'green' },
      medium: { label: '中风险', color: 'yellow' },
      high: { label: '高风险', color: 'orange' },
      very_high: { label: '极高风险', color: 'red' },
    };

    const { label, color } = config[level as keyof typeof config] || config.medium;

    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-${color}-100 text-${color}-800`}
      >
        {label}
      </span>
    );
  };

  return (
    <div>
      <Breadcrumb items={[{ label: '交易建议' }]} />

      <PageHeader
        title="交易建议"
        description="获取量化分析生成的交易建议"
      />

      {/* Generate New Recommendation */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          生成新建议
        </h2>
        <div className="flex space-x-4">
          <div className="flex-1">
            <StockInput
              onStockSelect={setSelectedStock}
              placeholder="输入股票代码生成交易建议..."
            />
          </div>
          <button
            onClick={handleGenerateRecommendation}
            disabled={!selectedStock || isGenerating}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? '生成中...' : '生成建议'}
          </button>
        </div>
        <InlineDisclaimer type="recommendation" />
      </div>

      {/* Recommendations List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            建议列表 ({recommendations.length})
          </h2>
        </div>

        {isLoading ? (
          <LoadingSpinner message="加载建议列表..." />
        ) : recommendations.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>暂无交易建议，输入股票代码开始生成</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {recommendations.map((rec, index) => (
              <div key={index} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <Link
                        to={`/stocks/${rec.symbol}`}
                        className="text-lg font-bold text-gray-900 hover:text-blue-600"
                      >
                        {rec.symbol}
                      </Link>
                      {rec.name && (
                        <span className="text-sm text-gray-500">{rec.name}</span>
                      )}
                      <RecommendationBadge type={rec.recommendation} />
                      <RiskBadge level={rec.riskLevel} />
                    </div>

                    <p className="text-sm text-gray-600 mb-3">{rec.reasoning}</p>

                    <div className="flex space-x-6 text-sm text-gray-500">
                      <div>
                        <span className="font-medium">置信度:</span>{' '}
                        {(rec.confidence * 100).toFixed(0)}%
                      </div>
                      {rec.targetPrice && (
                        <div>
                          <span className="font-medium">目标价:</span> $
                          {rec.targetPrice.toFixed(2)}
                        </div>
                      )}
                      {rec.stopLoss && (
                        <div>
                          <span className="font-medium">止损价:</span> $
                          {rec.stopLoss.toFixed(2)}
                        </div>
                      )}
                      <div>
                        <span className="font-medium">生成时间:</span>{' '}
                        {new Date(rec.generatedAt).toLocaleString()}
                      </div>
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    <Link
                      to={`/stocks/${rec.symbol}`}
                      className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      查看详情
                    </Link>
                    <button className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50">
                      保存
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RecommendationsPage;
