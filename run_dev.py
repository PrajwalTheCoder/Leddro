#!/usr/bin/env python3
"""
Leddro Unified Development Launcher (Phase 7.3)
Launches the FastAPI backend and Vite frontend together in a single terminal session.
Handles port conflicts, dependency checks, graceful shutdown, and prefixed log streaming.
"""

import sys
import os
import shutil
import socket
import signal
import subprocess
import threading
from pathlib import Path

# ANSI colors for readable log multiplexing
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Disable ANSI if terminal doesn't support it
if sys.platform == "win32" and not os.environ.get("WT_SESSION") and not os.environ.get("ANSICON"):
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        CYAN = GREEN = YELLOW = RED = BOLD = RESET = ""

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def stream_output(pipe, prefix: str, color: str):
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            print(f"{color}{BOLD}[{prefix}]{RESET} {line.rstrip()}", flush=True)
    except (ValueError, OSError):
        pass
    finally:
        pipe.close()

def main():
    root_dir = Path(__file__).resolve().parent
    os.chdir(root_dir)

    print(f"\n{BOLD}=== Leddro Development Workspace Launcher ==={RESET}\n")

    # 1. Environment file check
    env_file = root_dir / ".env"
    example_env = root_dir / ".env.example"
    if not env_file.exists():
        if example_env.exists():
            print(f"{YELLOW}[setup] .env not found. Initializing from .env.example (SQLite default)...{RESET}")
            shutil.copy(example_env, env_file)
        else:
            print(f"{RED}[error] Neither .env nor .env.example found in {root_dir}.{RESET}")
            sys.exit(1)

    # 2. Port conflict checks
    port_conflict = False
    if is_port_in_use(8000):
        print(f"{RED}[conflict] Port 8000 is already in use by another process.{RESET}")
        print(f"           The FastAPI backend cannot bind to port 8000.")
        print(f"           Please terminate the conflicting process or run backend separately.\n")
        port_conflict = True

    if is_port_in_use(5173):
        print(f"{YELLOW}[notice] Port 5173 is already in use.{RESET}")
        print(f"         Vite will attempt to automatically pick the next available port (e.g. 5174).\n")

    if port_conflict:
        sys.exit(1)

    # 3. Locate Python virtual environment
    if sys.platform == "win32":
        venv_python = root_dir / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = root_dir / ".venv" / "bin" / "python"

    if venv_python.exists():
        python_exe = str(venv_python)
    else:
        python_exe = sys.executable
        print(f"{YELLOW}[setup] Local .venv not found. Using system Python: {python_exe}{RESET}")

    # 4. Check frontend dependencies
    node_modules = root_dir / "node_modules"
    if not node_modules.exists():
        print(f"{RED}[error] node_modules directory not found.{RESET}")
        print(f"        Please run 'npm install' before launching the development server.")
        sys.exit(1)

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    # 5. Launch child processes
    backend_env = os.environ.copy()
    backend_env["PYTHONPATH"] = str(root_dir)

    print(f"{CYAN}[launcher] Starting FastAPI Backend on http://127.0.0.1:8000...{RESET}")
    backend_cmd = [python_exe, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    
    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=backend_env
        )
    except Exception as e:
        print(f"{RED}[error] Failed to start backend process: {e}{RESET}")
        sys.exit(1)

    print(f"{GREEN}[launcher] Starting Vite Frontend on http://localhost:5173...{RESET}")
    frontend_cmd = [npm_cmd, "run", "dev"]
    
    try:
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    except Exception as e:
        print(f"{RED}[error] Failed to start frontend process: {e}{RESET}")
        backend_proc.terminate()
        sys.exit(1)

    # 6. Stream logs
    t_backend = threading.Thread(target=stream_output, args=(backend_proc.stdout, "backend", CYAN), daemon=True)
    t_frontend = threading.Thread(target=stream_output, args=(frontend_proc.stdout, "frontend", GREEN), daemon=True)
    t_backend.start()
    t_frontend.start()

    print(f"\n{BOLD}{GREEN}[OK] Both services launched successfully!{RESET}")
    print(f"  * Frontend:  {BOLD}http://localhost:5173{RESET}")
    print(f"  * API Docs:  {BOLD}http://127.0.0.1:8000/docs{RESET}")
    print(f"  * Health:    {BOLD}http://127.0.0.1:8000/api/health{RESET}")
    print(f"{YELLOW}Press CTRL+C at any time to cleanly stop both services.{RESET}\n")

    def shutdown(signum=None, frame=None):
        print(f"\n{YELLOW}[launcher] Shutting down development processes...{RESET}")
        for proc, name in [(backend_proc, "backend"), (frontend_proc, "frontend")]:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            except Exception as e:
                print(f"{RED}[launcher] Error stopping {name}: {e}{RESET}")
        print(f"{GREEN}[launcher] All services stopped cleanly. Goodbye!{RESET}\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    # Monitor processes
    while True:
        try:
            b_code = backend_proc.poll()
            f_code = frontend_proc.poll()

            if b_code is not None:
                print(f"{RED}[error] Backend process exited unexpectedly with code {b_code}.{RESET}")
                shutdown()
            if f_code is not None:
                print(f"{RED}[error] Frontend process exited unexpectedly with code {f_code}.{RESET}")
                shutdown()

            threading.Event().wait(0.5)
        except KeyboardInterrupt:
            shutdown()

if __name__ == "__main__":
    main()
