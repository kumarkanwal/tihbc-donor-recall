"""Run the complete deterministic demo seed with ``python -m app.seed``."""

import asyncio

from app.seed.full import main

if __name__ == "__main__":
    asyncio.run(main())
