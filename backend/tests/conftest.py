"""
Pytest configuration for the optimizer test suite.

Sets up the Python path so tests can import from backend.app.*
without issues. Also ensures database tables exist before tests run.
"""

import sys
import os

# Ensure the repo root is in the Python path so imports like
# `from backend.app.optimizer.solver import solve_mip` work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Ensure DB tables exist before any test that touches the database
from backend.app.db.session import engine
from backend.app.db.base import Base
Base.metadata.create_all(bind=engine)