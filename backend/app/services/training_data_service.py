from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import logging

from app.services.historical_data_service import historical_data_service
from app.services.technical_indicators_service import technical_indicators_service
from app.core.cache import cache

logger = logging.getLogger(__name__)


class TrainingDataService:
    """Service for preparing training data for models."""

    # Default feature columns
    DEFAULT_FEATURES = [
        "open", "high", "low", "close", "volume",
        "sma_5", "sma_10", "sma_20", "sma_50",
        "rsi_14", "macd", "macd_signal",
        "bb_upper", "bb_middle", "bb_lower",
        "atr_14", "volume_ratio",
    ]

    async def prepare_training_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        target_column: str = "close",
        prediction_horizon: int = 5,
        features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Prepare training data for a symbol."""
        # Check cache
        cache_key = cache.get_stock_cache_key(
            symbol,
            f"training_data_{start_date}_{end_date}_{prediction_horizon}",
        )
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Get historical data
            historical_data = await historical_data_service.get_historical_prices(
                symbol,
                start_date=start_date,
                end_date=end_date,
                period="2y",
                interval="1d",
            )

            data = historical_data.get("data", [])
            if not data:
                raise ValueError(f"No data available for {symbol}")

            # Convert to DataFrame
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

            # Add technical indicators
            df = await self._add_technical_indicators(df, symbol)

            # Select features
            feature_cols = features or self.DEFAULT_FEATURES
            available_features = [f for f in feature_cols if f in df.columns]

            # Create target variable (future price change)
            df["target"] = df[target_column].shift(-prediction_horizon)
            df["target_return"] = (df["target"] - df[target_column]) / df[target_column]
            df["target_direction"] = (df["target_return"] > 0).astype(int)

            # Drop rows with NaN
            df = df.dropna()

            # Split features and target
            X = df[available_features].values
            y_reg = df["target_return"].values
            y_cls = df["target_direction"].values
            dates = df["date"].values

            # Train/validation/test split (70/15/15)
            n = len(X)
            train_idx = int(n * 0.7)
            val_idx = int(n * 0.85)

            result = {
                "symbol": symbol,
                "features": available_features,
                "feature_count": len(available_features),
                "total_samples": n,
                "train_samples": train_idx,
                "val_samples": val_idx - train_idx,
                "test_samples": n - val_idx,
                "prediction_horizon": prediction_horizon,
                "target_column": target_column,
                "data": {
                    "X_train": X[:train_idx].tolist(),
                    "X_val": X[train_idx:val_idx].tolist(),
                    "X_test": X[val_idx:].tolist(),
                    "y_train": y_reg[:train_idx].tolist(),
                    "y_val": y_reg[train_idx:val_idx].tolist(),
                    "y_test": y_reg[val_idx:].tolist(),
                    "y_cls_train": y_cls[:train_idx].tolist(),
                    "y_cls_val": y_cls[train_idx:val_idx].tolist(),
                    "y_cls_test": y_cls[val_idx:].tolist(),
                    "dates_train": dates[:train_idx].tolist(),
                    "dates_val": dates[train_idx:val_idx].tolist(),
                    "dates_test": dates[val_idx:].tolist(),
                },
                "statistics": self._calculate_statistics(df, available_features),
                "prepared_at": datetime.utcnow().isoformat(),
            }

            # Cache for 1 hour
            cache.set(cache_key, result, expire=3600)

            return result

        except Exception as e:
            logger.error(f"Error preparing training data for {symbol}: {e}")
            raise

    async def prepare_multi_stock_data(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        prediction_horizon: int = 5,
    ) -> Dict[str, Any]:
        """Prepare training data for multiple stocks."""
        all_data = {}

        for symbol in symbols:
            try:
                data = await self.prepare_training_data(
                    symbol,
                    start_date=start_date,
                    end_date=end_date,
                    prediction_horizon=prediction_horizon,
                )
                all_data[symbol] = data
            except Exception as e:
                logger.error(f"Error preparing data for {symbol}: {e}")
                continue

        if not all_data:
            raise ValueError("No data available for any symbol")

        # Combine data
        combined_X_train = []
        combined_y_train = []
        combined_X_val = []
        combined_y_val = []

        for symbol, data in all_data.items():
            combined_X_train.extend(data["data"]["X_train"])
            combined_y_train.extend(data["data"]["y_train"])
            combined_X_val.extend(data["data"]["X_val"])
            combined_y_val.extend(data["data"]["y_val"])

        return {
            "symbols": list(all_data.keys()),
            "symbol_count": len(all_data),
            "features": list(all_data.values())[0]["features"],
            "prediction_horizon": prediction_horizon,
            "combined_data": {
                "X_train": combined_X_train,
                "y_train": combined_y_train,
                "X_val": combined_X_val,
                "y_val": combined_y_val,
            },
            "per_stock_data": all_data,
            "prepared_at": datetime.utcnow().isoformat(),
        }

    async def _add_technical_indicators(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> pd.DataFrame:
        """Add technical indicators to DataFrame."""
        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values
        volumes = df["volume"].values

        # Moving averages
        for period in [5, 10, 20, 50]:
            df[f"sma_{period}"] = pd.Series(closes).rolling(window=period).mean()

        # RSI
        df["rsi_14"] = self._calculate_rsi_series(closes, 14)

        # MACD
        ema_12 = pd.Series(closes).ewm(span=12, adjust=False).mean()
        ema_26 = pd.Series(closes).ewm(span=26, adjust=False).mean()
        df["macd"] = ema_12 - ema_26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

        # Bollinger Bands
        sma_20 = pd.Series(closes).rolling(window=20).mean()
        std_20 = pd.Series(closes).rolling(window=20).std()
        df["bb_upper"] = sma_20 + (std_20 * 2)
        df["bb_middle"] = sma_20
        df["bb_lower"] = sma_20 - (std_20 * 2)

        # ATR
        df["atr_14"] = self._calculate_atr_series(highs, lows, closes, 14)

        # Volume ratio
        volume_sma = pd.Series(volumes).rolling(window=20).mean()
        df["volume_ratio"] = pd.Series(volumes) / volume_sma

        # Price changes
        df["price_change"] = pd.Series(closes).pct_change()
        df["price_change_5d"] = pd.Series(closes).pct_change(periods=5)

        # Volatility
        df["volatility_20d"] = pd.Series(closes).rolling(window=20).std() / sma_20

        return df

    def _calculate_rsi_series(
        self,
        prices: np.ndarray,
        period: int,
    ) -> pd.Series:
        """Calculate RSI as pandas Series."""
        deltas = pd.Series(prices).diff()
        gain = (deltas.where(deltas > 0, 0)).rolling(window=period).mean()
        loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_atr_series(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int,
    ) -> pd.Series:
        """Calculate ATR as pandas Series."""
        high_series = pd.Series(highs)
        low_series = pd.Series(lows)
        close_series = pd.Series(closes)

        tr1 = high_series - low_series
        tr2 = abs(high_series - close_series.shift())
        tr3 = abs(low_series - close_series.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def _calculate_statistics(
        self,
        df: pd.DataFrame,
        features: List[str],
    ) -> Dict[str, Any]:
        """Calculate statistics for features."""
        stats = {}

        for feature in features:
            if feature in df.columns:
                series = df[feature]
                stats[feature] = {
                    "mean": float(series.mean()),
                    "std": float(series.std()),
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "median": float(series.median()),
                    "missing": int(series.isna().sum()),
                }

        # Target statistics
        if "target_return" in df.columns:
            target = df["target_return"]
            stats["target_return"] = {
                "mean": float(target.mean()),
                "std": float(target.std()),
                "min": float(target.min()),
                "max": float(target.max()),
                "positive_ratio": float((target > 0).mean()),
            }

        return stats


# Global service instance
training_data_service = TrainingDataService()
