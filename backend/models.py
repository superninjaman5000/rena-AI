from transformers import AutoTokenizer, AutoModelForCausalLM
from awq import AutoAWQForCausalLM
import torch

MODEL_PATH = "/home/kaoru/models/models--TheBloke--U-Amethyst-20B-AWQ/"

# Load tokenizer & model locally
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,  # Use half precision to save memory
    device_map="auto",  # Auto-allocate GPU
    attn_implementation="sdpa",  # Optimized attention
    low_cpu_mem_usage=True  # Reduce RAM consumption
)

def generate_response(prompt):
    """Generates a response using the AI model"""
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to("cuda")

    with torch.no_grad():
        outputs = model.generate(
            input_ids,
            max_new_tokens=250,
            do_sample=True,
            temperature=0.7,
            repetition_penalty=1.2,
            top_p=0.9
        )

    return tokenizer.decode(outputs[0], skip_special_tokens=True)
