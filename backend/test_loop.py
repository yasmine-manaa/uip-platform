import asyncio
import sys

print("Python version:", sys.version, flush=True)

async def test():
    print("Async function body reached!", flush=True)
    return 42

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    res = loop.run_until_complete(test())
    print("Result:", res, flush=True)
finally:
    loop.close()
    print("Loop closed successfully!", flush=True)
