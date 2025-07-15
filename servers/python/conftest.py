import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add src directory to Python path
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Set up environment for tests
os.environ["ENVIRONMENT"] = "test"
