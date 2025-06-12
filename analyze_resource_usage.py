#!/usr/bin/env python3
"""
Resource Usage Analyzer for Stock Scraper
Analyzes resource_usage.log to provide insights about scraping operations
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import statistics

def analyze_resource_usage(log_file_path='resource_usage.log'):
    """Analyze resource usage patterns from log file"""
    
    if not os.path.exists(log_file_path):
        print(f"❌ Log file not found: {log_file_path}")
        print("💡 Run some scraping operations first to generate usage data")
        return
    
    operations = []
    
    # Read and parse log file
    try:
        with open(log_file_path, 'r') as f:
            for line in f:
                if line.strip():
                    operations.append(json.loads(line.strip()))
    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        return
    
    if not operations:
        print("📋 No operations found in log file")
        return
    
    print(f"📊 RESOURCE USAGE ANALYSIS ({len(operations)} operations)")
    print("=" * 60)
    
    # Group by operation type
    by_operation = defaultdict(list)
    for op in operations:
        operation_type = op['operation'].split('_')[1] if '_' in op['operation'] else op['operation']
        by_operation[operation_type].append(op)
    
    # Overall statistics
    all_memory = [op['peak_memory_mb'] for op in operations]
    all_cpu = [op['peak_cpu_percent'] for op in operations]
    all_duration = [op['duration_seconds'] for op in operations]
    
    print(f"\n🔍 OVERALL STATISTICS:")
    print(f"   Total Operations: {len(operations)}")
    print(f"   Memory Usage (MB):")
    print(f"     • Average: {statistics.mean(all_memory):.2f}")
    print(f"     • Peak: {max(all_memory):.2f}")
    print(f"     • Minimum: {min(all_memory):.2f}")
    print(f"   CPU Usage (%):")
    print(f"     • Average: {statistics.mean(all_cpu):.1f}")
    print(f"     • Peak: {max(all_cpu):.1f}")
    print(f"   Duration (seconds):")
    print(f"     • Average: {statistics.mean(all_duration):.2f}")
    print(f"     • Longest: {max(all_duration):.2f}")
    
    # Per operation type analysis
    print(f"\n📈 BY OPERATION TYPE:")
    for op_type, ops in by_operation.items():
        if len(ops) > 0:
            memory_vals = [op['peak_memory_mb'] for op in ops]
            cpu_vals = [op['peak_cpu_percent'] for op in ops]
            duration_vals = [op['duration_seconds'] for op in ops]
            
            print(f"\n   {op_type.upper()} ({len(ops)} operations):")
            print(f"     Memory (MB): Avg {statistics.mean(memory_vals):.2f}, Peak {max(memory_vals):.2f}")
            print(f"     CPU (%): Avg {statistics.mean(cpu_vals):.1f}, Peak {max(cpu_vals):.1f}")
            print(f"     Duration (s): Avg {statistics.mean(duration_vals):.2f}")
    
    # Recent operations
    print(f"\n🕐 RECENT OPERATIONS (Last 5):")
    recent_ops = sorted(operations, key=lambda x: x['timestamp'])[-5:]
    for op in recent_ops:
        dt = datetime.fromisoformat(op['timestamp'].replace('Z', '+00:00'))
        print(f"   {dt.strftime('%H:%M:%S')} | {op['operation']} | "
              f"Memory: {op['peak_memory_mb']:.2f}MB | "
              f"CPU: {op['peak_cpu_percent']:.1f}% | "
              f"Duration: {op['duration_seconds']:.2f}s")
    
    # Recommendations
    print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
    
    avg_memory = statistics.mean(all_memory)
    if avg_memory > 400:
        print("   🔴 HIGH MEMORY USAGE: Consider optimizing Selenium/browser settings")
        print("      • Use headless browser mode")
        print("      • Limit concurrent operations")
        print("      • Implement memory cleanup between operations")
    elif avg_memory > 200:
        print("   🟡 MODERATE MEMORY USAGE: Monitor and consider optimizations")
    else:
        print("   🟢 MEMORY USAGE LOOKS GOOD")
    
    avg_cpu = statistics.mean(all_cpu)
    if avg_cpu > 50:
        print("   🔴 HIGH CPU USAGE: Consider reducing processing intensity")
    elif avg_cpu > 25:
        print("   🟡 MODERATE CPU USAGE: Monitor performance")
    else:
        print("   🟢 CPU USAGE LOOKS EFFICIENT")
    
    # Server recommendations
    print(f"\n🖥️ SERVER RESOURCE RECOMMENDATIONS:")
    max_memory = max(all_memory)
    
    if max_memory <= 256:
        print("   📱 512MB RAM server should be sufficient")
    elif max_memory <= 512:
        print("   📱 1GB RAM server recommended")
    elif max_memory <= 1024:
        print("   💻 2GB RAM server recommended")
    else:
        print("   💻 4GB+ RAM server may be needed")
        print(f"      Peak usage: {max_memory:.2f}MB")

def main():
    """Main function"""
    print("🚀 Stock Scraper Resource Usage Analyzer")
    print("=" * 50)
    
    # Look for log file in current directory and common locations
    possible_paths = [
        'resource_usage.log',
        'core/resource_usage.log',
        '../resource_usage.log'
    ]
    
    log_path = None
    for path in possible_paths:
        if os.path.exists(path):
            log_path = path
            break
    
    if log_path:
        analyze_resource_usage(log_path)
    else:
        print("❌ No resource usage log file found")
        print("💡 Expected locations:")
        for path in possible_paths:
            print(f"   • {path}")
        print("\n🔧 To generate logs:")
        print("   1. Run your scraping operations")
        print("   2. The monitoring decorator will create resource_usage.log")
        print("   3. Run this script again")

if __name__ == "__main__":
    main() 