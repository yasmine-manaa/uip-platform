import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

print("Python version:", sys.version, flush=True)

async def test():
    print("Asyncio execution successful with WindowsSelectorEventLoopPolicy!", flush=True)

if __name__ == "__main__":
    asyncio.run(test())
