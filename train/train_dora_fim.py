"""
AetherKernel: Weight-Decomposed Low-Rank Adaptation (DoRA) Training Script
Fine-tunes a base code model with Fill-in-the-Middle (FIM) formatting.
Optimized to execute on Google Colab or Kaggle T4 GPUs.
"""
import os
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model

BASE_MODEL_NAME = "Qwen/Qwen2.5-Coder-1.5B"
OUTPUT_DIR = "./aether_dora_adapter"

def build_fim_dataset(tokenizer, num_samples: int = 200):
    raw_samples = [
        {
            "prefix": "def verify_signature(public_key: str, message: bytes, sig: bytes) -> bool:\n    try:\n",
            "middle": "        verifier = load_verifier(public_key)\n        return verifier.verify(message, sig)\n",
            "suffix": "    except Exception:\n        return False\n"
        },
        {
            "prefix": "class MemoryPool:\n    def __init__(self, capacity: int):\n",
            "middle": "        self.allocated = 0\n        self.blocks = []\n        self.capacity = capacity\n",
            "suffix": "    def is_exhausted(self) -> bool:\n        return self.allocated >= self.capacity\n"
        }
    ] * (num_samples // 2)

    def tokenize_fn(batch):
        formatted_prompts = [
            f"<fim_prefix>{p}<fim_suffix>{s}<fim_middle>{m}<|endoftext|>"
            for p, s, m in zip(batch["prefix"], batch["suffix"], batch["middle"])
        ]
        return tokenizer(
            formatted_prompts,
            truncation=True,
            max_length=512,
            padding="max_length"
        )

    ds = Dataset.from_dict({
        "prefix": [x["prefix"] for x in raw_samples],
        "middle": [x["middle"] for x in raw_samples],
        "suffix": [x["suffix"] for x in raw_samples],
    })
    return ds.map(tokenize_fn, batched=True)

def run_dora_training():
    print(f"[INFO] Initializing Tokenizer & Base Model: {BASE_MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        use_dora=True  # Enables magnitude and directional weight decomposition
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    print("[INFO] Preparing Fill-in-the-Middle (FIM) dataset...")
    train_dataset = build_fim_dataset(tokenizer, num_samples=200)

    training_arguments = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        num_train_epochs=2,
        logging_steps=10,
        fp16=True,
        save_strategy="no",
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_arguments,
        train_dataset=train_dataset
    )

    print("[INFO] Commencing DoRA model adaptation...")
    trainer.train()

    print(f"[INFO] Saving finalized DoRA weights to: {OUTPUT_DIR}")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__":
    run_dora_training()