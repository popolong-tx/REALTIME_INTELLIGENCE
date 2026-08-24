import React, { useState, useEffect } from 'react';
import { StockValidationResponse } from '../services/stockService';

interface SearchHistoryProps {
  onSelect: (stock: StockValidationResponse) => void;
  className?: string;
}

const STORAGE_KEY = 'stock_search_history';
const MAX_HISTORY = 20;

const SearchHistory: React.FC<SearchHistoryProps> = ({
  onSelect,
  className = '',
}) => {
  const [history, setHistory] = useState<StockValidationResponse[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  // Load history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse search history:', e);
      }
    }
  }, []);

  // Save history to localStorage
  const saveHistory = (newHistory: StockValidationResponse[]) => {
    setHistory(newHistory);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory));
  };

  // Add to history
  const addToHistory = (stock: StockValidationResponse) => {
    const filtered = history.filter((h) => h.symbol !== stock.symbol);
    const newHistory = [stock, ...filtered].slice(0, MAX_HISTORY);
    saveHistory(newHistory);
  };

  // Remove from history
  const removeFromHistory = (symbol: string) => {
    const newHistory = history.filter((h) => h.symbol !== symbol);
    saveHistory(newHistory);
  };

  // Clear all history
  const clearHistory = () => {
    saveHistory([]);
  };

  // Handle stock selection
  const handleSelect = (stock: StockValidationResponse) => {
    onSelect(stock);
    addToHistory(stock);
    setIsOpen(false);
  };

  if (history.length === 0) {
    return null;
  }

  return (
    <div className={`relative ${className}`}>
      {/* Toggle button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center text-sm text-gray-500 hover:text-gray-700"
      >
        <svg
          className="w-4 h-4 mr-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        搜索历史 ({history.length})
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-20 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
            <h3 className="font-medium text-gray-900">搜索历史</h3>
            <button
              onClick={clearHistory}
              className="text-sm text-red-600 hover:text-red-800"
            >
              清空
            </button>
          </div>

          {/* History list */}
          <div className="max-h-60 overflow-y-auto">
            {history.map((stock) => (
              <div
                key={stock.symbol}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
              >
                <button
                  onClick={() => handleSelect(stock)}
                  className="flex-1 text-left"
                >
                  <div className="font-medium text-gray-900">
                    {stock.symbol}
                  </div>
                  {stock.name && (
                    <div className="text-sm text-gray-500">{stock.name}</div>
                  )}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFromHistory(stock.symbol);
                  }}
                  className="ml-2 text-gray-400 hover:text-gray-600"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="px-4 py-2 bg-gray-50 text-sm text-gray-500">
            点击选择，×移除
          </div>
        </div>
      )}
    </div>
  );
};

// Export helper function to add to history
export const addToSearchHistory = (stock: StockValidationResponse) => {
  const saved = localStorage.getItem(STORAGE_KEY);
  let history: StockValidationResponse[] = [];

  if (saved) {
    try {
      history = JSON.parse(saved);
    } catch (e) {
      console.error('Failed to parse search history:', e);
    }
  }

  const filtered = history.filter((h) => h.symbol !== stock.symbol);
  const newHistory = [stock, ...filtered].slice(0, MAX_HISTORY);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory));
};

export default SearchHistory;
