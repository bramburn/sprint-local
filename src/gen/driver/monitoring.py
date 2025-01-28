import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from .config import DriverConfig

class MetricsCollector:
    """
    Comprehensive metrics collection and monitoring system
    """
    def __init__(self, config: DriverConfig = None):
        self.config = config or DriverConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Metrics storage
        self.metrics: List[PerformanceMetric] = []
        
        # Performance tracking
        self.performance_thresholds = {
            'code_generation_time': 2.0,  # seconds
            'test_execution_time': 1.0,   # seconds
            'vector_store_latency': 0.5,  # seconds
        }

    def record_metric(
        self, 
        metric_name: str, 
        value: float, 
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a performance metric
        
        :param metric_name: Name of the metric
        :param value: Metric value
        :param tags: Additional metadata tags
        """
        try:
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                metric_name=metric_name,
                value=value,
                tags=tags or {}
            )
            
            self.metrics.append(metric)
            
            # Check performance thresholds
            self._check_performance_threshold(metric)
        
        except Exception as e:
            self.logger.error(f"Metric recording error: {e}")

    def _check_performance_threshold(self, metric: 'PerformanceMetric'):
        """
        Check if a metric exceeds performance thresholds
        
        :param metric: Performance metric to check
        """
        threshold = self.performance_thresholds.get(metric.metric_name)
        
        if threshold and metric.value > threshold:
            self.logger.warning(
                f"Performance threshold exceeded: "
                f"{metric.metric_name} = {metric.value} > {threshold}"
            )

    def get_metrics_summary(
        self, 
        metric_name: Optional[str] = None, 
        time_window: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate metrics summary
        
        :param metric_name: Optional specific metric to summarize
        :param time_window: Time window in seconds for summary
        :return: Metrics summary
        """
        try:
            now = datetime.now()
            filtered_metrics = [
                m for m in self.metrics
                if (not metric_name or m.metric_name == metric_name) and
                   (not time_window or (now - m.timestamp).total_seconds() <= time_window)
            ]
            
            summary = {
                'total_metrics': len(filtered_metrics),
                'metrics_by_name': {}
            }
            
            for metric in filtered_metrics:
                if metric.metric_name not in summary['metrics_by_name']:
                    summary['metrics_by_name'][metric.metric_name] = {
                        'values': [],
                        'tags': set()
                    }
                
                summary['metrics_by_name'][metric.metric_name]['values'].append(metric.value)
                summary['metrics_by_name'][metric.metric_name]['tags'].update(metric.tags.keys())
            
            # Calculate statistics
            for name, data in summary['metrics_by_name'].items():
                if data['values']:
                    data.update({
                        'min': min(data['values']),
                        'max': max(data['values']),
                        'avg': sum(data['values']) / len(data['values']),
                        'tags': list(data['tags'])
                    })
            
            return summary
        
        except Exception as e:
            self.logger.error(f"Metrics summary generation error: {e}")
            return {}

    def export_metrics(self, format: str = 'json') -> str:
        """
        Export metrics in specified format
        
        :param format: Export format (json, csv)
        :return: Exported metrics string
        """
        try:
            import json
            import csv
            from io import StringIO
            
            if format == 'json':
                return json.dumps([
                    {
                        'timestamp': m.timestamp.isoformat(),
                        'metric_name': m.metric_name,
                        'value': m.value,
                        'tags': m.tags
                    } for m in self.metrics
                ])
            
            elif format == 'csv':
                output = StringIO()
                writer = csv.writer(output)
                writer.writerow(['Timestamp', 'Metric Name', 'Value', 'Tags'])
                
                for m in self.metrics:
                    writer.writerow([
                        m.timestamp.isoformat(),
                        m.metric_name,
                        m.value,
                        str(m.tags)
                    ])
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
        
        except Exception as e:
            self.logger.error(f"Metrics export error: {e}")
            return ""

    def clear_metrics(self, older_than: Optional[datetime] = None):
        """
        Clear metrics, optionally filtering by timestamp
        
        :param older_than: Remove metrics older than this timestamp
        """
        if older_than:
            self.metrics = [m for m in self.metrics if m.timestamp >= older_than]
        else:
            self.metrics.clear()

    def __repr__(self):
        return f"<MetricsCollector metrics={len(self.metrics)}>"


class PerformanceMetric:
    """
    Represents a single performance metric
    """
    def __init__(
        self, 
        timestamp: datetime, 
        metric_name: str, 
        value: float, 
        tags: Dict[str, str]
    ):
        self.timestamp = timestamp
        self.metric_name = metric_name
        self.value = value
        self.tags = tags

    def __repr__(self):
        return (
            f"<PerformanceMetric "
            f"name={self.metric_name} "
            f"value={self.value} "
            f"timestamp={self.timestamp}>"
        )
