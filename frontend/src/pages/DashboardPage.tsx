import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader, Breadcrumb, LoadingSpinner } from '../components/MainLayout';

interface MarketSummary {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
}

interface DashboardStats {
  totalRecommendations: number;
  activePlans: number;
  portfolioValue: number;
  todayPnL: number;
}

const DashboardPage: React.FC = () => {
  const [marketSummary, setMarketSummary] = useState<MarketSummary[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch market summary
        const marketResponse = await fetch('/api/v1/market/summary');
        const marketData = await marketResponse.json();
        setMarketSummary(marketData.stocks || []);

        // Fetch dashboard stats
        const statsResponse = await fetch('/api/v1/dashboard/stats');
        const statsData = await statsResponse.json();
        setStats(statsData);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (isLoading) {
    return <LoadingSpinner message="加载仪表板..." />;
  }

  return (
    <div>
      <Breadcrumb items={[{ label: '仪表板' }]} />

      <PageHeader
        title="仪表板"
        description="市场概览和投资组合状态"
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          title="投资组合价值"
          value={stats?.portfolioValue ? `$${stats.portfolioValue.toLocaleString()}` : '-'}
          change={stats?.todayPnL}
          changeLabel="今日"
          icon="💰"
        />
        <StatsCard
          title="活跃推荐"
          value={stats?.totalRecommendations?.toString() || '0'}
          icon="💡"
          link="/recommendations"
        />
        <StatsCard
          title="交易计划"
          value={stats?.activePlans?.toString() || '0'}
          icon="📋"
          link="/trading-plan"
        />
        <StatsCard
          title="监控股票"
          value={marketSummary.length.toString()}
          icon="👁️"
          link="/watchlist"
        />
      </div>

      {/* Market Summary */}
      <div className="bg-white rounded-lg shadow mb-8">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">市场概览</h2>
            <Link
              to="/stocks"
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              查看全部 →
            </Link>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  股票
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  价格
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  涨跌
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  涨跌幅
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  成交量
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {marketSummary.map((stock) => (
                <tr key={stock.symbol} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {stock.symbol}
                      </div>
                      <div className="text-sm text-gray-500">{stock.name}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    ${stock.price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    <span
                      className={
                        stock.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }
                    >
                      {stock.change >= 0 ? '+' : ''}
                      {stock.change.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        stock.changePercent >= 0
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {stock.changePercent >= 0 ? '+' : ''}
                      {stock.changePercent.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                    {(stock.volume / 1e6).toFixed(2)}M
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link
                      to={`/stocks/${stock.symbol}`}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      详情
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <QuickActionCard
          title="股票研究"
          description="查看股票详情和技术分析"
          icon="🔍"
          link="/stocks"
        />
        <QuickActionCard
          title="生成推荐"
          description="获取交易建议和投资计划"
          icon="💡"
          link="/recommendations"
        />
        <QuickActionCard
          title="模型训练"
          description="训练和优化量化模型"
          icon="🤖"
          link="/models"
        />
      </div>
    </div>
  );
};

// Stats Card Component
const StatsCard: React.FC<{
  title: string;
  value: string;
  change?: number;
  changeLabel?: string;
  icon: string;
  link?: string;
}> = ({ title, value, change, changeLabel, icon, link }) => {
  const content = (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <span className="text-3xl">{icon}</span>
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {change !== undefined && (
            <p
              className={`text-sm ${
                change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {change >= 0 ? '+' : ''}
              {change.toFixed(2)}
              {changeLabel && ` ${changeLabel}`}
            </p>
          )}
        </div>
      </div>
    </div>
  );

  if (link) {
    return <Link to={link}>{content}</Link>;
  }

  return content;
};

// Quick Action Card Component
const QuickActionCard: React.FC<{
  title: string;
  description: string;
  icon: string;
  link: string;
}> = ({ title, description, icon, link }) => (
  <Link
    to={link}
    className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
  >
    <div className="flex items-center">
      <span className="text-4xl">{icon}</span>
      <div className="ml-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
    </div>
  </Link>
);

export default DashboardPage;
