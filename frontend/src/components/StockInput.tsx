import React, { useState, useEffect, useRef } from 'react';
import { stockService, StockValidationResponse, AutoCompleteResponse } from '../services/stockService';

interface StockInputProps {
  onStockSelect: (stock: StockValidationResponse) => void;
  onStocksSelect?: (stocks: StockValidationResponse[]) => void;
  multiple?: boolean;
  placeholder?: string;
  className?: string;
}

const StockInput: React.FC<StockInputProps> = ({
  onStockSelect,
  onStocksSelect,
  multiple = false,
  placeholder = '输入股票代码，如 AAPL 或 600519.SH',
  className = '',
}) => {
  const [inputValue, setInputValue] = useState('');
  const [suggestions, setSuggestions] = useState<AutoCompleteResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedStocks, setSelectedStocks] = useState<StockValidationResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Debounce autocomplete
  useEffect(() => {
    const timer = setTimeout(() => {
      if (inputValue.length >= 2) {
        fetchSuggestions(inputValue);
      } else {
        setSuggestions([]);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [inputValue]);

  // Close suggestions on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchSuggestions = async (query: string) => {
    setIsLoading(true);
    try {
      const results = await stockService.autocomplete(query, 10);
      setSuggestions(results);
      setShowSuggestions(true);
    } catch (err) {
      console.error('Autocomplete error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    setError(null);
  };

  const handleSuggestionClick = async (suggestion: AutoCompleteResponse) => {
    setInputValue(suggestion.symbol);
    setShowSuggestions(false);
    await validateAndSelect(suggestion.symbol);
  };

  const handleKeyDown = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (inputValue.trim()) {
        await validateAndSelect(inputValue.trim());
      }
    }
  };

  const validateAndSelect = async (symbol: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await stockService.validate(symbol);

      if (result.valid) {
        if (multiple) {
          const updatedStocks = [...selectedStocks, result];
          setSelectedStocks(updatedStocks);
          onStocksSelect?.(updatedStocks);
          setInputValue('');
        } else {
          onStockSelect(result);
          setInputValue(result.symbol);
        }
      } else {
        setError(result.error || '股票代码无效');
      }
    } catch (err) {
      setError('验证失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const removeStock = (symbol: string) => {
    const updatedStocks = selectedStocks.filter((s) => s.symbol !== symbol);
    setSelectedStocks(updatedStocks);
    onStocksSelect?.(updatedStocks);
  };

  return (
    <div className={`relative ${className}`}>
      {/* Selected stocks tags */}
      {multiple && selectedStocks.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {selectedStocks.map((stock) => (
            <span
              key={stock.symbol}
              className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
            >
              {stock.symbol}
              <button
                type="button"
                onClick={() => removeStock(stock.symbol)}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Input field */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder={placeholder}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
        />

        {isLoading && (
          <div className="absolute right-3 top-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto"
        >
          {suggestions.map((suggestion) => (
            <div
              key={suggestion.symbol}
              onClick={() => handleSuggestionClick(suggestion)}
              className="px-4 py-3 hover:bg-gray-100 cursor-pointer border-b border-gray-200 last:border-b-0"
            >
              <div className="font-medium text-gray-900">{suggestion.symbol}</div>
              {suggestion.name && (
                <div className="text-sm text-gray-500">{suggestion.name}</div>
              )}
              {suggestion.market && (
                <div className="text-xs text-gray-400">{suggestion.market}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Help text */}
      <p className="mt-2 text-sm text-gray-500">
        {multiple
          ? '输入股票代码后按回车添加，可添加多个'
          : '输入股票代码后按回车验证'}
      </p>
    </div>
  );
};

export default StockInput;
