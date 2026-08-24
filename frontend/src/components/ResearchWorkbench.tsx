import React, { useState, useEffect } from 'react';
import StockInput from './StockInput';
import { StockValidationResponse } from '../services/stockService';

interface ResearchData {
  stockInfo: any;
  technicalAnalysis: any;
  news: any;
  sentiment: any;
  financials: any;
}

interface ResearchWorkbenchProps {
  className?: string;
}

const ResearchWorkbench: React.FC<ResearchWorkbenchProps> = ({
  className = '',
}) => {
  const [selectedStock, setSelectedStock] = useState<StockValidationResponse | null>(null);
  const [researchData, setResearchData] = useState<ResearchData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [notes, setNotes] = useState('');

  const tabs = [
    { id: 'overview', label: '概览', icon: '📊' },
    { id: 'technical', label: '技术分析', icon: '📈' },
    { id: 'fundamental', label: '基本面', icon: '📋' },
    { id: 'news', label: '新闻动态', icon: '📰' },
    { id: 'sentiment', label: '市场情绪', icon: '💭' },
    { id: 'notes', label: '研究笔记', icon: '📝' },
  ];

  const handleStockSelect = async (stock: StockValidationResponse) => {
    setSelectedStock(stock);
    setIsLoading(true);

    try {
      // Fetch research data
      const [stockInfo, technical, news, sentiment, financials] = await Promise.all([
        fetch(`/api/v1/stocks/${stock.symbol}/info`).then((r) => r.json()),
        fetch(`/api/v1/stocks/${stock.symbol}/technical`).then((r) => r.json()),
        fetch(`/api/v1/stocks/${stock.symbol}/news`).then((r) => r.json()),
        fetch(`/api/v1/stocks/${stock.symbol}/sentiment`).then((r) => r.json()),
        fetch(`/api/v1/stocks/${stock.symbol}/financials`).then((r) => r.json()),
      ]);

      setResearchData({
        stockInfo,
        technicalAnalysis: technical,
        news,
        sentiment,
        financials,
      });
    } catch (error) {
      console.error('Error fetching research data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const renderTabContent = () => {
    if (!researchData) {
      return (
        <div className="text-center py-12 text-gray-500">
          <p>请先选择一只股票开始研究</p>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return <OverviewTab data={researchData.stockInfo} />;
      case 'technical':
        return <TechnicalTab data={researchData.technicalAnalysis} />;
      case 'fundamental':
        return <FundamentalTab data={researchData.financials} />;
      case 'news':
        return <NewsTab data={researchData.news} />;
      case 'sentiment':
        return <SentimentTab data={researchData.sentiment} />;
      case 'notes':
        return <NotesTab notes={notes} onChange={setNotes} />;
      default:
        return null;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">证券研究工作台</h2>
        <div className="mt-3">
          <StockInput
            onStockSelect={handleStockSelect}
            placeholder="输入股票代码开始研究..."
          />
        </div>
      </div>

      {/* Stock Info Bar */}
      {selectedStock && (
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-gray-900">
                {selectedStock.symbol}
              </h3>
              {selectedStock.name && (
                <p className="text-sm text-gray-500">{selectedStock.name}</p>
              )}
            </div>
            {researchData?.stockInfo && (
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">
                  ${researchData.stockInfo.current_price?.toFixed(2)}
                </div>
                <div
                  className={`text-sm font-medium ${
                    researchData.stockInfo.price_change >= 0
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}
                >
                  {researchData.stockInfo.price_change >= 0 ? '+' : ''}
                  {researchData.stockInfo.price_change?.toFixed(2)} (
                  {researchData.stockInfo.price_change_percent?.toFixed(2)}%)
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center px-4 py-3 text-sm font-medium whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="p-4">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">加载研究数据中...</p>
          </div>
        ) : (
          renderTabContent()
        )}
      </div>
    </div>
  );
};

// Tab Components
const OverviewTab: React.FC<{ data: any }> = ({ data }) => (
  <div className="grid grid-cols-2 gap-4">
    <div className="space-y-3">
      <h4 className="font-medium text-gray-900">基本信息</h4>
      <dl className="space-y-2">
        <div className="flex justify-between">
          <dt className="text-sm text-gray-500">市场</dt>
          <dd className="text-sm font-medium">{data?.market || '-'}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-sm text-gray-500">交易所</dt>
          <dd className="text-sm font-medium">{data?.exchange || '-'}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-sm text-gray-500">行业</dt>
          <dd className="text-sm font-medium">{data?.industry || '-'}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-sm text-gray-500">市值</dt>
          <dd className="text-sm font-medium">
            {data?.market_cap
              ? `$${(data.market_cap / 1e9).toFixed(2)}B`
              : '-'}
          </dd>
        </div>
      </dl>
    </div>
    <div className="space-y-3">
      <h4 className="font-medium text-gray-900">估值指标</h4>
      <dl className="space-y-2">
        <div className="flex justify-between">
          <dt className="text-sm text-gray-500">市盈率</dt>
          <dd className="text-sm font-medium">{data?.pe_ratio?.toFixed(2) || '-'}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-sm text-gray-500">市净率</dt>
          <dd className="text-sm font-medium">{data?.price_to_book?.toFixed(2) || '-'}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-sm text-gray-500">股息率</dt>
          <dd className="text-sm font-medium">
            {data?.dividend_yield
              ? `${(data.dividend_yield * 100).toFixed(2)}%`
              : '-'}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-sm text-gray-500">Beta</dt>
          <dd className="text-sm font-medium">{data?.beta?.toFixed(2) || '-'}</dd>
        </div>
      </dl>
    </div>
  </div>
);

const TechnicalTab: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4">
    <h4 className="font-medium text-gray-900">技术指标</h4>
    {data?.indicators && (
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="text-sm text-gray-500">RSI (14)</div>
          <div className="text-lg font-bold">
            {data.indicators.oscillators?.rsi?.value?.toFixed(2) || '-'}
          </div>
          <div className="text-xs text-gray-400">
            {data.indicators.oscillators?.rsi?.signal || '-'}
          </div>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="text-sm text-gray-500">MACD</div>
          <div className="text-lg font-bold">
            {data.indicators.oscillators?.macd?.macd_line?.toFixed(4) || '-'}
          </div>
          <div className="text-xs text-gray-400">
            {data.indicators.oscillators?.macd?.signal || '-'}
          </div>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="text-sm text-gray-500">信号</div>
          <div className="text-lg font-bold">
            {data.signals?.overall_signal || '-'}
          </div>
        </div>
      </div>
    )}
  </div>
);

const FundamentalTab: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4">
    <h4 className="font-medium text-gray-900">财务数据</h4>
    {data?.key_metrics && (
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h5 className="text-sm font-medium text-gray-700 mb-2">估值</h5>
          <dl className="space-y-1">
            {Object.entries(data.key_metrics.valuation_metrics || {}).map(
              ([key, value]) => (
                <div key={key} className="flex justify-between">
                  <dt className="text-sm text-gray-500">{key}</dt>
                  <dd className="text-sm font-medium">
                    {typeof value === 'number' ? value.toFixed(2) : value || '-'}
                  </dd>
                </div>
              )
            )}
          </dl>
        </div>
        <div>
          <h5 className="text-sm font-medium text-gray-700 mb-2">盈利能力</h5>
          <dl className="space-y-1">
            {Object.entries(data.key_metrics.profitability_metrics || {}).map(
              ([key, value]) => (
                <div key={key} className="flex justify-between">
                  <dt className="text-sm text-gray-500">{key}</dt>
                  <dd className="text-sm font-medium">
                    {typeof value === 'number'
                      ? `${(value * 100).toFixed(2)}%`
                      : value || '-'}
                  </dd>
                </div>
              )
            )}
          </dl>
        </div>
      </div>
    )}
  </div>
);

const NewsTab: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4">
    <h4 className="font-medium text-gray-900">最新新闻</h4>
    {data?.news?.length > 0 ? (
      <div className="space-y-3">
        {data.news.slice(0, 5).map((item: any, index: number) => (
          <div key={index} className="border-b border-gray-100 pb-3">
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-blue-600 hover:text-blue-800"
            >
              {item.title}
            </a>
            <p className="text-xs text-gray-500 mt-1">
              {item.source} • {new Date(item.published_at).toLocaleDateString()}
            </p>
          </div>
        ))}
      </div>
    ) : (
      <p className="text-sm text-gray-500">暂无新闻</p>
    )}
  </div>
);

const SentimentTab: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4">
    <h4 className="font-medium text-gray-900">市场情绪</h4>
    {data && (
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-green-50 p-3 rounded-lg text-center">
          <div className="text-2xl font-bold text-green-600">
            {data.positive_count || 0}
          </div>
          <div className="text-sm text-green-600">正面</div>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg text-center">
          <div className="text-2xl font-bold text-gray-600">
            {data.neutral_count || 0}
          </div>
          <div className="text-sm text-gray-600">中性</div>
        </div>
        <div className="bg-red-50 p-3 rounded-lg text-center">
          <div className="text-2xl font-bold text-red-600">
            {data.negative_count || 0}
          </div>
          <div className="text-sm text-red-600">负面</div>
        </div>
      </div>
    )}
  </div>
);

const NotesTab: React.FC<{ notes: string; onChange: (notes: string) => void }> = ({
  notes,
  onChange,
}) => (
  <div className="space-y-4">
    <h4 className="font-medium text-gray-900">研究笔记</h4>
    <textarea
      value={notes}
      onChange={(e) => onChange(e.target.value)}
      placeholder="在此记录您的研究笔记..."
      rows={10}
      className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-blue-500 focus:border-blue-500"
    />
  </div>
);

export default ResearchWorkbench;
