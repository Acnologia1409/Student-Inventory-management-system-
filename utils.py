import math
import sys
from datetime import datetime

def log_operation(func):
    """Decorator to log operation details, function names, and arguments."""
    def wrapper(*args, **kwargs):
        # We can write to data/audit_log.txt as a side effect
        log_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Executing: {func.__name__} | Args: {args} {kwargs}"
        # Print logs to console in debug style
        print(f"\033[90mDEBUG: {log_msg}\033[0m")
        
        # Write to log file
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, "audit_log.txt")
        
        try:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(log_msg + "\n")
        except Exception as e:
            pass # Suppress logging errors to prevent crash
            
        return func(*args, **kwargs)
    return wrapper

# Import os inside utility file for path resolutions in decorator
import os

def calculate_compound_fine(days: int, daily_rate: float = 1.0, compounding_rate: float = 1.05) -> float:
    """Recursively calculates a compounding late fine for overdue items.
    
    Fine increases by 5% compounding daily:
    Day 1: daily_rate * 1.00
    Day 2: Day 1 + daily_rate * (1.05)
    Day 3: Day 2 + daily_rate * (1.05^2)
    """
    if days <= 0:
        return 0.0
    if days == 1:
        return daily_rate
    
    # Recursive step
    previous_fines = calculate_compound_fine(days - 1, daily_rate, compounding_rate)
    current_day_fine = daily_rate * math.pow(compounding_rate, days - 1)
    return previous_fines + current_day_fine


def parse_and_convert_asset_tag(asset_tag: str) -> dict:
    """Extracts numerical digits from asset tag and displays it in Binary, Octal, Hex."""
    # Strip any non-digit prefix, e.g., 'INV102' -> 102
    digits_str = "".join([char for char in asset_tag if char.isdigit()])
    if not digits_str:
        number = 0
    else:
        number = int(digits_str)

    # Convert to different number bases
    return {
        "decimal": number,
        "binary": bin(number),  # Binary representation (e.g. 0b1100110)
        "octal": oct(number),   # Octal representation (e.g. 0o146)
        "hex": hex(number)      # Hexadecimal representation (e.g. 0x66)
    }


def analyze_fines_and_risks(fine_amount: float) -> tuple:
    """Utilizes various functions from the math module to return metrics."""
    if fine_amount <= 0.0:
        return 0.0, "Zero Risk", 0
        
    # math.ceil to round fine up to nearest integer
    ceiled_fine = math.ceil(fine_amount)
    
    # math.log to assess risk logarithmically
    risk_metric = math.log1p(fine_amount)  # ln(1 + x)
    
    if risk_metric > 3.0:
        risk_level = "CRITICAL RISK - ACCOUNT SUSPENSION"
    elif risk_metric > 1.5:
        risk_level = "MEDIUM RISK - PAYMENT DUE"
    else:
        risk_level = "LOW RISK - WARNING ISSUED"
        
    return float(ceiled_fine), risk_level, round(risk_metric, 4)
