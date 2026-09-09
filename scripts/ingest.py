import os
import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import asyncio
from app.knowledge.ingest import main

if __name__ == "__main__":
    asyncio.run(main())

