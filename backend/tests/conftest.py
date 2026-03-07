"""
Pytest configuration for the optimizer test suite.

Sets up the Python path so tests can import from backend.app.*
without issues. No database fixtures needed — optimizer tests
work with plain dicts, not ORM objects.
"""

import sys
import os

# Ensure the repo root is in the Python path so imports like
# `from backend.app.optimizer.solver import solve_mip` work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))