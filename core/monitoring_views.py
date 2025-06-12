"""
Monitoring views for real-time resource usage
"""

import psutil
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import os
from django.conf import settings

def system_status(request):
    """API endpoint for current system resource usage"""
    try:
        # Get current process info
        process = psutil.Process()
        
        # System-wide metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process-specific metrics
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent()
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total_mb': round(memory.total / 1024 / 1024, 2),
                    'available_mb': round(memory.available / 1024 / 1024, 2),
                    'used_mb': round(memory.used / 1024 / 1024, 2),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
                    'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                    'used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
                    'percent': round((disk.used / disk.total) * 100, 1)
                }
            },
            'process': {
                'pid': process.pid,
                'cpu_percent': process_cpu,
                'memory_mb': round(process_memory.rss / 1024 / 1024, 2),
                'memory_percent': round(process.memory_percent(), 2),
                'threads': process.num_threads(),
                'status': process.status()
            }
        }
        
        return JsonResponse(status)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=500)

def resource_usage_history(request):
    """API endpoint for historical resource usage from logs"""
    try:
        log_file = os.path.join(settings.BASE_DIR, 'resource_usage.log')
        
        if not os.path.exists(log_file):
            return JsonResponse({
                'message': 'No resource usage history available',
                'operations': []
            })
        
        operations = []
        with open(log_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        operations.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        
        # Sort by timestamp (most recent first)
        operations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limit to last 50 operations
        operations = operations[:50]
        
        return JsonResponse({
            'total_operations': len(operations),
            'operations': operations
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@csrf_exempt
def resource_alerts(request):
    """Check if resource usage is above thresholds"""
    try:
        # Get current usage
        process = psutil.Process()
        memory = psutil.virtual_memory()
        
        current_memory_mb = process.memory_info().rss / 1024 / 1024
        system_memory_percent = memory.percent
        
        alerts = []
        
        # Memory alerts
        if current_memory_mb > 400:
            alerts.append({
                'type': 'memory',
                'level': 'critical',
                'message': f'High memory usage: {current_memory_mb:.2f}MB',
                'recommendation': 'Consider scaling up or optimizing memory usage'
            })
        elif current_memory_mb > 200:
            alerts.append({
                'type': 'memory',
                'level': 'warning',
                'message': f'Moderate memory usage: {current_memory_mb:.2f}MB',
                'recommendation': 'Monitor memory usage closely'
            })
        
        # System memory alerts
        if system_memory_percent > 85:
            alerts.append({
                'type': 'system_memory',
                'level': 'critical',
                'message': f'System memory usage: {system_memory_percent:.1f}%',
                'recommendation': 'System may need more RAM'
            })
        
        return JsonResponse({
            'timestamp': datetime.now().isoformat(),
            'alerts': alerts,
            'current_usage': {
                'process_memory_mb': round(current_memory_mb, 2),
                'system_memory_percent': system_memory_percent
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500) 