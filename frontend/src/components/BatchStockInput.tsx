import React, { useState } from 'react';
import { stockService, StockValidationResponse } from '../services/stockService';

interface BatchStockInputProps {
  onStocksValidated: (stocks: StockValidationResponse[]) => void;
  className?: string;
}

const BatchStockInput: React.FC<BatchStockInputProps> = ({
  onStocksValidated,
  className = '',
}) => {
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<StockValidationResponse[]>([]);
  const [error, setError] = useState<string | null>(null);

  const parseStockCodes = (text: string): string[] => {
    // Split by comma, newline, or space
    return text
      .split(/[,\\n\\s]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  };

  const handleValidate = async () => {
    const symbols = parseStockCodes(inputText);

    if (symbols.length === 0) {
      setError('请输入至少一个股票代码');
      return;
    }

    if (symbols.length > 50) {
      setError('最多支持50个股票代码');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const validationResults = await stockService.batchValidate(symbols);
      setResults(validationResults.results);

      const validStocks = validationResults.results.filter((r) => r.valid);
      if (validStocks.length > 0) {
        onStocksValidated(validStocks);
      }

      if (validStocks.length === 0) {
        setError('没有找到有效的股票代码');
      }
    } catch (err) {
      setError('验证失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setInputText('');
    setResults([]);
    setError(null);
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    // Allow paste to work normally
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Input area */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          批量输入股票代码
        </label>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onPaste={handlePaste}
          placeholder={'输入多个股票代码，用逗号、换行或空格分隔\\n例如：AAPL, MSFT, 600519.SH\\n000858.SZ, GOOGL'}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent h-32 resize-none"
          disabled={isLoading}
        />
      </div>

      {/* Action buttons */}
      <div className="flex space-x-3">
        <button
          onClick={handleValidate}
          disabled={isLoading || !inputText.trim()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? '验证中...' : '批量验证'}
        </button>
        <button
          onClick={handleClear}
          disabled={isLoading}
          className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50"
        >
          清空
        </button>
      </div>

      {/* Error message */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
            <h3 className="font-medium text-gray-900">验证结果</h3>
            <p className="text-sm text-gray-500">
              共 {results.length} 个，有效 {results.filter((r) => r.valid).length} 个，
              无效 {results.filter((r) => !r.valid).length} 个
            </p>
          </div>

          <div className="divide-y divide-gray-200 max-h-60 overflow-y-auto">
            {results.map((result) => (
              <div
                key={result.symbol}
                className={`px-4 py-3 ${
                  result.valid ? 'bg-white' : 'bg-red-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-gray-900">
                      {result.symbol}
                    </span>
                    {result.name && (
                      <span className="ml-2 text-gray-500">{result.name}</span>
                    )}
                  </div>
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      result.valid
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {result.valid ? '有效' : '无效'}
                  </span>
                </div>
                {result.error && (
                  <p className="text-sm text-red-600 mt-1">{result.error}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Help text */}
      <p className="text-sm text-gray-500">
        支持美股、港股、A股等多种市场格式，最多支持50个股票代码
      </p>
    </div>
  );
};

export default BatchStockInput;
