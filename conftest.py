import sys
from pathlib import Path

# Make the project root importable so tests can import generate, process_photo, etc.
sys.path.insert(0, str(Path(__file__).parent))
