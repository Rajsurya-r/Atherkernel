import os
import torch
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# Redirect cache away from C: drive to E: drive
CACHE_DIR = r"E:\huggingface_cache"
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = CACHE_DIR
os.environ["TORCH_HOME"] = r"E:\torch_cache"

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

app = FastAPI()
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

try:
    print("[INFO] Mounting trained DoRA adapter from local directory...")
    model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
    print("[SUCCESS] DoRA weights mounted successfully.")
except Exception as e:
    print(f"[WARN] Failed to load adapter: {e}. Falling back to base model.")
    model = base_model

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 64

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