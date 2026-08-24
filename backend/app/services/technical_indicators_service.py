from typing import Optional, Dict, Any, List
import numpy as np
from datetime import datetime
import logging

from app.services.historical_data_service import historical_data_service
from app.core.cache import cache

logger = logging.getLogger(__name__)


class TechnicalIndicatorsService:
    """Service for calculating technical indicators."""

    async def get_technical_analysis(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> Dict[str, Any]:
        """Get comprehensive technical analysis."""
        cache_key = cache.get_stock_cache_key(symbol, f"technical_{period}_{interval}")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Get historical data
            historical_data = await historical_data_service.get_historical_prices(
                symbol, period=period, interval=interval
            )

            data = historical_data.get("data", [])
            if not data:
                raise ValueError(f"No data available for {symbol}")

            # Extract price arrays
            closes = np.array([float(d["close"]) for d in data])
            highs = np.array([float(d["high"]) for d in data])
            lows = np.array([float(d["low"]) for d in data])
            volumes = np.array([float(d["volume"]) for d in data])

            # Calculate indicators
            result = {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data_points": len(data),
                "indicators": {
                    "moving_averages": self._calculate_moving_averages(closes),
                    "oscillators": self._calculate_oscillators(closes, highs, lows),
                    "volatility": self._calculate_volatility_indicators(closes, highs, lows),
                    "volume": self._calculate_volume_indicators(closes, volumes),
                    "trend": self._calculate_trend_indicators(closes, highs, lows),
                },
                "signals": self._generate_signals(closes, highs, lows, volumes),
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache for 15 minutes
            cache.set(cache_key, result, expire=900)

            return result

        except Exception as e:
            logger.error(f"Error calculating technical analysis for {symbol}: {e}")
            raise

    def _calculate_moving_averages(
        self,
        closes: np.ndarray,
    ) -> Dict[str, Any]:
        """Calculate moving averages."""
        ma_periods = [5, 10, 20, 50, 100, 200]
        ema_periods = [12, 26, 50]

        result = {
            "sma": {},
            "ema": {},
        }

        # Simple Moving Averages
        for period in ma_periods:
            if len(closes) >= period:
                sma = np.convolve(closes, np.ones(period)/period, mode='valid')
                result["sma"][f"sma_{period}"] = float(sma[-1]) if len(sma) > 0 else None

        # Exponential Moving Averages
        for period in ema_periods:
            if len(closes) >= period:
                ema = self._calculate_ema(closes, period)
                result["ema"][f"ema_{period}"] = float(ema[-1]) if len(ema) > 0 else None

        # Current price position relative to MAs
        current_price = closes[-1]
        ma_positions = {}
        for key, value in result["sma"].items():
            if value is not None:
                ma_positions[key] = "above" if current_price > value else "below"

        result["positions"] = ma_positions

        return result

    def _calculate_ema(
        self,
        data: np.ndarray,
        period: int,
    ) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        multiplier = 2 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]

        for i in range(1, len(data)):
            ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]

        return ema

    def _calculate_oscillators(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
    ) -> Dict[str, Any]:
        """Calculate oscillator indicators."""
        result = {}

        # RSI (Relative Strength Index)
        if len(closes) >= 14:
            result["rsi"] = self._calculate_rsi(closes, 14)

        # MACD
        if len(closes) >= 26:
            result["macd"] = self._calculate_macd(closes)

        # Stochastic Oscillator
        if len(closes) >= 14:
            result["stochastic"] = self._calculate_stochastic(closes, highs, lows, 14)

        # Williams %R
        if len(closes) >= 14:
            result["williams_r"] = self._calculate_williams_r(highs, lows, closes, 14)

        # CCI (Commodity Channel Index)
        if len(closes) >= 20:
            result["cci"] = self._calculate_cci(highs, lows, closes, 20)

        return result

    def _calculate_rsi(
        self,
        closes: np.ndarray,
        period: int,
    ) -> Dict[str, Any]:
        """Calculate RSI."""
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # RSI interpretation
        if rsi > 70:
            signal = "overbought"
        elif rsi < 30:
            signal = "oversold"
        else:
            signal = "neutral"

        return {
            "value": round(rsi, 2),
            "signal": signal,
            "period": period,
        }

    def _calculate_macd(
        self,
        closes: np.ndarray,
    ) -> Dict[str, Any]:
        """Calculate MACD."""
        ema_12 = self._calculate_ema(closes, 12)
        ema_26 = self._calculate_ema(closes, 26)

        macd_line = ema_12 - ema_26
        signal_line = self._calculate_ema(macd_line, 9)
        histogram = macd_line - signal_line

        # MACD signal
        if histogram[-1] > 0 and histogram[-2] <= 0:
            signal = "bullish_crossover"
        elif histogram[-1] < 0 and histogram[-2] >= 0:
            signal = "bearish_crossover"
        elif histogram[-1] > 0:
            signal = "bullish"
        else:
            signal = "bearish"

        return {
            "macd_line": round(float(macd_line[-1]), 4),
            "signal_line": round(float(signal_line[-1]), 4),
            "histogram": round(float(histogram[-1]), 4),
            "signal": signal,
        }

    def _calculate_stochastic(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        period: int,
    ) -> Dict[str, Any]:
        """Calculate Stochastic Oscillator."""
        highest_high = np.max(highs[-period:])
        lowest_low = np.min(lows[-period:])

        if highest_high == lowest_low:
            k_percent = 50
        else:
            k_percent = ((closes[-1] - lowest_low) / (highest_high - lowest_low)) * 100

        # Simple 3-period SMA of %K for %D
        k_values = []
        for i in range(-3, 0):
            hh = np.max(highs[i-period:i])
            ll = np.min(lows[i-period:i])
            if hh == ll:
                k_values.append(50)
            else:
                k_values.append(((closes[i] - ll) / (hh - ll)) * 100)

        d_percent = np.mean(k_values)

        # Stochastic signal
        if k_percent > 80:
            signal = "overbought"
        elif k_percent < 20:
            signal = "oversold"
        else:
            signal = "neutral"

        return {
            "k_percent": round(k_percent, 2),
            "d_percent": round(d_percent, 2),
            "signal": signal,
        }

    def _calculate_williams_r(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int,
    ) -> Dict[str, Any]:
        """Calculate Williams %R."""
        highest_high = np.max(highs[-period:])
        lowest_low = np.min(lows[-period:])

        if highest_high == lowest_low:
            williams_r = -50
        else:
            williams_r = ((highest_high - closes[-1]) / (highest_high - lowest_low)) * -100

        # Williams %R signal
        if williams_r > -20:
            signal = "overbought"
        elif williams_r < -80:
            signal = "oversold"
        else:
            signal = "neutral"

        return {
            "value": round(williams_r, 2),
            "signal": signal,
        }

    def _calculate_cci(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int,
    ) -> Dict[str, Any]:
        """Calculate CCI (Commodity Channel Index)."""
        typical_price = (highs + lows + closes) / 3
        sma = np.mean(typical_price[-period:])
        mean_deviation = np.mean(np.abs(typical_price[-period:] - sma))

        if mean_deviation == 0:
            cci = 0
        else:
            cci = (typical_price[-1] - sma) / (0.015 * mean_deviation)

        # CCI signal
        if cci > 100:
            signal = "overbought"
        elif cci < -100:
            signal = "oversold"
        else:
            signal = "neutral"

        return {
            "value": round(cci, 2),
            "signal": signal,
        }

    def _calculate_volatility_indicators(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
    ) -> Dict[str, Any]:
        """Calculate volatility indicators."""
        result = {}

        # Bollinger Bands
        if len(closes) >= 20:
            result["bollinger_bands"] = self._calculate_bollinger_bands(closes, 20)

        # ATR (Average True Range)
        if len(closes) >= 14:
            result["atr"] = self._calculate_atr(highs, lows, closes, 14)

        return result

    def _calculate_bollinger_bands(
        self,
        closes: np.ndarray,
        period: int,
        std_dev: int = 2,
    ) -> Dict[str, Any]:
        """Calculate Bollinger Bands."""
        sma = np.mean(closes[-period:])
        std = np.std(closes[-period:])

        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)

        # Current price position
        current_price = closes[-1]
        bandwidth = (upper_band - lower_band) / sma * 100

        if current_price > upper_band:
            signal = "above_upper"
        elif current_price < lower_band:
            signal = "below_lower"
        else:
            signal = "within_bands"

        return {
            "upper_band": round(upper_band, 2),
            "middle_band": round(sma, 2),
            "lower_band": round(lower_band, 2),
            "bandwidth": round(bandwidth, 2),
            "signal": signal,
        }

    def _calculate_atr(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int,
    ) -> Dict[str, Any]:
        """Calculate ATR (Average True Range)."""
        true_ranges = []

        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1]),
            )
            true_ranges.append(tr)

        atr = np.mean(true_ranges[-period:])

        # ATR as percentage of price
        atr_percent = (atr / closes[-1]) * 100

        return {
            "value": round(atr, 2),
            "percent": round(atr_percent, 2),
            "interpretation": "high" if atr_percent > 3 else "low",
        }

    def _calculate_volume_indicators(
        self,
        closes: np.ndarray,
        volumes: np.ndarray,
    ) -> Dict[str, Any]:
        """Calculate volume indicators."""
        result = {}

        # Volume SMA
        if len(volumes) >= 20:
            volume_sma = np.mean(volumes[-20:])
            current_volume = volumes[-1]
            volume_ratio = current_volume / volume_sma if volume_sma > 0 else 1

            result["volume_sma_20"] = round(volume_sma, 0)
            result["volume_ratio"] = round(volume_ratio, 2)
            result["volume_signal"] = "high" if volume_ratio > 1.5 else "low" if volume_ratio < 0.5 else "normal"

        # OBV (On-Balance Volume)
        if len(closes) >= 2:
            obv = self._calculate_obv(closes, volumes)
            result["obv"] = obv

        return result

    def _calculate_obv(
        self,
        closes: np.ndarray,
        volumes: np.ndarray,
    ) -> Dict[str, Any]:
        """Calculate OBV (On-Balance Volume)."""
        obv = np.zeros_like(volumes)
        obv[0] = volumes[0]

        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv[i] = obv[i-1] + volumes[i]
            elif closes[i] < closes[i-1]:
                obv[i] = obv[i-1] - volumes[i]
            else:
                obv[i] = obv[i-1]

        # OBV trend
        obv_sma = np.mean(obv[-20:]) if len(obv) >= 20 else obv[-1]
        obv_signal = "bullish" if obv[-1] > obv_sma else "bearish"

        return {
            "current": round(float(obv[-1]), 0),
            "signal": obv_signal,
        }

    def _calculate_trend_indicators(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
    ) -> Dict[str, Any]:
        """Calculate trend indicators."""
        result = {}

        # ADX (Average Directional Index)
        if len(closes) >= 14:
            result["adx"] = self._calculate_adx(highs, lows, closes, 14)

        # Parabolic SAR
        if len(closes) >= 2:
            result["parabolic_sar"] = self._calculate_parabolic_sar(highs, lows, closes)

        return result

    def _calculate_adx(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int,
    ) -> Dict[str, Any]:
        """Calculate ADX (Average Directional Index)."""
        # Simplified ADX calculation
        # In production, use a proper technical analysis library

        # Calculate +DM and -DM
        plus_dm = np.zeros(len(highs))
        minus_dm = np.zeros(len(lows))

        for i in range(1, len(highs)):
            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]

            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move

        # Calculate TR
        tr = np.zeros(len(closes))
        for i in range(1, len(closes)):
            tr[i] = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1]),
            )

        # Smoothed values
        atr = np.mean(tr[-period:])
        plus_di = (np.mean(plus_dm[-period:]) / atr) * 100 if atr > 0 else 0
        minus_di = (np.mean(minus_dm[-period:]) / atr) * 100 if atr > 0 else 0

        # ADX
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        adx = dx  # Simplified; should be smoothed

        # ADX interpretation
        if adx > 25:
            trend_strength = "strong"
        elif adx > 20:
            trend_strength = "moderate"
        else:
            trend_strength = "weak"

        return {
            "value": round(adx, 2),
            "plus_di": round(plus_di, 2),
            "minus_di": round(minus_di, 2),
            "trend_strength": trend_strength,
            "trend_direction": "bullish" if plus_di > minus_di else "bearish",
        }

    def _calculate_parabolic_sar(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
    ) -> Dict[str, Any]:
        """Calculate Parabolic SAR."""
        # Simplified Parabolic SAR
        # In production, use a proper technical analysis library

        af = 0.02  # Acceleration factor
        max_af = 0.20

        # Determine initial trend
        if closes[-1] > closes[-2]:
            trend = "bullish"
            sar = lows[-1]
        else:
            trend = "bearish"
            sar = highs[-1]

        return {
            "value": round(sar, 2),
            "trend": trend,
            "signal": "buy" if trend == "bullish" else "sell",
        }

    def _generate_signals(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        volumes: np.ndarray,
    ) -> Dict[str, Any]:
        """Generate trading signals based on indicators."""
        signals = []

        # RSI signal
        if len(closes) >= 14:
            rsi = self._calculate_rsi(closes, 14)
            if rsi["signal"] == "oversold":
                signals.append({
                    "indicator": "RSI",
                    "signal": "buy",
                    "strength": "moderate",
                    "reason": f"RSI at {rsi['value']} indicates oversold conditions",
                })
            elif rsi["signal"] == "overbought":
                signals.append({
                    "indicator": "RSI",
                    "signal": "sell",
                    "strength": "moderate",
                    "reason": f"RSI at {rsi['value']} indicates overbought conditions",
                })

        # MACD signal
        if len(closes) >= 26:
            macd = self._calculate_macd(closes)
            if macd["signal"] == "bullish_crossover":
                signals.append({
                    "indicator": "MACD",
                    "signal": "buy",
                    "strength": "strong",
                    "reason": "MACD bullish crossover",
                })
            elif macd["signal"] == "bearish_crossover":
                signals.append({
                    "indicator": "MACD",
                    "signal": "sell",
                    "strength": "strong",
                    "reason": "MACD bearish crossover",
                })

        # Moving average signals
        if len(closes) >= 50:
            sma_20 = np.mean(closes[-20:])
            sma_50 = np.mean(closes[-50:])

            if sma_20 > sma_50 and closes[-1] > sma_20:
                signals.append({
                    "indicator": "MA",
                    "signal": "buy",
                    "strength": "moderate",
                    "reason": "Price above SMA20, SMA20 above SMA50",
                })
            elif sma_20 < sma_50 and closes[-1] < sma_20:
                signals.append({
                    "indicator": "MA",
                    "signal": "sell",
                    "strength": "moderate",
                    "reason": "Price below SMA20, SMA20 below SMA50",
                })

        # Overall signal
        buy_signals = sum(1 for s in signals if s["signal"] == "buy")
        sell_signals = sum(1 for s in signals if s["signal"] == "sell")

        if buy_signals > sell_signals:
            overall = "bullish"
        elif sell_signals > buy_signals:
            overall = "bearish"
        else:
            overall = "neutral"

        return {
            "individual_signals": signals,
            "buy_count": buy_signals,
            "sell_count": sell_signals,
            "overall_signal": overall,
        }


# Global service instance
technical_indicators_service = TechnicalIndicatorsService()
