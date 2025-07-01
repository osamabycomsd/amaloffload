import threading
import queue
import time
import json
from typing import Callable, Dict, List
import socket
from zeroconf import Zeroconf, ServiceBrowser, ServiceInfo
import logging
import requests  # ✅ تأكد من استيراده

logging.basicConfig(level=logging.INFO)

class PeerRegistry:
    def __init__(self):
        self._peers = {}
        self._zeroconf = Zeroconf()
        self.local_node_id = socket.gethostname()

    def register_service(self, name: str, port: int, load: float = 0.0):
        service_info = ServiceInfo(
            "_tasknode._tcp.local.",
            f"{name}._tasknode._tcp.local.",
            addresses=[socket.inet_aton(self._get_local_ip())],
            port=port,
            properties={
                b'load': str(load).encode(),   # تأكد من أنها bytes
                b'node_id': self.local_node_id.encode()
            },
            server=f"{name}.local."
        )
        self._zeroconf.register_service(service_info)
        logging.info(f"✅ Service registered: {name} @ {self._get_local_ip()}:{port}")

    def discover_peers(self, timeout: int = 3) -> List[Dict]:
        class Listener:
            def __init__(self):
                self.peers = []

            def add_service(self, zc, type_, name):
                info = zc.get_service_info(type_, name)
                if info:
                    ip = socket.inet_ntoa(info.addresses[0])
                    peer_data = {
                        'ip': ip,
                        'port': info.port,
                        'load': float(info.properties.get(b'load', b'0')),
                        'node_id': info.properties.get(b'node_id', b'unknown').decode(),
                        'last_seen': time.time()
                    }
                    if peer_data not in self.peers:
                        self.peers.append(peer_data)

            def update_service(self, zc, type_, name):
                self.add_service(zc, type_, name)

            def remove_service(self, zc, type_, name):
                pass  # اختياري

        listener = Listener()
        ServiceBrowser(self._zeroconf, "_tasknode._tcp.local.", listener)
        time.sleep(timeout)
        return sorted(listener.peers, key=lambda x: x['load'])

    def _get_local_ip(self) -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

class DistributedExecutor:
    def __init__(self, shared_secret: str):
        self.peer_registry = PeerRegistry()
        self.shared_secret = shared_secret
        self.task_queue = queue.PriorityQueue()
        self.result_cache = {}
        self.available_peers = []
        self._init_peer_discovery()

    def _init_peer_discovery(self):
        def discovery_loop():
            while True:
                self.available_peers = self.peer_registry.discover_peers()
                logging.info(f"✅ Discovered peers: {self.available_peers}")
                time.sleep(10)

        threading.Thread(target=discovery_loop, daemon=True).start()

    def submit(self, task_func: Callable, *args, **kwargs):
        """إرسال مهمة جديدة للنظام"""
        task_id = f"{task_func.__name__}_{time.time()}"

        task = {
            'task_id': task_id,
            'function': task_func.__name__,
            'args': args,
            'kwargs': kwargs,
            'sender_id': self.peer_registry.local_node_id
        }

        if self.available_peers:
            # ترتيب الأجهزة: LAN أولاً ثم WAN
            lan_peers = [p for p in self.available_peers if self._is_local_ip(p['ip'])]
            wan_peers = [p for p in self.available_peers if not self._is_local_ip(p['ip'])]
            
            # اختيار من LAN أولاً
            if lan_peers:
                peer = min(lan_peers, key=lambda x: x['load'])
                logging.info(f"✅ Sending task {task_id} to LAN peer {peer['node_id']}")
            else:
                # إذا لم تتوفر أجهزة محلية، استخدم WAN
                peer = min(wan_peers, key=lambda x: x['load'])
                logging.info(f"✅ Sending task {task_id} to WAN peer {peer['node_id']}")
            
            self._send_to_peer(peer, task)
        else:
            logging.warning("⚠️ لا توجد أجهزة متاحة - سيتم تنفيذ المهمة محلياً")

    def _is_local_ip(self, ip: str) -> bool:
        """فحص إذا كان IP في الشبكة المحلية"""
        return (
            ip.startswith('192.168.') or 
            ip.startswith('10.') or 
            ip.startswith('172.') or
            ip == '127.0.0.1'
        )

    def _send_to_peer(self, peer: Dict, task: Dict):
        try:
            url = f"http://{peer['ip']}:{peer['port']}/run"
            response = requests.post(url, json=task, timeout=10)
            response.raise_for_status()
            logging.info(f"✅ Response from peer: {response.text}")
            return response.json()
        except Exception as e:
            logging.error(f"❌ فشل إرسال المهمة لـ {peer['node_id']}: {e}")
            return None

if __name__ == "__main__":
    executor = DistributedExecutor("my_secret_key")
    executor.peer_registry.register_service("node1", 7520, load=0.1)
    print("✅ نظام توزيع المهام جاهز...")

    # مثال لإرسال مهمة:
    def example_task(x):
        return x * x

    executor.submit(example_task, 5)

