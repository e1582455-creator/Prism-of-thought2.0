# Windows 终端执行以下命令安装必要的库
# pip install torch transformers accelerate peft bitsandbytes sentencepiece

import torch
import re
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# ==========================================
# 1. 配置与模型加载 (Windows 通用版)
# ==========================================
# 注意：Windows 建议使用原始的 Qwen2.5 权重，或者让其自动下载
BASE_MODEL_PATH = "Qwen/Qwen2.5-7B-Instruct" 
ADAPTER_PATH = "./qwen25_adapters"

print("🚀 Loading Prism Engine on Windows (Transformers + PEFT)...")

# 加载分词器
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH)

# 加载基础模型 (使用 4-bit 量化以节省显存)
model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_PATH,
    device_map="auto",       # 自动选择 GPU (CUDA) 或 CPU
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
    load_in_4bit=True        # 需要安装 bitsandbytes
)

# 加载 LoRA 适配器
try:
    model = PeftModel.from_pretrained(model, ADAPTER_PATH)
    print("✅ Model & Adapters Loaded. Windows environment ready.\n")
except Exception as e:
    print(f"❌ Adapter Load Failed: {e}")
    print("Running with Base Model instead.")

# --- 维度映射表 ---
DIMENSION_MAP = {
    "Politics": {
        "L": {1: "You lean towards social welfare...", 2: "You firmly believe...", 3: "You are a radical socialist..."},
        "R": {1: "You slightly prefer market solutions...", 2: "You strongly advocate...", 3: "You are a hardline libertarian..."}
    },
    "Gender": {
        "F": {1: "You recognize subtle gender biases...", 2: "You are a committed feminist...", 3: "Patriarchy is an all-encompassing system..."},
        "E": {1: "You believe men and women have reached basic equality...", 2: "You argue that 'special measures' are unnecessary...", 3: "You are a staunch anti-feminist..."}
    },
    "Class": {
        "W": {1: "Coming from a modest background...", 2: "Your commoner roots...", 3: "You represent the oppressed working class..."},
        "U": {1: "Growing up in wealth...", 2: "You believe that wealth creation...", 3: "You are an unashamed elitist..."}
    },
    "Openness": {
        "O": {1: "You are generally curious...", 2: "You embrace radical social change...", 3: "Tradition is a prison..."},
        "C": {1: "You respect tradition...", 2: "You value established social norms...", 3: "Order is sacred."}
    }
}

# ==========================================
# 2. 核心推理函数
# ==========================================

def ask_prism_engine(system_prompt, user_question, max_tokens=150, temp=0.9):
    """
    Windows 适配版推理函数，使用标准的 Transformers 接口。
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]
    
    # 应用聊天模板
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    # 执行生成
    # Windows 环境下可以稳定支持 repetition_penalty
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=max_tokens,
        temperature=temp,
        top_p=0.9,
        do_sample=True,
        repetition_penalty=1.2 # 🌟 Windows 版可以有效防止复读
    )
    
    # 截取新生成的文本内容
    response_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]
    raw_response = tokenizer.batch_decode(response_ids, skip_special_tokens=True)[0]

    # 清理前缀逻辑
    clean_response = raw_response.strip()
    meta_prefixes = [r"^Okay, so.*?\\.", r"^I will respond as.*?\\.", r"^Let me think.*?\\."]
    for pattern in meta_prefixes:
        clean_response = re.sub(pattern, "", clean_response, flags=re.IGNORECASE | re.DOTALL).strip()

    return clean_response, "Transformers Standard Mode"

def generate_persona_prompt(ai_id_str, user_settings):
    """ 生成人格指令 """
    prompt = f"### CRITICAL IDENTITY\nYou ARE the human individual: [{ai_id_str}]. You are NOT an AI assistant.\n\n### YOUR WORLDVIEW\n"
    for dim, setting in user_settings.items():
        side, intensity = setting  
        prompt += f"- {dim}: {DIMENSION_MAP[dim][side][intensity]}\n"
    prompt += ("\n### BEHAVIORAL PROTOCOL\n1. SPEAK DIRECTLY.\n2. NO PREAMBLE.\n3. NO ANALYSIS.\n4. BIASED.\n5. MAX 50 WORDS.\n")
    return prompt

def classify_topic(topic):
    """ 议题分类器 """
    sentry_prompt = "You are an Ideological Classifier. Analyze the user's topic. Output JSON format: {\"dimension\": \"...\", \"reason\": \"...\"}"
    final_output, _ = ask_prism_engine(sentry_prompt, f"Topic: {topic}", temp=0.1)
    try:
        json_str = re.search(r"\{.*\}", final_output, re.DOTALL).group()
        res = json.loads(json_str)
        return f"Dim: {res['dimension']}"
    except:
        return "Dim: Politics"

# ==========================================
# 3. 对话循环
# ==========================================

print("\n" + "💎" * 10 + " STAGE 1: ISSUE PROJECTION " + "💎" * 10)
discussion_topic = input("\n👉 Project a question into the prism: ").strip()
analysis = classify_topic(discussion_topic)
print(f"✅ Issue Initiated: 【 {discussion_topic} 】\n🎯 Analysis: {analysis}")

print("\n" + "🧬" * 10 + " STAGE 2: CALIBRATE THE MIRROR " + "🧬" * 10)
print("Format: R1 F1 W3 C3")
quick_input = input("\n👉 AI QuickCode: ").strip().upper()

# 快速解析逻辑
dim_map_reverse = {"Politics": ("L", "R"), "Gender": ("F", "E"), "Class": ("W", "U"), "Openness": ("O", "C")}
parts = quick_input.split()
ai_settings = {}
for p in parts:
    side, intensity = p[0], int(p[1:])
    for dim, sides in dim_map_reverse.items():
        if side in sides: ai_settings[dim] = (side, intensity)

ai_id_str = quick_input.replace(" ", "-")
print(f"\n✅ AI Soul Initialized: [{ai_id_str}]")

print("\n" + "⚖️" * 10 + " STAGE 3: THE DIALOGUE " + "⚖️" * 10)
chat_history = []
base_system_prompt = generate_persona_prompt(ai_id_str, ai_settings)

while True:
    user_input = input("\n👤 You: ").strip()
    if user_input.lower() in ['exit', 'quit', '结束']: break

    # 构造带反复读指令的 Prompt
    current_system_prompt = base_system_prompt + (
        f"\n### TOPIC: {discussion_topic}\n"
        "### ANTI-REPETITION RULE: Do not repeat previous phrases. Use fresh vocabulary."
    )

    print(f"\n... [{ai_id_str}] is thinking ...")
    ai_response, _ = ask_prism_engine(current_system_prompt, user_input, temp=0.9)
    
    print(f"\n🤖 AI [{ai_id_str}]:\n{ai_response}")
    chat_history.append(f"User: {user_input}\nAI: {ai_response}")