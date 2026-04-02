"""
Monitoring module for Codemail system.
Provides health checks, metrics collection, and system status reporting.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from config import email_config, llm_config

logger = logging.getLogger("codmail.monitoring")


class SystemMonitor:
    """System health monitor for Codemail."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.task_counts = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "running": 0
        }
        
    def get_system_status(self) -> Dict:
        """
        Get comprehensive system status.
        
        Returns:
            Dictionary with system health information
        """
        try:
            # Import here to avoid circular dependencies
            from task_queue import create_task_queue
            
            queue = create_task_queue()
            
            # Get queue stats
            queue_stats = {}
            if hasattr(queue, 'get_queue_stats'):
                queue_stats = queue.get_queue_stats()
            
            # Calculate uptime
            uptime = datetime.now() - self.start_time
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": int(uptime.total_seconds()),
                "version": "1.0.0-alpha",
                "queue_stats": queue_stats,
                "components": {
                    "email_monitor": self._check_email_config(),
                    "llm_interface": self._check_llm_connection(),
                    "task_queue": self._check_task_queue()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _check_email_config(self) -> Dict:
        """Check email configuration status."""
        try:
            # Check if required environment variables are set
            has_credentials = bool(email_config.email_address and email_config.email_password)
            
            return {
                "status": "configured" if has_credentials else "missing_credentials",
                "imap_host": email_config.imap_host,
                "smtp_host": email_config.smtp_host,
                "email_set": has_credentials
            }
        except Exception as e:
            logger.error(f"Error checking email config: {e}")
            return {"status": "error", "error": str(e)}
    
    def _check_llm_connection(self) -> Dict:
        """Check LLM connection status."""
        try:
            from llm_interface import create_llm_interface
            
            llm = create_llm_interface()
            
            # Test connection
            is_connected = llm.check_connection()
            
            return {
                "status": "connected" if is_connected else "disconnected",
                "endpoint": llm_config.endpoint,
                "connection_test": "passed" if is_connected else "failed"
            }
        except Exception as e:
            logger.error(f"Error checking LLM connection: {e}")
            return {"status": "error", "error": str(e)}
    
    def _check_task_queue(self) -> Dict:
        """Check task queue status."""
        try:
            from task_queue import create_task_queue
            
            queue = create_task_queue()
            
            # Test database connection
            test_task_id = None
            try:
                test_task_id = queue.create_task(
                    project_name="health_check",
                    instructions="Health check task - delete after testing"
                )
                
                # Clean up
                if test_task_id:
                    queue.delete_task(test_task_id)
                    
                db_status = "connected"
            except Exception as e:
                logger.error(f"Error testing database connection: {e}")
                db_status = f"error: {str(e)}"
            
            return {
                "status": db_status,
                "type": "SQLite",
                "database_url": queue.database_url
            }
        except Exception as e:
            logger.error(f"Error checking task queue: {e}")
            return {"status": "error", "error": str(e)}
    
    def record_task_completion(self, status: str):
        """Record a task completion for metrics."""
        self.task_counts["total"] += 1
        
        if status == "completed":
            self.task_counts["completed"] += 1
        elif status == "failed":
            self.task_counts["failed"] += 1
        elif status == "running":
            self.task_counts["running"] += 1
    
    def get_metrics(self) -> Dict:
        """Get system metrics."""
        return {
            **self.task_counts,
            "success_rate": (
                self.task_counts["completed"] / self.task_counts["total"] * 100
                if self.task_counts["total"] > 0 else 0
            )
        }


def create_monitor() -> SystemMonitor:
    """Factory function to create system monitor."""
    return SystemMonitor()


class HealthCheckAPI:
    """Health check endpoints for monitoring systems."""
    
    def __init__(self):
        self.monitor = create_monitor()
        
    def get_health_status(self) -> Dict:
        """
        Get health status for external monitoring.
        
        Returns:
            Dictionary with health information
        """
        status = self.monitor.get_system_status()
        
        # Determine overall status
        if status["status"] == "healthy":
            all_components_ok = all(
                component.get("status") in ["connected", "configured"]
                for component in status.get("components", {}).values()
            )
            
            if not all_components_ok:
                status["status"] = "degraded"
        
        return status
    
    def get_ready_status(self) -> Dict:
        """
        Get readiness status (for Kubernetes-style readiness probes).
        
        Returns:
            Dictionary with readiness information
        """
        status = self.get_health_status()
        
        # Check if system is ready to accept tasks
        ready = (
            status["status"] in ["healthy", "degraded"] and
            status.get("components", {}).get("llm_interface", {}).get("status") != "error"
        )
        
        return {
            **status,
            "ready": ready
        }


def create_health_check_api() -> HealthCheckAPI:
    """Factory function to create health check API."""
    return HealthCheckAPI()
