"""
Data Transformation Utilities for MySQL ETL
Provides helpers for data aggregation, calculation, and transformation
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json
from decimal import Decimal

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """Calculates performance metrics like OEE, availability, efficiency"""
    
    @staticmethod
    def calculate_oee(availability: float, performance: float, quality: float) -> float:
        """
        Calculate Overall Equipment Effectiveness (OEE)
        OEE = Availability × Performance × Quality
        
        Args:
            availability: Availability percentage (0-100)
            performance: Performance percentage (0-100)
            quality: Quality percentage (0-100)
        
        Returns:
            OEE percentage (0-100)
        """
        try:
            oee = (availability / 100) * (performance / 100) * (quality / 100) * 100
            return round(oee, 2)
        except Exception as e:
            logger.error(f"Error calculating OEE: {e}")
            return 0.0
    
    @staticmethod
    def calculate_availability(scheduled_time: float, downtime: float) -> float:
        """
        Calculate availability percentage
        Availability = (Scheduled Time - Downtime) / Scheduled Time × 100
        """
        try:
            if scheduled_time <= 0:
                return 0.0
            availability = ((scheduled_time - downtime) / scheduled_time) * 100
            return round(min(100, max(0, availability)), 2)
        except Exception as e:
            logger.error(f"Error calculating availability: {e}")
            return 0.0
    
    @staticmethod
    def calculate_mtbf(total_uptime: float, failure_count: int) -> float:
        """
        Calculate Mean Time Between Failures (MTBF)
        MTBF = Total Uptime / Number of Failures
        """
        try:
            if failure_count <= 0:
                return 0.0
            mtbf = total_uptime / failure_count
            return round(mtbf, 2)
        except Exception as e:
            logger.error(f"Error calculating MTBF: {e}")
            return 0.0
    
    @staticmethod
    def calculate_mttr(total_downtime: float, failure_count: int) -> float:
        """
        Calculate Mean Time To Repair (MTTR)
        MTTR = Total Downtime / Number of Failures
        """
        try:
            if failure_count <= 0:
                return 0.0
            mttr = (total_downtime / failure_count)
            return round(mttr, 2)
        except Exception as e:
            logger.error(f"Error calculating MTTR: {e}")
            return 0.0


class FinancialCalculator:
    """Calculates financial metrics like margins, variances, ratios"""
    
    @staticmethod
    def calculate_margin(revenue: Decimal, cost: Decimal) -> Tuple[Decimal, float]:
        """
        Calculate profit margin
        Returns: (margin_amount, margin_percent)
        """
        try:
            margin_amount = revenue - cost
            if revenue == 0:
                margin_percent = 0.0
            else:
                margin_percent = float((margin_amount / revenue * 100))
            return margin_amount, round(margin_percent, 2)
        except Exception as e:
            logger.error(f"Error calculating margin: {e}")
            return Decimal(0), 0.0
    
    @staticmethod
    def calculate_variance(actual: Decimal, standard: Decimal) -> Tuple[Decimal, float]:
        """
        Calculate variance (actual vs standard)
        Returns: (variance_amount, variance_percent)
        """
        try:
            variance_amount = actual - standard
            if standard == 0:
                variance_percent = 0.0
            else:
                variance_percent = float((variance_amount / standard * 100))
            return variance_amount, round(variance_percent, 2)
        except Exception as e:
            logger.error(f"Error calculating variance: {e}")
            return Decimal(0), 0.0
    
    @staticmethod
    def calculate_ratio(numerator: Decimal, denominator: Decimal, 
                       precision: int = 2) -> float:
        """Calculate ratio with specified precision"""
        try:
            if denominator == 0:
                return 0.0
            ratio = float(numerator / denominator)
            return round(ratio, precision)
        except Exception as e:
            logger.error(f"Error calculating ratio: {e}")
            return 0.0
    
    @staticmethod
    def calculate_dso(receivables: Decimal, daily_sales: Decimal) -> float:
        """
        Calculate Days Sales Outstanding (DSO)
        DSO = (Accounts Receivable / Daily Sales) × Number of Days
        """
        try:
            if daily_sales == 0:
                return 0.0
            dso = float((receivables / daily_sales) * 30)
            return round(dso, 2)
        except Exception as e:
            logger.error(f"Error calculating DSO: {e}")
            return 0.0
    
    @staticmethod
    def calculate_dpo(payables: Decimal, daily_cogs: Decimal) -> float:
        """
        Calculate Days Payable Outstanding (DPO)
        DPO = (Accounts Payable / Daily COGS) × Number of Days
        """
        try:
            if daily_cogs == 0:
                return 0.0
            dpo = float((payables / daily_cogs) * 30)
            return round(dpo, 2)
        except Exception as e:
            logger.error(f"Error calculating DPO: {e}")
            return 0.0


class QualityCalculator:
    """Calculates quality metrics like defect rates, CPK, PPK"""
    
    @staticmethod
    def calculate_defect_rate(defects: int, total: int) -> float:
        """Calculate defect rate percentage"""
        try:
            if total == 0:
                return 0.0
            rate = (defects / total) * 100
            return round(rate, 3)
        except Exception as e:
            logger.error(f"Error calculating defect rate: {e}")
            return 0.0
    
    @staticmethod
    def calculate_yield(good_units: int, total_units: int) -> float:
        """Calculate yield percentage (good units / total units)"""
        try:
            if total_units == 0:
                return 0.0
            yield_pct = (good_units / total_units) * 100
            return round(yield_pct, 2)
        except Exception as e:
            logger.error(f"Error calculating yield: {e}")
            return 0.0
    
    @staticmethod
    def calculate_cpk(mean: float, std_dev: float, usl: float, lsl: float) -> float:
        """
        Calculate Process Capability Index (Cpk)
        Cpk = min((USL - mean), (mean - LSL)) / (3 × σ)
        """
        try:
            if std_dev == 0:
                return 0.0
            cpu = (usl - mean) / (3 * std_dev)
            cpl = (mean - lsl) / (3 * std_dev)
            cpk = min(cpu, cpl)
            return round(max(0, cpk), 3)
        except Exception as e:
            logger.error(f"Error calculating CPK: {e}")
            return 0.0
    
    @staticmethod
    def calculate_ppk(mean: float, std_dev: float, usl: float, lsl: float) -> float:
        """
        Calculate Process Performance Index (Ppk)
        Similar to Cpk but uses overall standard deviation
        """
        try:
            if std_dev == 0:
                return 0.0
            ppu = (usl - mean) / (3 * std_dev)
            ppl = (mean - lsl) / (3 * std_dev)
            ppk = min(ppu, ppl)
            return round(max(0, ppk), 3)
        except Exception as e:
            logger.error(f"Error calculating PPK: {e}")
            return 0.0


class AggregationHelper:
    """Helpers for data aggregation from multiple sources"""
    
    @staticmethod
    def sum_safe(values: List[Optional[float]]) -> float:
        """Safely sum values, ignoring None"""
        try:
            valid_values = [v for v in values if v is not None]
            return sum(valid_values) if valid_values else 0.0
        except Exception as e:
            logger.error(f"Error summing values: {e}")
            return 0.0
    
    @staticmethod
    def avg_safe(values: List[Optional[float]]) -> float:
        """Safely calculate average, ignoring None"""
        try:
            valid_values = [v for v in values if v is not None]
            if not valid_values:
                return 0.0
            return round(sum(valid_values) / len(valid_values), 2)
        except Exception as e:
            logger.error(f"Error calculating average: {e}")
            return 0.0
    
    @staticmethod
    def weighted_avg(values: List[float], weights: List[float]) -> float:
        """Calculate weighted average"""
        try:
            if not values or not weights:
                return 0.0
            if len(values) != len(weights):
                raise ValueError("Values and weights must have same length")
            
            total_weight = sum(weights)
            if total_weight == 0:
                return 0.0
            
            weighted_sum = sum(v * w for v, w in zip(values, weights))
            return round(weighted_sum / total_weight, 2)
        except Exception as e:
            logger.error(f"Error calculating weighted average: {e}")
            return 0.0
    
    @staticmethod
    def percentile(values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        try:
            if not values:
                return 0.0
            
            sorted_values = sorted(values)
            index = (percentile / 100) * (len(sorted_values) - 1)
            
            lower_index = int(index)
            upper_index = lower_index + 1
            
            if upper_index >= len(sorted_values):
                return sorted_values[lower_index]
            
            # Linear interpolation
            lower_value = sorted_values[lower_index]
            upper_value = sorted_values[upper_index]
            
            fraction = index - lower_index
            result = lower_value + fraction * (upper_value - lower_value)
            
            return round(result, 2)
        except Exception as e:
            logger.error(f"Error calculating percentile: {e}")
            return 0.0


class DateHelper:
    """Helpers for date-based calculations"""
    
    @staticmethod
    def get_month_range(year: int, month: int) -> Tuple[datetime, datetime]:
        """Get start and end dates for a month"""
        from datetime import date
        
        start_date = date(year, month, 1)
        
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        return start_date, end_date
    
    @staticmethod
    def get_year_range(year: int) -> Tuple[datetime, datetime]:
        """Get start and end dates for a year"""
        from datetime import date
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        return start_date, end_date
    
    @staticmethod
    def get_week_range(year: int, week: int) -> Tuple[datetime, datetime]:
        """Get start and end dates for an ISO week"""
        from datetime import date
        start_date = datetime.strptime(f'{year}-W{week:02d}-1', '%Y-W%W-%w').date()
        end_date = start_date + timedelta(days=6)
        return start_date, end_date
    
    @staticmethod
    def format_month_key(year: int, month: int) -> str:
        """Format year-month as YYYY-MM"""
        return f"{year:04d}-{month:02d}"
    
    @staticmethod
    def parse_month_key(month_key: str) -> Tuple[int, int]:
        """Parse YYYY-MM format to (year, month)"""
        try:
            parts = month_key.split('-')
            return int(parts[0]), int(parts[1])
        except Exception as e:
            logger.error(f"Error parsing month key: {e}")
            return 0, 0


class ValidationHelper:
    """Helpers for data validation before loading"""
    
    @staticmethod
    def validate_decimal(value: any, min_val: Decimal = None, 
                        max_val: Decimal = None) -> Tuple[bool, Optional[Decimal]]:
        """Validate and convert to Decimal"""
        try:
            if value is None:
                return False, None
            
            decimal_val = Decimal(str(value))
            
            if min_val is not None and decimal_val < min_val:
                return False, None
            
            if max_val is not None and decimal_val > max_val:
                return False, None
            
            return True, decimal_val
        except Exception as e:
            logger.debug(f"Decimal validation failed for {value}: {e}")
            return False, None
    
    @staticmethod
    def validate_percentage(value: any) -> Tuple[bool, Optional[float]]:
        """Validate value is between 0 and 100"""
        try:
            if value is None:
                return False, None
            
            float_val = float(value)
            
            if not (0 <= float_val <= 100):
                return False, None
            
            return True, round(float_val, 2)
        except Exception as e:
            logger.debug(f"Percentage validation failed for {value}: {e}")
            return False, None
    
    @staticmethod
    def validate_integer(value: any, min_val: int = None, 
                        max_val: int = None) -> Tuple[bool, Optional[int]]:
        """Validate and convert to integer"""
        try:
            if value is None:
                return False, None
            
            int_val = int(value)
            
            if min_val is not None and int_val < min_val:
                return False, None
            
            if max_val is not None and int_val > max_val:
                return False, None
            
            return True, int_val
        except Exception as e:
            logger.debug(f"Integer validation failed for {value}: {e}")
            return False, None
    
    @staticmethod
    def validate_string(value: any, max_length: int = None) -> Tuple[bool, Optional[str]]:
        """Validate string value"""
        try:
            if value is None:
                return False, None
            
            str_val = str(value).strip()
            
            if not str_val:
                return False, None
            
            if max_length and len(str_val) > max_length:
                return False, None
            
            return True, str_val
        except Exception as e:
            logger.debug(f"String validation failed for {value}: {e}")
            return False, None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test calculations
    print("Testing Performance Calculator...")
    oee = PerformanceCalculator.calculate_oee(95, 98, 99)
    print(f"OEE (95%, 98%, 99%): {oee}%")
    
    print("\nTesting Financial Calculator...")
    margin, margin_pct = FinancialCalculator.calculate_margin(Decimal(1000), Decimal(600))
    print(f"Margin (1000, 600): ${margin} ({margin_pct}%)")
    
    print("\nTesting Quality Calculator...")
    defect_rate = QualityCalculator.calculate_defect_rate(5, 1000)
    print(f"Defect Rate (5/1000): {defect_rate}%")
    
    print("\nTesting Aggregation Helper...")
    avg = AggregationHelper.avg_safe([10, 20, 30, 40, None])
    print(f"Average [10,20,30,40,None]: {avg}")
