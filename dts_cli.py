# dts_cli.py
import click
from dashboard import app
from rpc_server import app as rpc_app
import threading

@click.group()
def cli():
    pass

@cli.command()
def start():
    """بدء النظام الموزع"""
    print("جارِ تشغيل النظام الموزع...")
    
    # تشغيل واجهة التحكم في خيط منفصل
    dashboard_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5000)
    )
    dashboard_thread.daemon = True
    dashboard_thread.start()
    
    # تشغيل خادم RPC
    rpc_app.run(host="0.0.0.0", port=7520)

@cli.command()
def discover():
    """عرض الأجهزة المتصلة"""
    from peer_discovery import discover_peers
    peers = discover_peers()
    print("الأجهزة المتصلة:")
    for i, peer in enumerate(peers, 1):
        print(f"{i}. {peer}")

if __name__ == "__main__":
    cli()
