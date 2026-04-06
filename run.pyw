"""Desktop entry point for the Tally Prime Importer.

Double-click this file on Windows to launch the application without a
CMD/console window.  Python must be associated with .pyw files (the
standard Python installer on Windows does this automatically).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

main()
