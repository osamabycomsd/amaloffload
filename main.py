# main.py – نسخة مُنقَّحة ومستقرة

"""
تشغيل خادم FastAPI + واجهة أوامر موزّعة.
- يعتمد على حزمة offload_core (tasks + peer_discovery + smart_tasks).
- يفعّل Zeroconf لاكتشاف العقد.
- يُشغّل ماسح الإنترنت وخوادم الخلفية.
- يوفّر قائمة CLI لاختبار المهام.
"""

import sys
import time
import json
import logging
import subprocess
import threading
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel
from offload_core.smart_tasks import (
    matrix_multiply,
    prime_calculation,
    data_processing,
)

# ---- مسارات المشروع ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))  # يضمن العثور على offload_core

# ---- حزمة المنطق ------------------------------------------------------------
from offload_core import tasks  # offload_core/tasks.py بعد النقل
from offload_core.smart_tasks import (
    matrix_multiply,
    prime_calculation,
    data_processing,
    # image_processing_emulation  # أضِفها إذا كانت موجودة
)
from distributed_executor import DistributedExecutor

# ---- إعداد FastAPI ----------------------------------------------------------
app = FastAPI(title="Offload Helper API")

class TaskRequest(BaseModel):
    func: str
    args: list | None = []
    kwargs: dict | None = {}
    complexity: int | float | None = None

@app.post("/run")
async def run_task(req: TaskRequest):
    """End‑point موحّد يستدعي dispatch في offload_core.tasks"""
    return tasks.dispatch(req)

# ---- إعدادات النظام ---------------------------------------------------------
CPU_PORT = 7520
PYTHON_EXE = sys.executable  # python أو python3 حسب البيئة

# ---- وظائف مساعدة -----------------------------------------------------------

def benchmark(fn, *args):
    start = time.time()
    res = fn(*args)
    return time.time() - start, res


def start_background():
    """تشغيل Peer Server وLoad Balancer في الخلفية"""
    subprocess.Popen([PYTHON_EXE, "peer_server.py"])
    subprocess.Popen([PYTHON_EXE, "load_balancer.py"])
    logging.info("✅ تم تشغيل الخدمات الخلفيّة (peer_server & load_balancer)")


def cli_menu(executor: DistributedExecutor):
    menu_tasks = {
        "1": ("ضرب المصفوفات", matrix_multiply, 500),
        "2": ("حساب الأعداد الأولية", prime_calculation, 100_000),
        "3": ("معالجة البيانات", data_processing, 10_000),
    }

    while True:
        print("\n🚀 نظام توزيع المهام الذكي")
        for k, v in menu_tasks.items():
            print(f"{k}: {v[0]}")
        choice = input("اختر المهمة (أو q للخروج): ").strip().lower()
        if choice == "q":
            break
        if choice not in menu_tasks:
            print("⚠️ اختيار غير صحيح!")
            continue

        name, fn, arg = menu_tasks[choice]
        print(f"\nتشغيل: {name} …")

        try:
            dur, res = benchmark(fn, arg)
            print(f"✅ النتيجة جاهزة. ⏱️ {dur:.3f} ث")
        except Exception as exc:
            print(f"❌ خطأ في تنفيذ المهمة: {exc}")

# ---- نقطة التشغيل -----------------------------------------------------------

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # تشغيل الخدمات الخلفية
    start_background()

    # تهيئة مُنفذ موزّع
    executor = DistributedExecutor("my_shared_secret_123")
    executor.peer_registry.register_service("node_main", CPU_PORT, load=0.2)
    logging.info("✅ النظام جاهز للعمل")

    # تشغيل خادم FastAPI في خيط منفصل
    import uvicorn
    threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=CPU_PORT, log_level="warning"),
        daemon=True,
    ).start()

    # واجهة CLI
    cli_menu(executor)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 إيقاف النظام…")

