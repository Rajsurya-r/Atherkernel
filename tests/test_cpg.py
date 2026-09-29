import time
import pytest
from src.cpg_engine import AetherCPG
from src.agent_gatekeeper import AetherGatekeeper

SAMPLE_CODE = """
def authenticate_user(token: str) -> bool:
    return len(token) > 32

def route_request(endpoint: str, token: str) -> str:
    if authenticate_user(token):
        return f"OK: {endpoint}"
    return "UNAUTHORIZED"
"""

def test_cpg_ingestion_and_sub_5ms_latency(tmp_path):
    db_file = str(tmp_path / "test_kuzu")
    cpg = AetherCPG(db_file)
    cpg.ingest_code("auth_mod", "/sys/auth/tokens.py", SAMPLE_CODE)
    
    start_time = time.perf_counter()
    cag_prefix = cpg.extract_deterministic_cag_prefix("authenticate_user")
    traversal_time_ms = (time.perf_counter() - start_time) * 1000
    
    assert "authenticate_user" in cag_prefix
    assert traversal_time_ms < 5.0, f"CPG traversal exceeded SLA: {traversal_time_ms:.2f} ms"

def test_cag_prefix_lexicographical_invariance(tmp_path):
    db_file = str(tmp_path / "test_kuzu_inv")
    cpg = AetherCPG(db_file)
    cpg.ingest_code("auth_mod", "/sys/auth/tokens.py", SAMPLE_CODE)
    
    run_1 = cpg.extract_deterministic_cag_prefix("authenticate_user")
    run_2 = cpg.extract_deterministic_cag_prefix("authenticate_user")
    assert run_1 == run_2, "CAG prefix failed deterministic lexicographical invariance"

def test_gatekeeper_security_ast():
    gate = AetherGatekeeper()
    malicious_code = "import os\nos.system('rm -rf /')"
    valid, msg = gate.verify_security_ast(malicious_code)
    assert not valid
    assert "Security Violation" in msg

    safe_code = "def add(a, b):\n    return a + b"
    valid, msg = gate.verify_security_ast(safe_code)
    assert valid