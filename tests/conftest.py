"""Pytest configuration: make the app/ directory importable from tests/."""
import os
import sys

# Insert app/ at the front of sys.path so test modules can import app modules
# directly (e.g. `from rosary_state import ...`).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
