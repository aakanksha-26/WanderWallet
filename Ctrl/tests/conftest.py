import sys
from pathlib import Path

# Add backend/src to sys.path so tests can import app, db, etc.
BACKEND_SRC = str(Path(__file__).resolve().parent.parent / "backend" / "src")
if BACKEND_SRC not in sys.path:
    sys.path.insert(0, BACKEND_SRC)
