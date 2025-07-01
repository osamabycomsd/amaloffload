# remote_executor.py (مُحدَّث: يدعم التشفير والتوقيع)
# ============================================================
# يرسل المهمّة إلى سيرفر RPC خارجي مع تشفير + توقيع، أو يعمل بوضع JSON صافٍ لو لم يكن SecurityManager مفعَّل.
# ============================================================

import requests
import json
import os
from typing import Any

# عنوان الخادم البعيد (يمكن تعيينه بمتغير بيئي)
REMOTE_SERVER = os.getenv("REMOTE_SERVER", "http://89.111.171.92:7520/run")

# محاولة استيراد SecurityManager (اختياري)
try:
    from security_layer import SecurityManager
    security = SecurityManager(os.getenv("SHARED_SECRET", "my_shared_secret_123"))
    SECURITY_ENABLED = True
except ImportError:
    security = None
    SECURITY_ENABLED = False


def execute_remotely(func_name: str, args: list[Any] | None = None, kwargs: dict[str, Any] | None = None):
    """إرسال استدعاء دالة إلى الخادم البعيد وإرجاع النتيجة."""

    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    task = {
        "func": func_name,
        "args": args,
        "kwargs": kwargs,
        "sender_id": "client_node"
    }

    try:
        if SECURITY_ENABLED:
            # 1) وقّع المهمة ثم شفّرها
            signed_task = security.sign_task(task)
            encrypted   = security.encrypt_data(json.dumps(signed_task).encode())

            headers = {
                "X-Signature": security.signature_hex,
                "Content-Type": "application/octet-stream"
            }
            payload = encrypted  # خام ثنائي
        else:
            # وضع التطوير: أرسل JSON صريح
            headers = {"Content-Type": "application/json"}
            payload = task

        response = requests.post(REMOTE_SERVER, headers=headers, json=payload if not SECURITY_ENABLED else None,
                                 data=payload if SECURITY_ENABLED else None,
                                 timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("result", "⚠️ لا يوجد نتيجة")

    except Exception as e:
        return f"❌ فشل التنفيذ البعيد: {e}"
