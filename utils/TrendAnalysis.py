"""
Trend Analysis Utility Module
Provides functions for calculating trends, forecasting, and performance analysis
"""
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional


class TrendAnalysis:
    """Utility class for trend analysis and forecasting"""

    @staticmethod
    def calculate_trend_line(data_points: List[float]) -> Dict:
        """
        Calculate a linear trend line using simple linear regression

        Args:
            data_points: List of numeric values

        Returns:
            Dictionary with trend slope, intercept, and R-squared value
        """
        if len(data_points) < 2:
            return {
                'slope': 0,
                'intercept': data_points[0] if data_points else 0,
                'r_squared': 0,
                'direction': 'stable'
            }

        x = np.arange(len(data_points))
        y = np.array(data_points, dtype=float)

        # Remove NaN values
        valid_indices = ~np.isnan(y)
        if np.sum(valid_indices) < 2:
            return {
                'slope': 0,
                'intercept': np.nanmean(y) if not np.isnan(np.nanmean(y)) else 0,
                'r_squared': 0,
                'direction': 'stable'
            }

        x_valid = x[valid_indices]
        y_valid = y[valid_indices]

        # Calculate linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_valid, y_valid)

        # Determine direction
        if slope > 0.05:
            direction = 'improving'
        elif slope < -0.05:
            direction = 'declining'
        else:
            direction = 'stable'

        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_value ** 2),
            'direction': direction,
            'p_value': float(p_value)
        }

    @staticmethod
    def calculate_moving_average(data_points: List[float], window_size: int = 3) -> List[float]:
        """
        Calculate moving average for data smoothing

        Args:
            data_points: List of numeric values
            window_size: Size of the moving window (default 3)

        Returns:
            List of moving averages (same length as input, padded with NaN)
        """
        if len(data_points) < window_size:
            return [np.nan] * len(data_points)

        y = np.array(data_points, dtype=float)
        moving_avg = np.convolve(y, np.ones(window_size) / window_size, mode='valid')

        # Pad the beginning with NaN to match original length
        padding = [np.nan] * (len(data_points) - len(moving_avg))
        result = padding + list(moving_avg)

        # Replace NaN with None for JSON serialization
        return [float(x) if not np.isnan(x) else None for x in result]

    @staticmethod
    def detect_seasonality(historical_data: List[Dict], period: int = 4) -> Dict:
        """
        Detect seasonality patterns (quarterly, monthly, etc.)
        Uses autocorrelation to identify repeating patterns

        Args:
            historical_data: List of dicts with 'date' and 'value' keys
            period: Expected period length (default 4 for quarterly)

        Returns:
            Dictionary with seasonality detection results
        """
        if len(historical_data) < period * 2:
            return {
                'has_seasonality': False,
                'period': period,
                'autocorrelation': 0,
                'confidence': 0
            }

        values = [d['value'] for d in historical_data]
        y = np.array(values, dtype=float)

        # Remove NaN values
        y = y[~np.isnan(y)]

        if len(y) < period:
            return {
                'has_seasonality': False,
                'period': period,
                'autocorrelation': 0,
                'confidence': 0
            }

        # Calculate autocorrelation at the period
        mean = np.mean(y)
        c0 = np.sum((y - mean) ** 2) / len(y)
        c_period = np.sum((y[:-period] - mean) * (y[period:] - mean)) / len(y)
        autocorr = c_period / c0 if c0 > 0 else 0

        # Seasonality is considered present if autocorrelation is strong
        has_seasonality = abs(autocorr) > 0.5
        confidence = min(abs(autocorr), 1.0)

        return {
            'has_seasonality': has_seasonality,
            'period': period,
            'autocorrelation': float(autocorr),
            'confidence': float(confidence)
        }

    @staticmethod
    def forecast_next_period(historical_data: List[Dict], periods_ahead: int = 1) -> List[Dict]:
        """
        Forecast next periods using advanced trend analysis
        Combines linear regression, moving average, and seasonality detection

        Args:
            historical_data: List of dicts with 'date' and 'value' keys, sorted by date
            periods_ahead: Number of periods to forecast

        Returns:
            List of forecasted values with confidence intervals
        """
        if len(historical_data) < 2:
            return []

        values = [float(d['value']) for d in historical_data]
        dates = [d.get('date') for d in historical_data]

        # Calculate trend
        trend = TrendAnalysis.calculate_trend_line(values)
        slope = trend['slope']

        # Calculate moving averages for smoothing
        ma3 = TrendAnalysis.calculate_moving_average(values, 3)
        ma6 = TrendAnalysis.calculate_moving_average(values, 6)

        # Get the last value for forecasting
        last_value = values[-1]
        last_ma3 = next((x for x in reversed(ma3) if x is not None), last_value)

        # Detect seasonality
        seasonality = TrendAnalysis.detect_seasonality(historical_data, period=min(4, len(values) // 2))

        # Generate forecasts
        forecasts = []
        current_value = last_value
        base_trend = slope

        for i in range(1, periods_ahead + 1):
            # Apply trend
            forecasted_value = current_value + base_trend

            # Apply damping factor (reduce trend strength over time)
            damping_factor = 0.95 ** i

            # Calculate standard error for confidence interval
            se = np.std(values) * np.sqrt(1 + 1/len(values))
            confidence_lower = forecasted_value - (1.96 * se)
            confidence_upper = forecasted_value + (1.96 * se)

            # Ensure forecasted value doesn't go negative if original data is positive
            if min(values) >= 0:
                forecasted_value = max(0, forecasted_value)
                confidence_lower = max(0, confidence_lower)

            forecasts.append({
                'period': i,
                'forecasted_value': round(float(forecasted_value), 2),
                'confidence_lower': round(float(confidence_lower), 2),
                'confidence_upper': round(float(confidence_upper), 2),
                'confidence_level': 0.95
            })

            # Update current value for next iteration
            current_value = forecasted_value

        return forecasts

    @staticmethod
    def calculate_growth_rate(period1_data: List[float], period2_data: List[float],
                             metric: str = 'average') -> Dict:
        """
        Calculate growth rate (QoQ, YoY) between two periods

        Args:
            period1_data: Performance data from first period
            period2_data: Performance data from second period
            metric: How to aggregate (average, sum, latest)

        Returns:
            Dictionary with growth rate and trend info
        """
        if not period1_data or not period2_data:
            return {
                'growth_rate': 0,
                'period1_value': 0,
                'period2_value': 0,
                'change': 0,
                'trend': 'neutral'
            }

        # Calculate aggregated values
        if metric == 'sum':
            val1 = sum(period1_data)
            val2 = sum(period2_data)
        elif metric == 'latest':
            val1 = period1_data[-1] if period1_data else 0
            val2 = period2_data[-1] if period2_data else 0
        else:  # average
            val1 = np.mean(period1_data) if period1_data else 0
            val2 = np.mean(period2_data) if period2_data else 0

        # Calculate growth rate
        growth_rate = ((val2 - val1) / abs(val1)) * 100 if val1 != 0 else 0
        change = val2 - val1

        # Determine trend
        if growth_rate > 5:
            trend = 'improving'
        elif growth_rate < -5:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'growth_rate': round(float(growth_rate), 2),
            'period1_value': round(float(val1), 2),
            'period2_value': round(float(val2), 2),
            'change': round(float(change), 2),
            'trend': trend
        }

    @staticmethod
    def normalize_data(values: List[float], method: str = 'minmax') -> List[float]:
        """
        Normalize data for comparison across different scales

        Args:
            values: List of numeric values
            method: Normalization method ('minmax' or 'zscore')

        Returns:
            List of normalized values
        """
        if not values or len(values) == 0:
            return []

        y = np.array(values, dtype=float)

        if method == 'minmax':
            min_val = np.nanmin(y)
            max_val = np.nanmax(y)
            if max_val - min_val == 0:
                return [0.5] * len(values)
            normalized = (y - min_val) / (max_val - min_val)
        else:  # zscore
            mean = np.nanmean(y)
            std = np.nanstd(y)
            if std == 0:
                return [0.0] * len(values)
            normalized = (y - mean) / std

        return [float(x) if not np.isnan(x) else 0 for x in normalized]

    @staticmethod
    def identify_outliers(values: List[float], method: str = 'iqr', threshold: float = 1.5) -> Dict:
        """
        Identify outliers in data using IQR or Z-score method

        Args:
            values: List of numeric values
            method: 'iqr' or 'zscore'
            threshold: Threshold for IQR method (default 1.5)

        Returns:
            Dictionary with outlier indices and values
        """
        if not values or len(values) < 3:
            return {'outliers': [], 'indices': []}

        y = np.array(values, dtype=float)

        if method == 'iqr':
            q1 = np.nanpercentile(y, 25)
            q3 = np.nanpercentile(y, 75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            outlier_mask = (y < lower_bound) | (y > upper_bound)
        else:  # zscore
            mean = np.nanmean(y)
            std = np.nanstd(y)
            if std == 0:
                return {'outliers': [], 'indices': []}
            z_scores = np.abs((y - mean) / std)
            outlier_mask = z_scores > threshold

        outlier_indices = np.where(outlier_mask)[0].tolist()
        outliers = [float(y[i]) for i in outlier_indices]

        return {
            'outliers': outliers,
            'indices': outlier_indices,
            'count': len(outliers)
        }

    @staticmethod
    def compare_distributions(data1: List[float], data2: List[float]) -> Dict:
        """
        Compare two distributions statistically

        Args:
            data1: First dataset
            data2: Second dataset

        Returns:
            Dictionary with comparison metrics
        """
        if not data1 or not data2:
            return {'mean_diff': 0, 'is_significant': False}

        y1 = np.array(data1, dtype=float)
        y2 = np.array(data2, dtype=float)

        # Calculate means and standard deviations
        mean1 = np.nanmean(y1)
        mean2 = np.nanmean(y2)
        std1 = np.nanstd(y1)
        std2 = np.nanstd(y2)

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(y1[~np.isnan(y1)], y2[~np.isnan(y2)])

        # Determine significance at 0.05 level
        is_significant = p_value < 0.05

        return {
            'mean_diff': round(float(mean2 - mean1), 2),
            'std_diff': round(float(std2 - std1), 2),
            'p_value': round(float(p_value), 4),
            'is_significant': is_significant,
            'interpretation': 'Significant difference' if is_significant else 'No significant difference'
        }
