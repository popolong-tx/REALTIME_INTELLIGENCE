import React, { useState } from 'react';
import StockInput from '../components/StockInput';
import BatchStockInput from '../components/BatchStockInput';
import SearchHistory from '../components/SearchHistory';
import { PageHeader, Breadcrumb } from '../components/MainLayout';
import { StockValidationResponse } from '../services/stockService';

const StockSearchPage: React.FC = () => {
  const [selectedStock, setSelectedStock] = useState<StockValidationResponse | null>(null);
  const [searchMode, setSearchMode] = useState<'single' | 'batch'>('single');
  const [searchResults, setSearchResults] = useState<StockValidationResponse[]>([]);

  const handleStockSelect = (stock: StockValidationResponse) => {
    setSelectedStock(stock);
    // Navigate to stock detail or add to results
    setSearchResults((prev) => {
      const exists = prev.find((s) => s.symbol === stock.symbol);
      if (exists) return prev;
      return [...prev, stock];
    });
  };

  const handleBatchSelect = (stocks: StockValidationResponse[]) => {
    setSearchResults((prev) => {
      const newStocks = stocks.filter(
        (s) => !prev.find((p) => p.symbol === s.symbol)
      );
      return [...prev, ...newStocks];
    });
  };

  const handleRemoveStock = (symbol: string) => {
    setSearchResults((prev) => prev.filter((s) => s.symbol !== symbol));
    if (selectedStock?.symbol === symbol) {
      setSelectedStock(null);
    }
  };

  return (
    <div>
      <Breadcrumb items={[{ label: '股票查询' }]} />

      <PageHeader
        title="股票查询"
        description="输入股票代码查询相关信息"
      />

      {/* Search Mode Toggle */}
      <div className="mb-6">
        <div className="flex space-x-4">
          <button
            onClick={() => setSearchMode('single')}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              searchMode === 'single'
                ? 'bg-blue-100 text-blue-700 border border-blue-300'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            单股票查询
          </button>
          <button
            onClick={() => setSearchMode('batch')}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              searchMode === 'batch'
                ? 'bg-blue-100 text-blue-700 border border-blue-300'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            批量查询
          </button>
        </div>
      </div>

      {/* Search Input */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {searchMode === 'single' ? (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                输入股票代码
              </h2>
              <StockInput
                onStockSelect={handleStockSelect}
                placeholder="输入股票代码，如 AAPL 或 600519.SH"
              />
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                批量输入股票代码
              </h2>
              <BatchStockInput onStocksValidated={handleBatchSelect} />
            </div>
          )}

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="mt-6 bg-white rounded-lg shadow">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">
                  查询结果 ({searchResults.length})
                </h2>
              </div>
              <div className="divide-y divide-gray-200">
                {searchResults.map((stock) => (
                  <div
                    key={stock.symbol}
                    className={`p-4 hover:bg-gray-50 cursor-pointer ${
                      selectedStock?.symbol === stock.symbol
                        ? 'bg-blue-50'
                        : ''
                    }`}
                    onClick={() => setSelectedStock(stock)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">
                          {stock.symbol}
                        </h3>
                        {stock.name && (
                          <p className="text-sm text-gray-500">{stock.name}</p>
                        )}
                        <div className="flex space-x-4 mt-1 text-xs text-gray-400">
                          {stock.market && <span>市场: {stock.market}</span>}
                          {stock.exchange && <span>交易所: {stock.exchange}</span>}
                          {stock.sector && <span>行业: {stock.sector}</span>}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            // Navigate to stock detail
                          }}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          查看详情
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveStock(stock.symbol);
                          }}
                          className="px-3 py-1 text-sm text-red-600 hover:text-red-800"
                        >
                          移除
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Search History */}
          <div className="bg-white rounded-lg shadow p-6">
            <SearchHistory onSelect={handleStockSelect} />
          </div>

          {/* Quick Tips */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              查询提示
            </h3>
            <ul className="space-y-3 text-sm text-gray-600">
              <li className="flex items-start">
                <span className="mr-2">💡</span>
                <span>支持美股、港股、A股等多种市场格式</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">💡</span>
                <span>输入至少2个字符可触发自动补全</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">💡</span>
                <span>批量查询时用逗号或换行分隔股票代码</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">💡</span>
                <span>查询结果将保存在搜索历史中</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockSearchPage;
