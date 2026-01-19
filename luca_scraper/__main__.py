"""
Entry point for running luca_scraper as a module.
Usage: python -m luca_scraper [options]

This module delegates execution to scriptname.py which contains the actual scraper logic.
"""

import sys
import os
import runpy

# Add parent directory to path to ensure scriptname.py can be found
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Change to parent directory so scriptname.py can find its relative imports
os.chdir(parent_dir)

# Execute scriptname.py as if it were run directly with "python scriptname.py"
# This ensures the if __name__ == "__main__": block executes
scriptname_path = os.path.join(parent_dir, 'scriptname.py')
if os.path.exists(scriptname_path):
    runpy.run_path(scriptname_path, run_name='__main__')
else:
    print(f"ERROR: scriptname.py not found at {scriptname_path}")
    sys.exit(1)
