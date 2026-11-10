import sys, os, time
backend_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

def time_it(label, fn):
    t0 = time.time()
    print(f"[{label}] starting...", flush=True)
    fn()
    print(f"[{label}] done in {time.time()-t0:.2f}s", flush=True)

time_it("CustomerProfileAgent", lambda: __import__("app.agents.profile_agent"))
time_it("PolicyDocumentAgent", lambda: __import__("app.agents.policy_agent"))
time_it("RiskAssessmentAgent", lambda: __import__("app.agents.risk_agent"))
time_it("HistoricalClaimsAgent", lambda: __import__("app.agents.claims_agent"))
time_it("ExternalIntelligenceAgent", lambda: __import__("app.agents.external_agent"))
time_it("GovernanceTrustAgent", lambda: __import__("app.agents.governance_agent"))
time_it("LangGraph StateGraph", lambda: __import__("langgraph.graph"))
time_it("Graph module", lambda: __import__("app.orchestrator.graph"))
