import time
import psutil
import logging
from typing import Dict, Any
from datetime import datetime
import json
from pathlib import Path
import requests
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import threading

logger = logging.getLogger(__name__)

class MonitoringManager:
    def __init__(self, metrics_port: int = 9090):
        self.metrics_port = metrics_port
        self.start_time = time.time()
        
        # Initialize Prometheus metrics
        self.request_count = Counter('mcp_publish_requests_total', 'Total number of requests')
        self.error_count = Counter('mcp_publish_errors_total', 'Total number of errors')
        self.publish_latency = Histogram('mcp_publish_latency_seconds', 'Publishing latency in seconds')
        self.memory_usage = Gauge('mcp_publish_memory_bytes', 'Memory usage in bytes')
        self.cpu_usage = Gauge('mcp_publish_cpu_percent', 'CPU usage percentage')
        
        # Start metrics server
        self.start_metrics_server()

    def start_metrics_server(self):
        """Start the Prometheus metrics server."""
        try:
            start_http_server(self.metrics_port)
            logger.info(f"Metrics server started on port {self.metrics_port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {str(e)}")

    def update_system_metrics(self):
        """Update system metrics."""
        self.memory_usage.set(psutil.Process().memory_info().rss)
        self.cpu_usage.set(psutil.cpu_percent())

    def record_request(self, endpoint: str):
        """Record a request."""
        self.request_count.labels(endpoint=endpoint).inc()

    def record_error(self, endpoint: str, error_type: str):
        """Record an error."""
        self.error_count.labels(endpoint=endpoint, error_type=error_type).inc()

    def record_publish_latency(self, platform: str, duration: float):
        """Record publishing latency."""
        self.publish_latency.labels(platform=platform).observe(duration)

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the service."""
        try:
            uptime = time.time() - self.start_time
            memory = psutil.Process().memory_info().rss
            cpu = psutil.cpu_percent()
            
            return {
                'status': 'healthy',
                'uptime': uptime,
                'memory_usage': memory,
                'cpu_usage': cpu,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting health status: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def save_metrics(self, file_path: str):
        """Save metrics to a file."""
        try:
            metrics = {
                'request_count': self.request_count._value.get(),
                'error_count': self.error_count._value.get(),
                'memory_usage': self.memory_usage._value.get(),
                'cpu_usage': self.cpu_usage._value.get(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(metrics, f, indent=2)
                
            logger.info(f"Metrics saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")

    def start_metrics_collection(self, interval: int = 60):
        """Start periodic metrics collection."""
        def collect_metrics():
            while True:
                self.update_system_metrics()
                time.sleep(interval)

        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()
        logger.info(f"Started metrics collection with {interval}s interval") 