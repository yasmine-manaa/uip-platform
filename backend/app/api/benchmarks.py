"""
API Endpoints: Scientific Validation Benchmarks (Section 13).
Compares Configuration A (Baseline), Configuration B (Single Agent),
Configuration C (Sequential), and Configuration D (Orchestrated Multi-Agent UIP).
"""

from fastapi import APIRouter
from app.evaluation.benchmark_runner import ScientificBenchmarkRunner

router = APIRouter(prefix="/benchmarks", tags=["Scientific Validation"])


@router.get("/scientific-validation")
def run_scientific_validation():
    """
    Executes benchmark comparison across Configurations A, B, C, D.
    Returns quantitative metrics: Poisson deviance, Citation grounding %,
    Contradiction detection rate %, Escalation accuracy %, Latency, and Auditability score.
    """
    return ScientificBenchmarkRunner.run_benchmark()
