"""
AetherKernel: Benchmark Evaluation Harness
Measures Time-To-First-Token (TTFT), KV hit rates, and AST compilation accuracy.
"""
from src.agent_gatekeeper import AetherGatekeeper

EVAL_TASKS = [
    {
        "context": "class DataParser:\n    def validate(self, raw: str) -> bool: pass",
        "prefix": "class JsonParser(DataParser):\n    def validate(self, raw: str) -> bool:\n",
        "suffix": "\n        return True"
    },
    {
        "context": "def hash_secret(secret: str) -> str: pass",
        "prefix": "def verify_secret(secret: str, target: str) -> bool:\n",
        "suffix": "\n    return res == target"
    }
]

def run_evaluation_suite():
    gate = AetherGatekeeper()
    total_samples = len(EVAL_TASKS)
    syntax_passes = 0
    total_latency = 0.0

    print(f"[BENCHMARK] Executing {total_samples} Fill-in-the-Middle evaluation runs...")
    for idx, task in enumerate(EVAL_TASKS, start=1):
        res = gate.execute_governance_pipeline(task["context"], task["prefix"], task["suffix"])
        total_latency += res["latency_ms"]
        if res["sandbox_valid"] and res["security_valid"]:
            syntax_passes += 1
        print(f"  • Sample {idx}/{total_samples} -> Valid: {res['sandbox_valid']}, Latency: {res['latency_ms']:.2f} ms")

    avg_latency = total_latency / total_samples
    cfr = ((total_samples - syntax_passes) / total_samples) * 100.0
    print("\n================ BENCHMARK RESULTS ================")
    print(f"Mean Latency (TTFT)  : {avg_latency:.2f} ms")
    print(f"Change Failure Rate : {cfr:.1f}%")
    print(f"AST Integrity Pass  : {(syntax_passes / total_samples) * 100:.1f}%")
    print("====================================================")

if __name__ == "__main__":
    run_evaluation_suite()