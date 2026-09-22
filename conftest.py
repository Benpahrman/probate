import os
import sys

# Ensure repository root and backend are on sys.path for test discovery
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Set isolated test database for pytest runs
TEST_DB_PATH = os.path.join(BACKEND_DIR, "database", "test_backend.db")
os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
