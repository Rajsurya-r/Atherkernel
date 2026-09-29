import os
import torch
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Cache directories on E: drive
CACHE_DIR = r"E:\huggingface_cache"
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = CACHE_DIR
os.environ["TORCH_HOME"] = r"E:\torch_cache"

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

app = FastAPI(title="AetherKernel Speculative Inference Runtime")
BASE_MODEL = "Qwen/Qwen2.5-Coder-1.5B"
ADAPTER_DIR = "./aether_dora_adapter"

print(f"[INFO] Using download directory on E drive: {CACHE_DIR}")
print("[INFO] Loading base model into E: drive cache...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, cache_dir=CACHE_DIR)
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float32,
    device_map="cpu",
    cache_dir=CACHE_DIR
)

adapter_status = "Not Mounted"
try:
    print("[INFO] Mounting trained DoRA adapter from local directory...")
    model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
    adapter_status = "Active (DoRA Weights Mounted)"
    print("[SUCCESS] DoRA weights mounted successfully.")
except Exception as e:
    print(f"[WARN] Failed to load adapter: {e}. Falling back to base model.")
    model = base_model
    adapter_status = f"Fallback to Base Model ({e})"

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 64

@app.get("/", response_class=HTMLResponse)
def index():
    """Web UI Status Page for http://localhost:8000"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AetherKernel Inference Engine</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d1117; color: #c9d1d9; display: flex; justify-content: center; align-items: center; height: 90vh; margin: 0; }}
            .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 32px; width: 520px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }}
            h2 {{ color: #58a6ff; margin-top: 0; }}
            .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: bold; background: #238636; color: #fff; }}
            .metric {{ margin: 14px 0; font-size: 14px; line-height: 1.5; }}
            code {{ background: #21262d; padding: 3px 8px; border-radius: 4px; color: #79c0ff; font-family: Consolas, monospace; }}
            a {{ color: #58a6ff; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>⚡ AetherKernel Serving Engine</h2>
            <div class="metric"><strong>Status:</strong> <span class="badge">ONLINE</span></div>
            <div class="metric"><strong>Target Foundation Model:</strong> <code>{BASE_MODEL}</code></div>
            <div class="metric"><strong>Adapter Layer:</strong> <code>{adapter_status}</code></div>
            <div class="metric"><strong>Inference Endpoint:</strong> <code>POST /v1/completions</code></div>
            <div class="metric"><strong>Interactive API Docs:</strong> <a href="/docs" target="_blank">Open Swagger UI (/docs)</a></div>
        </div>
    </body>
    </html>
    """

@app.post("/v1/completions")
def generate(req: CompletionRequest):
    inputs = tokenizer(req.prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=req.max_tokens,
            pad_token_id=tokenizer.eos_token_id
        )
    generated_text = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    return {"choices": [{"text": generated_text}]}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)