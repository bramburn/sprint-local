import time
import functools
import logging
from typing import Callable, Any
import tracemalloc
import resource
import psutil
import os

logger = logging.getLogger('performance')

class PerformanceTracker:
    """
    Utility class for tracking performance metrics of agent operations.
    """
    
    @staticmethod
    def track_time(func: Callable) -> Callable:
        """
        Decorator to track execution time of a function.
        
        Args:
            func: Function to be tracked
        
        Returns:
            Wrapped function with timing metrics
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            tracemalloc.start()
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate metrics
                end_time = time.time()
                execution_time = end_time - start_time
                current, peak = tracemalloc.get_traced_memory()
                
                # Log performance metrics
                logger.info(
                    f"Function: {func.__name__}\n"
                    f"Execution Time: {execution_time:.4f} seconds\n"
                    f"Memory Usage: Current {current / 10**6}MB, Peak {peak / 10**6}MB"
                )
                
                return result
            
            except Exception as e:
                logger.error(
                    f"Error in {func.__name__}: {e}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                raise
            
            finally:
                tracemalloc.stop()
        
        return wrapper
    
    @staticmethod
    def log_token_usage(input_tokens: int, output_tokens: int):
        """
        Log token usage for LLM operations.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        total_tokens = input_tokens + output_tokens
        logger.info(
            f"Token Usage: "
            f"Input: {input_tokens}, "
            f"Output: {output_tokens}, "
            f"Total: {total_tokens}"
        )
    
    @staticmethod
    def circuit_breaker(max_failures: int = 3):
        """
        Implement a circuit breaker for agent operations.
        
        Args:
            max_failures: Maximum number of consecutive failures allowed
        
        Returns:
            Decorator for circuit breaking
        """
        def decorator(func):
            failures = 0
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                nonlocal failures
                
                try:
                    result = func(*args, **kwargs)
                    failures = 0  # Reset on success
                    return result
                
                except Exception as e:
                    failures += 1
                    
                    if failures >= max_failures:
                        logger.error(
                            f"Circuit breaker triggered for {func.__name__}. "
                            f"Too many consecutive failures: {failures}"
                        )
                        raise RuntimeError(
                            f"Exceeded maximum failure threshold of {max_failures}"
                        )
                    
                    logger.warning(
                        f"Failure in {func.__name__}. "
                        f"Attempt {failures}/{max_failures}: {e}"
                    )
                    raise
            
            return wrapper
        
        return decorator

class PerformanceMetrics:
    """
    Comprehensive performance tracking utility for agent operations.
    """
    
    @staticmethod
    def track_performance(func: Callable) -> Callable:
        """
        Decorator to track performance metrics for function calls.
        
        Tracks:
        - Execution time
        - Memory usage
        - CPU usage
        - Number of calls
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Start tracking
            start_time = time.time()
            start_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)  # MB
            start_cpu = psutil.cpu_percent()
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate metrics
                end_time = time.time()
                end_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)  # MB
                end_cpu = psutil.cpu_percent()
                
                # Log performance metrics
                logger.info(
                    f"Performance Metrics for {func.__name__}:\n"
                    f"  Execution Time: {(end_time - start_time) * 1000:.2f} ms\n"
                    f"  Memory Usage: {end_memory - start_memory:.2f} MB\n"
                    f"  CPU Usage: {end_cpu - start_cpu:.2f}%"
                )
                
                return result
            
            except Exception as e:
                logger.error(f"Performance tracking error in {func.__name__}: {e}")
                raise
        
        return wrapper

    @staticmethod
    def log_system_resources():
        """
        Log current system resource utilization.
        """
        memory = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent(interval=1)
        
        logger.info(
            "System Resource Snapshot:\n"
            f"  Total Memory: {memory.total / (1024 * 1024 * 1024):.2f} GB\n"
            f"  Available Memory: {memory.available / (1024 * 1024 * 1024):.2f} GB\n"
            f"  Memory Usage: {memory.percent}%\n"
            f"  CPU Usage: {cpu_usage}%"
        )

# Alias for easier import
track_performance = PerformanceMetrics.track_performance
