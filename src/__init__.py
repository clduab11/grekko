# Grekko Trading Platform
__version__ = "0.3.0"
__author__ = "Grekko Team"

# Make src a proper package
import sys
from pathlib import Path

# Add src to Python path for proper imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))