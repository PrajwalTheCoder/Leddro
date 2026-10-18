# backend/__init__.py
import sys
from pathlib import Path

# Ensure backend root and backend/app are in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
project_dir = backend_dir.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))
