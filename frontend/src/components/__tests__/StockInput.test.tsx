import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import StockInput from '../StockInput';

// Mock the stock service
jest.mock('../../services/stockService', () => ({
  stockService: {
    autocomplete: jest.fn().mockResolvedValue([
      { symbol: 'AAPL', name: 'Apple Inc.', market: 'US' },
      { symbol: 'AMZN', name: 'Amazon.com Inc.', market: 'US' },
    ]),
    validate: jest.fn().mockResolvedValue({
      valid: true,
      symbol: 'AAPL',
      name: 'Apple Inc.',
      market: 'US',
    }),
  },
}));

describe('StockInput', () => {
  const mockOnStockSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly', () => {
    render(<StockInput onStockSelect={mockOnStockSelect} />);

    expect(screen.getByPlaceholderText(/输入股票代码/)).toBeInTheDocument();
  });

  it('shows autocomplete suggestions after typing', async () => {
    render(<StockInput onStockSelect={mockOnStockSelect} />);

    const input = screen.getByPlaceholderText(/输入股票代码/);
    await userEvent.type(input, 'AA');

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('AMZN')).toBeInTheDocument();
    });
  });

  it('selects stock from autocomplete', async () => {
    render(<StockInput onStockSelect={mockOnStockSelect} />);

    const input = screen.getByPlaceholderText(/输入股票代码/);
    await userEvent.type(input, 'AA');

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('AAPL'));

    await waitFor(() => {
      expect(mockOnStockSelect).toHaveBeenCalledWith(
        expect.objectContaining({
          symbol: 'AAPL',
          valid: true,
        })
      );
    });
  });

  it('validates stock on Enter key', async () => {
    render(<StockInput onStockSelect={mockOnStockSelect} />);

    const input = screen.getByPlaceholderText(/输入股票代码/);
    await userEvent.type(input, 'AAPL');
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(mockOnStockSelect).toHaveBeenCalled();
    });
  });

  it('shows error for invalid stock', async () => {
    const { stockService } = require('../../services/stockService');
    stockService.validate.mockResolvedValueOnce({
      valid: false,
      symbol: 'INVALID',
      error: 'Stock not found',
    });

    render(<StockInput onStockSelect={mockOnStockSelect} />);

    const input = screen.getByPlaceholderText(/输入股票代码/);
    await userEvent.type(input, 'INVALID');
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(screen.getByText('Stock not found')).toBeInTheDocument();
    });
  });
});
