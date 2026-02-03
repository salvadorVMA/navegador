"""
Monitoring and diagnostic tool for the variable search process in the dashboard.

This module helps diagnose timeout issues by providing real-time monitoring
of the variable search process and detailed diagnostic information.
"""

import os
import sys
import time
import re
import traceback
from datetime import datetime
import json
import threading
from typing import Dict, Any, Optional, List

# Add monitoring to a running dashboard instance
class VariableSearchMonitor:
    """
    Monitors the variable search process and provides diagnostic information.
    """
    
    def __init__(self):
        self.start_time = None
        self.step_times = []
        self.current_step = "not_started"
        self.errors = []
        self.results = []
        self.completed = False
    
    def start_monitoring(self):
        """Start monitoring a new variable search process"""
        self.start_time = time.time()
        self.step_times = []
        self.current_step = "starting"
        self.errors = []
        self.results = []
        self.completed = False
        
        print(f"🔍 Variable search monitoring started at {datetime.now().isoformat()}")
        return self
    
    def log_step(self, step_name: str, data: Optional[Dict[str, Any]] = None):
        """Log a step in the variable search process"""
        now = time.time()
        elapsed = now - self.start_time if self.start_time else 0
        
        step_data = {
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "elapsed": elapsed,
            "data": data or {}
        }
        
        self.step_times.append(step_data)
        self.current_step = step_name
        
        print(f"📊 Variable search step: {step_name} (elapsed: {elapsed:.2f}s)")
        return self
    
    def log_error(self, error_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Log an error in the variable search process"""
        now = time.time()
        elapsed = now - self.start_time if self.start_time else 0
        
        error_data = {
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "elapsed": elapsed,
            "details": details or {}
        }
        
        self.errors.append(error_data)
        print(f"❌ Variable search error: {error_type} - {message} (elapsed: {elapsed:.2f}s)")
        return self
    
    def complete(self, success: bool, results: Optional[Dict[str, Any]] = None):
        """Mark the monitoring as complete"""
        now = time.time()
        elapsed = now - self.start_time if self.start_time else 0
        
        self.completed = True
        self.results = results or {}
        
        status = "✅ successful" if success else "❌ failed"
        print(f"🏁 Variable search {status} after {elapsed:.2f}s")
        
        if results:
            # Only print a summary of the results to avoid overwhelming the console
            if isinstance(results, dict) and "selected_variables" in results:
                var_count = len(results["selected_variables"]) if results["selected_variables"] else 0
                print(f"📊 Found {var_count} variables")
                
                if var_count > 0 and isinstance(results["selected_variables"], list):
                    sample = results["selected_variables"][:5]
                    print(f"📋 Sample variables: {', '.join(sample)}")
        
        return self
    
    def get_report(self) -> Dict[str, Any]:
        """Generate a detailed report of the monitoring results"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        return {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            "elapsed_seconds": elapsed,
            "completed": self.completed,
            "current_step": self.current_step,
            "steps": self.step_times,
            "errors": self.errors,
            "results": self.results,
            "success": self.completed and not self.errors
        }
    
    def save_report(self, filename: Optional[str] = None) -> str:
        """Save the monitoring report to a file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"variable_search_report_{timestamp}.json"
        
        report = self.get_report()
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Saved variable search report to {filename}")
        return filename

# Global monitor instance that can be imported and used throughout the application
monitor = VariableSearchMonitor()

# Decorator to monitor a variable search function
def monitor_variable_search(func):
    """Decorator to monitor a variable search function"""
    def wrapper(*args, **kwargs):
        global monitor
        monitor.start_monitoring()
        
        monitor.log_step("function_start", {
            "function": func.__name__,
            "args_count": len(args),
            "kwargs": list(kwargs.keys())
        })
        
        try:
            result = func(*args, **kwargs)
            success = True
            
            # Check for common result structures
            if isinstance(result, dict) and "success" in result:
                success = result["success"]
            
            monitor.complete(success, results=result)
            return result
            
        except Exception as e:
            monitor.log_error("exception", str(e), {"traceback": traceback.format_exc()})
            monitor.complete(False)
            raise
    
    return wrapper

# Function to diagnose existing timeout issues
def diagnose_variable_search_timeouts(dashboard_path: str) -> Dict[str, Any]:
    """
    Analyze the dashboard code to diagnose timeout-related issues
    
    Args:
        dashboard_path: Path to the dashboard.py file
        
    Returns:
        Dict with diagnostic information
    """
    findings = {
        "timeout_values": [],
        "potential_issues": [],
        "recommendations": []
    }
    
    try:
        with open(dashboard_path, "r") as f:
            content = f.read()
        
        # Find all timeout values
        timeout_matches = re.findall(r"timeout=(\d+)", content)
        findings["timeout_values"] = [int(t) for t in timeout_matches]
        
        # Check for low timeouts
        low_timeouts = [t for t in findings["timeout_values"] if t < 15]
        if low_timeouts:
            findings["potential_issues"].append(
                f"Found {len(low_timeouts)} potentially low timeout values: {low_timeouts}"
            )
            findings["recommendations"].append(
                "Consider increasing timeouts to at least 15-30 seconds for complex operations"
            )
        
        # Check for error handling around timeout exceptions
        timeout_exception_count = content.count("TimeoutError")
        timeout_handling_patterns = [
            "except concurrent.futures.TimeoutError",
            "except TimeoutError"
        ]
        
        timeout_handlers = sum(content.count(pattern) for pattern in timeout_handling_patterns)
        
        if timeout_exception_count > timeout_handlers:
            findings["potential_issues"].append(
                f"Found {timeout_exception_count} timeout references but only {timeout_handlers} handlers"
            )
            findings["recommendations"].append(
                "Ensure all potential timeout exceptions are properly caught and handled"
            )
        
        # Check for auto-next-step configuration
        interval_match = re.search(r"dcc\.Interval\(id=\"auto-next-step-interval\", interval=(\d+), n_intervals=0, disabled=True, max_intervals=(\d+)\)", content)
        if interval_match:
            interval_ms = int(interval_match.group(1))
            max_intervals = int(interval_match.group(2))
            
            if interval_ms < 1000:
                findings["potential_issues"].append(
                    f"Auto-next-step interval is very short ({interval_ms}ms)"
                )
                findings["recommendations"].append(
                    "Consider increasing auto-next-step interval to at least 2000ms"
                )
                
            if max_intervals < 5:
                findings["potential_issues"].append(
                    f"Max intervals ({max_intervals}) might be too low for complex variable searches"
                )
                findings["recommendations"].append(
                    "Consider increasing max_intervals to 10 or higher for complex searches"
                )
        
        # Overall assessment
        if findings["potential_issues"]:
            findings["summary"] = f"Found {len(findings['potential_issues'])} potential timeout-related issues"
        else:
            findings["summary"] = "No obvious timeout-related issues found"
            
    except Exception as e:
        findings["error"] = str(e)
        findings["summary"] = "Error occurred during diagnosis"
    
    return findings

if __name__ == "__main__":
    # If run directly, diagnose the dashboard
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
    
    if os.path.exists(dashboard_path):
        print(f"📊 Diagnosing variable search timeouts in {dashboard_path}")
        findings = diagnose_variable_search_timeouts(dashboard_path)
        
        print(f"\n📋 Timeout Diagnosis Summary: {findings['summary']}")
        
        if "potential_issues" in findings and findings["potential_issues"]:
            print("\n⚠️ Potential Issues:")
            for issue in findings["potential_issues"]:
                print(f"  - {issue}")
        
        if "recommendations" in findings and findings["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in findings["recommendations"]:
                print(f"  - {rec}")
    else:
        print(f"❌ Dashboard file not found at {dashboard_path}")
