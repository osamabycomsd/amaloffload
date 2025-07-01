# processor_manager.py

import psutil
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)

class ResourceMonitor:
    def __init__(self):
        self.cpu_history = deque(maxlen=10)
        self.mem_history = deque(maxlen=10)

    def current_load(self):
        cpu = psutil.cpu_percent(interval=0.5) / 100.0  # كنسبة (0.0 - 1.0)
        mem = psutil.virtual_memory().available / (1024**2)  # MB

        self.cpu_history.append(cpu)
        self.mem_history.append(mem)

        avg_cpu = sum(self.cpu_history) / len(self.cpu_history)
        avg_mem = sum(self.mem_history) / len(self.mem_history)

        logging.info(f"Instant CPU: {cpu:.2%}, Instant MEM: {mem:.1f}MB")
        logging.info(f"Avg CPU: {avg_cpu:.2%}, Avg MEM: {avg_mem:.1f}MB")

        return {
            "instant": {"cpu": cpu, "mem": mem},
            "average": {"cpu": avg_cpu, "mem": avg_mem},
            "recommendation": "offload" if avg_cpu > 0.7 or avg_mem < 500 else "local"
        }

def trigger_offload():
    """عملية توزيع المهام التجريبية"""
    print("⚠️ تم استدعاء توزيع المهام (اختباري)")

def should_offload(task_complexity=0):
    monitor = ResourceMonitor()
    status = monitor.current_load()

    if (
        status['average']['cpu'] > 0.6 or
        task_complexity > 75
    ):
        return True
    return False

# مثال تشغيل فوري عند الاستيراد (غير مفضل عادة)
if __name__ == "__main__":
    cpu_load = psutil.cpu_percent(interval=1)
    mem_available = psutil.virtual_memory().available / (1024**2)

    if cpu_load > 50 or mem_available < 500:
        trigger_offload()

    if should_offload(80):
        print("💡 ينصح بتوزيع المهمة")
    else:
        print("✅ يمكن تنفيذ المهمة محلياً")

