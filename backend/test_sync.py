import time

print("Testing sync execution...", flush=True)
t0 = time.time()

def step1():
    return {"profile": "OK"}

def step2():
    return {"risk": 250.0}

res = {**step1(), **step2()}
print(f"Sync execution completed in {time.time()-t0:.4f}s! Result: {res}", flush=True)
