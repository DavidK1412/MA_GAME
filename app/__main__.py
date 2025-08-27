"""
Entry point for running the app module directly.
"""
from .main import app

if __name__ == "__main__":
    import hypercorn.asyncio
    import asyncio
    
    config = hypercorn.Config()
    config.bind = ["0.0.0.0:8000"]
    
    asyncio.run(hypercorn.asyncio.serve(app, config))
