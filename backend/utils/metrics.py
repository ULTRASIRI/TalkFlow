"""
Metrics Collection
Tracks and reports performance metrics
"""
import time
from collections import deque
from typing import Dict, List, Optional
import statistics

from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class MetricsCollector:
    """
    Collects and analyzes performance metrics
    Maintains rolling windows for latency tracking
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize metrics collector
        
        Args:
            window_size: Number of samples to keep for rolling statistics
        """
        self.window_size = window_size
        self.metrics: Dict[str, deque] = {}
        self.counters: Dict[str, int] = {}
        self.start_time = time.time()
        
        logger.info(f"Metrics collector initialized (window_size={window_size})")
    
    def record(self, metric_name: str, value: float):
        """
        Record a metric value
        
        Args:
            metric_name: Name of the metric
            value: Metric value
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = deque(maxlen=self.window_size)
        
        self.metrics[metric_name].append(value)
    
    def increment(self, counter_name: str, amount: int = 1):
        """
        Increment a counter
        
        Args:
            counter_name: Name of the counter
            amount: Amount to increment
        """
        if counter_name not in self.counters:
            self.counters[counter_name] = 0
        
        self.counters[counter_name] += amount
    
    def get_stats(self, metric_name: str) -> Optional[Dict[str, float]]:
        """
        Get statistics for a metric
        
        Args:
            metric_name: Name of the metric
        
        Returns:
            Dictionary with statistics or None
        """
        if metric_name not in self.metrics or len(self.metrics[metric_name]) == 0:
            return None
        
        values = list(self.metrics[metric_name])
        
        return {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'stdev': statistics.stdev(values) if len(values) > 1 else 0.0,
            'count': len(values),
            'p95': self._percentile(values, 0.95),
            'p99': self._percentile(values, 0.99)
        }
    
    def _percentile(self, values: List[float], p: float) -> float:
        """
        Calculate percentile
        
        Args:
            values: List of values
            p: Percentile (0-1)
        
        Returns:
            Percentile value
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]
    
    def get_summary(self) -> Dict:
        """
        Get summary of all metrics
        
        Returns:
            Dictionary with all metric summaries
        """
        summary = {
            'uptime_seconds': time.time() - self.start_time,
            'metrics': {},
            'counters': self.counters.copy()
        }
        
        for metric_name in self.metrics:
            stats = self.get_stats(metric_name)
            if stats:
                summary['metrics'][metric_name] = stats
        
        return summary
    
    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.counters.clear()
        self.start_time = time.time()
        logger.info("Metrics reset")
    
    def get_recent(self, metric_name: str, n: int = 10) -> List[float]:
        """
        Get recent values for a metric
        
        Args:
            metric_name: Name of the metric
            n: Number of recent values
        
        Returns:
            List of recent values
        """
        if metric_name not in self.metrics:
            return []
        
        values = list(self.metrics[metric_name])
        return values[-n:]
    
    def log_summary(self):
        """Log summary of metrics"""
        summary = self.get_summary()
        
        logger.info("=== Metrics Summary ===")
        logger.info(f"Uptime: {summary['uptime_seconds']:.1f}s")
        
        if summary['counters']:
            logger.info("Counters:")
            for name, value in summary['counters'].items():
                logger.info(f"  {name}: {value}")
        
        if summary['metrics']:
            logger.info("Metrics:")
            for name, stats in summary['metrics'].items():
                logger.info(
                    f"  {name}: "
                    f"mean={stats['mean']:.1f}, "
                    f"median={stats['median']:.1f}, "
                    f"p95={stats['p95']:.1f}, "
                    f"count={stats['count']}"
                )


class LatencyTracker:
    """
    Context manager for tracking latency
    """
    
    def __init__(self, metrics_collector: MetricsCollector, metric_name: str):
        """
        Initialize latency tracker
        
        Args:
            metrics_collector: Metrics collector instance
            metric_name: Name of the metric to record
        """
        self.metrics_collector = metrics_collector
        self.metric_name = metric_name
        self.start_time = None
    
    def __enter__(self):
        """Start timing"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record"""
        if self.start_time:
            latency_ms = (time.time() - self.start_time) * 1000
            self.metrics_collector.record(self.metric_name, latency_ms)


class ThroughputTracker:
    """
    Tracks throughput (items per second)
    """
    
    def __init__(self, window_seconds: int = 60):
        """
        Initialize throughput tracker
        
        Args:
            window_seconds: Window size in seconds
        """
        self.window_seconds = window_seconds
        self.timestamps = deque()
    
    def record_event(self):
        """Record an event"""
        now = time.time()
        self.timestamps.append(now)
        
        # Remove old events
        cutoff = now - self.window_seconds
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()
    
    def get_rate(self) -> float:
        """
        Get current throughput rate
        
        Returns:
            Events per second
        """
        if len(self.timestamps) < 2:
            return 0.0
        
        duration = time.time() - self.timestamps[0]
        
        if duration > 0:
            return len(self.timestamps) / duration
        
        return 0.0
    
    def reset(self):
        """Reset tracker"""
        self.timestamps.clear()
