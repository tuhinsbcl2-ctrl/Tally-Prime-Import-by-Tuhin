"""Entry point for the Tally Prime Importer application.

Run with:
    python main.py
"""
import sys
import os

# Ensure the repo root is on the Python path
sys.path.insert(0, os.path.dirname(__file__))

from tally_importer.gui.app import App


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
