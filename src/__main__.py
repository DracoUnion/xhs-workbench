"""python -m src 入口（等价于 console script `xhs-workbench`）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import run

if __name__ == "__main__":
    run()