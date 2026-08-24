from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import numpy as np
import logging

from app.models.training import Model, ModelStatus
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class ModelEvaluationService:
    """Service for model evaluation and backtesting."""

    async def evaluate_model(
        self,
        model_id: str,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> Dict[str, Any]:
        """Evaluate model performance on test data."""
        import joblib
        from sklearn.metrics import (
            mean_squared_error,
            mean_absolute_error,
            r2_score,
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
        )

        db = SessionLocal()
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model or not model.model_path:
                raise ValueError(f"Model {model_id} not found or not trained")

            # Safety: Loading locally-created model artifact only.
            # These are internal sklearn/xgb models, not from untrusted external sources.
            trained_model = joblib.load(model.model_path)

            # Make predictions
            y_pred = trained_model.predict(X_test)

            # Calculate regression metrics
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            # Direction accuracy
            direction_true = (y_test > 0).astype(int)
            direction_pred = (y_pred > 0).astype(int)
            direction_accuracy = accuracy_score(direction_true, direction_pred)
            direction_precision = precision_score(direction_true, direction_pred, zero_division=0)
            direction_recall = recall_score(direction_true, direction_pred, zero_division=0)
            direction_f1 = f1_score(direction_true, direction_pred, zero_division=0)

            # Update model with test metrics
            model.accuracy = direction_accuracy
            model.precision = direction_precision
            model.recall = direction_recall
            model.f1_score = direction_f1
            db.commit()

            return {
                "model_id": model_id,
                "regression_metrics": {
                    "mse": float(mse),
                    "rmse": float(rmse),
                    "mae": float(mae),
                    "r2": float(r2),
                },
                "classification_metrics": {
                    "accuracy": float(direction_accuracy),
                    "precision": float(direction_precision),
                    "recall": float(direction_recall),
                    "f1_score": float(direction_f1),
                },
                "sample_count": len(y_test),
                "evaluated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }

        finally:
            db.close()

    async def backtest_model(
        self,
        model_id: str,
        historical_data: List[Dict[str, Any]],
        initial_capital: float = 100000.0,
        position_size: float = 0.1,
        stop_loss: float = 0.05,
        take_profit: float = 0.1,
        transaction_cost: float = 0.001,
    ) -> Dict[str, Any]:
        """Backtest model on historical data."""
        import joblib

        db = SessionLocal()
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model or not model.model_path:
                raise ValueError(f"Model {model_id} not found or not trained")

            # Safety: Loading locally-created model artifact only.
            # These are internal sklearn/xgb models, not from untrusted external sources.
            trained_model = joblib.load(model.model_path)

            # Prepare features (simplified - in production, use proper feature engineering)
            X = np.array([
                [d.get("open", 0), d.get("high", 0), d.get("low", 0),
                 d.get("close", 0), d.get("volume", 0)]
                for d in historical_data
            ])

            # Make predictions
            predictions = trained_model.predict(X)

            # Run backtest simulation
            capital = initial_capital
            position = 0
            trades = []
            equity_curve = []

            for i in range(len(historical_data) - 1):
                current_price = historical_data[i].get("close", 0)
                next_price = historical_data[i + 1].get("close", 0)
                prediction = predictions[i]

                # Trading logic
                if prediction > 0 and position == 0:
                    # Buy signal
                    shares = int(capital * position_size / current_price)
                    if shares > 0:
                        cost = shares * current_price * (1 + transaction_cost)
                        capital -= cost
                        position = shares
                        trades.append({
                            "date": historical_data[i].get("date"),
                            "action": "buy",
                            "price": current_price,
                            "shares": shares,
                            "cost": cost,
                        })

                elif prediction < 0 and position > 0:
                    # Sell signal
                    revenue = position * current_price * (1 - transaction_cost)
                    capital += revenue
                    profit = revenue - (trades[-1]["cost"] if trades else 0)
                    trades.append({
                        "date": historical_data[i].get("date"),
                        "action": "sell",
                        "price": current_price,
                        "shares": position,
                        "revenue": revenue,
                        "profit": profit,
                    })
                    position = 0

                # Check stop loss / take profit
                if position > 0 and trades:
                    entry_price = trades[-1].get("price", current_price)
                    pnl_pct = (current_price - entry_price) / entry_price

                    if pnl_pct <= -stop_loss:
                        # Stop loss
                        revenue = position * current_price * (1 - transaction_cost)
                        capital += revenue
                        trades.append({
                            "date": historical_data[i].get("date"),
                            "action": "stop_loss",
                            "price": current_price,
                            "shares": position,
                            "revenue": revenue,
                        })
                        position = 0

                    elif pnl_pct >= take_profit:
                        # Take profit
                        revenue = position * current_price * (1 - transaction_cost)
                        capital += revenue
                        trades.append({
                            "date": historical_data[i].get("date"),
                            "action": "take_profit",
                            "price": current_price,
                            "shares": position,
                            "revenue": revenue,
                        })
                        position = 0

                # Record equity
                equity = capital + (position * current_price if position > 0 else 0)
                equity_curve.append({
                    "date": historical_data[i].get("date"),
                    "equity": equity,
                    "capital": capital,
                    "position_value": position * current_price if position > 0 else 0,
                })

            # Close any remaining position
            if position > 0:
                final_price = historical_data[-1].get("close", 0)
                revenue = position * final_price * (1 - transaction_cost)
                capital += revenue
                trades.append({
                    "date": historical_data[-1].get("date"),
                    "action": "close",
                    "price": final_price,
                    "shares": position,
                    "revenue": revenue,
                })
                position = 0

            # Calculate performance metrics
            final_equity = capital
            total_return = (final_equity - initial_capital) / initial_capital

            # Calculate max drawdown
            equity_values = [e["equity"] for e in equity_curve]
            max_drawdown = self._calculate_max_drawdown(equity_values)

            # Calculate Sharpe ratio
            returns = np.diff(equity_values) / equity_values[:-1]
            sharpe_ratio = self._calculate_sharpe_ratio(returns)

            # Win rate
            winning_trades = [t for t in trades if t.get("profit", 0) > 0]
            win_rate = len(winning_trades) / len(trades) if trades else 0

            # Update model with backtest results
            model.max_drawdown = max_drawdown
            model.sharpe_ratio = sharpe_ratio
            model.total_return = total_return
            model.backtest_results = {
                "initial_capital": initial_capital,
                "final_equity": final_equity,
                "total_return": total_return,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "total_trades": len(trades),
                "win_rate": win_rate,
            }
            db.commit()

            return {
                "model_id": model_id,
                "initial_capital": initial_capital,
                "final_equity": final_equity,
                "total_return": total_return,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "total_trades": len(trades),
                "win_rate": win_rate,
                "trades": trades,
                "equity_curve": equity_curve,
                "backtested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }

        finally:
            db.close()

    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown."""
        if not equity_curve:
            return 0.0

        peak = equity_curve[0]
        max_dd = 0.0

        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)

        return max_dd

    def _calculate_sharpe_ratio(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.02,
    ) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) == 0:
            return 0.0

        # Annualize returns (assuming daily returns)
        annual_return = np.mean(returns) * 252
        annual_std = np.std(returns) * np.sqrt(252)

        if annual_std == 0:
            return 0.0

        return (annual_return - risk_free_rate) / annual_std


# Global service instance
model_evaluation_service = ModelEvaluationService()
