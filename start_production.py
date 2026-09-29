"""Production Dual-Service Launcher for PlanBridge AI.
Launches both FastAPI REST backend (port 8000) and Streamlit Operations UI (port 8501)
with concurrent logging and clean signal handling.
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent

def run_production():
    print("=" * 70)
    print("  🚀 Starting PlanBridge AI Production Platform (Oil India Limited)")
    print("=" * 70)
    print(f"  • Project Directory: {PROJECT_ROOT}")
    print(f"  • Python Interpreter: {sys.executable}")
    print("  • FastAPI REST Backend: http://0.0.0.0:8000 (Swagger: /docs)")
    print("  • Streamlit Operations UI: http://0.0.0.0:8501")
    print("=" * 70)

    # Environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    env["PYTHONUNBUFFERED"] = "1"

    # 1. Start FastAPI backend with Uvicorn
    api_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.api.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--workers",
        "1",
    ]

    # 2. Start Streamlit frontend
    ui_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(PROJECT_ROOT / "app" / "dashboard.py"),
        "--server.port",
        "8501",
        "--server.address",
        "0.0.0.0",
        "--server.headless",
        "true",
    ]

    procs = []
    try:
        print("[1/2] Launching FastAPI Backend...")
        p_api = subprocess.Popen(api_cmd, env=env)
        procs.append(p_api)
        time.sleep(1.5)

        print("[2/2] Launching Streamlit Frontend...")
        p_ui = subprocess.Popen(ui_cmd, env=env)
        procs.append(p_ui)

        print("\n✅ All PlanBridge AI services are running live!")
        print("   -> Open http://localhost:8501 in your web browser for the UI.")
        print("   -> Open http://localhost:8000/docs for the REST API Documentation.")
        print("   -> Press Ctrl+C to terminate all services.\n")

        # Keep alive and monitor child processes
        while True:
            for p in procs:
                if p.poll() is not None:
                    print(f"⚠️ Process {p.pid} terminated unexpectedly. Shutting down.")
                    return
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal. Terminating PlanBridge services...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("✅ All services terminated safely.")

if __name__ == "__main__":
    run_production()
