import streamlit as st
import torch
import re
import gc
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- 1. 内存与环境优化初始化 ---
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()

@st.cache_resource
def load_prism_engine():
    # 使用 Qwen 1.5B 确保 CPU 也能跑动
    model_name = "Qwen/Qwen2.5-1.5B-Instruct" 
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32, 
        low_cpu_mem_usage=True, # 关键：降低内存峰值
        device_map={"": "cpu"} 
    )
    return model, tokenizer

# --- 2. 维度映射表 (对标 Chatbot.py) ---
DIMENSION_MAP = {
    "Politics": {"L": {1: "You lean towards social welfare...", 2: "You firmly believe in socialist redistribution...", 3: "You are a radical socialist..."},
                "R": {1: "You slightly prefer market solutions...", 2: "You strongly advocate for free markets...", 3: "You are a hardline libertarian..."}},
    "Gender": {"F": {1: "You recognize subtle gender biases...", 2: "You are a committed feminist...", 3: "Patriarchy is an all-encompassing system..."},
               "E": {1: "You believe men and women have reached basic equality...", 2: "You argue that 'special measures' are unnecessary...", 3: "You are a staunch anti-feminist..."}},
    "Class": {"W": {1: "Coming from a modest background...", 2: "Your commoner roots...", 3: "You represent the oppressed working class..."},
              "U": {1: "Growing up in wealth...", 2: "You believe that wealth creation is a virtue...", 3: "You are an unashamed elitist..."}},
    "Openness": {"O": {1: "You are generally curious...", 2: "You embrace radical social change...", 3: "Tradition is a prison..."},
                 "C": {1: "You respect tradition...", 2: "You value established social norms...", 3: "Order is sacred."}}
}

st.set_page_config(page_title="Prism of Thought", page_icon="💎", layout="centered")

# 加载模型
try:
    model, tokenizer = load_prism_engine()
except Exception as e:
    st.error(f"Engine Failure: {e}")
    st.stop()

# 状态管理
if "stage" not in st.session_state: st.session_state.stage = 1
if "messages" not in st.session_state: st.session_state.messages = []

# --- STAGE 1: ISSUE PROJECTION ---
if st.session_state.stage == 1:
    st.title("💎 STAGE 1: ISSUE PROJECTION")
    topic = st.text_area("Project a question into the prism:", 
                         placeholder="e.g., Will UBI affect work motivation?", height=100)
    if st.button("Initiate Issue"):
        if topic:
            st.session_state.topic = topic
            st.session_state.stage = 2
            st.rerun()

# --- STAGE 2: CALIBRATE THE MIRROR ---
elif st.session_state.stage == 2:
    st.title("🧬 STAGE 2: CALIBRATE THE MIRROR")
    st.info(f"🎯 **Topic:** {st.session_state.topic}")
    
    st.markdown("### Persona Settings")
    col1, col2 = st.columns(2)
    with col1:
        p_val = st.select_slider("Politics (Left-Right)", options=[1, 2, 3], value=2)
        s_val = st.select_slider("Gender (Feminist-Equality)", options=[1, 2, 3], value=2)
    with col2:
        c_val = st.select_slider("Class (Working-Upper)", options=[1, 2, 3], value=2)
        o_val = st.select_slider("Openness (Radical-Traditional)", options=[1, 2, 3], value=2)

    if st.button("Anchor Soul"):
        def get_dim_setting(val, left_char, right_char):
            side = left_char if val <= 2 else right_char
            intensity = val if val <= 2 else val - 1 
            return side, intensity

        p_side, p_i = get_dim_setting(p_val, "L", "R")
        s_side, s_i = get_dim_setting(s_val, "F", "E")
        c_side, c_i = get_dim_setting(c_val, "W", "U")
        o_side, o_i = get_dim_setting(o_val, "O", "C")

        # 存储人格详细描述
        display_details = (
            f"- **Politics**: {DIMENSION_MAP['Politics'][p_side][p_i]}\n"
            f"- **Gender**: {DIMENSION_MAP['Gender'][s_side][s_i]}\n"
            f"- **Class**: {DIMENSION_MAP['Class'][c_side][c_i]}\n"
            f"- **Openness**: {DIMENSION_MAP['Openness'][o_side][o_i]}"
        )
        st.session_state.persona_summary = f"Political {p_val}/3, Social {s_val}/3, Class {c_val}/3, Openness {o_val}/3"
        st.session_state.persona_display = display_details
        
        # System Prompt 构建
        st.session_state.persona = f"### identity\nYou are a human. NOT an AI.\n### worldview\n{display_details}\n### protocol\nBe incisive, no preamble, max 80 words."
        st.session_state.ai_id = f"{p_side}{p_i}-{s_side}{s_i}-{c_side}{c_i}-{o_side}{o_i}"
        st.session_state.stage = 3
        st.rerun()

# --- STAGE 3: THE DIALOGUE (强化人格展示版 + 自动截断语义完整版) ---
elif st.session_state.stage == 3:
    st.title(f"⚖️ STAGE 3: DIALOGUE [{st.session_state.ai_id}]")
    
    # 顶部展示当前设定的“灵魂”背景
    with st.expander("🛠️ Active Persona & Issue Details", expanded=True):
        st.markdown(f"**Topic:** {st.session_state.topic}")
        st.markdown(f"**QuickCode Specs:** {st.session_state.persona_summary}")
        st.divider()
        st.markdown(st.session_state.persona_display)

    # 对话流
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if user_input := st.chat_input("Input your thought..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.write(user_input)

        with st.chat_message("assistant"):
            full_prompt = f"System: {st.session_state.persona}\nTopic: {st.session_state.topic}\nUser: {user_input}\nAssistant:"
            inputs = tokenizer(full_prompt, return_tensors="pt").to("cpu")
            
            with st.spinner(f"Refracting as {st.session_state.ai_id}..."):
                # 显存清理，防止连接错误
                gc.collect()
                
                # 生成回复，保持与 Chatbot.py 一致的参数
                outputs = model.generate(
                    **inputs, 
                    max_new_tokens=150, 
                    temperature=0.9, 
                    repetition_penalty=1.2, 
                    do_sample=True
                )
                
                # 原始解码
                raw_response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
                
                # 1. 清理 AI 常见的客套前缀
                cleaned_response = re.sub(r"^(Okay|I will|From my perspective).*?[\.\!\?]", "", raw_response, flags=re.IGNORECASE).strip()
                
                # 2. 自动截断至最后一个完整标点，防止出现断头句
                # 寻找 句号、感叹号、问号 的最后一个索引
                last_punc = max(
                    cleaned_response.rfind('.'), 
                    cleaned_response.rfind('!'), 
                    cleaned_response.rfind('?')
                )
                
                if last_punc != -1:
                    # 只截取到最后一个标点位置
                    final_response = cleaned_response[:last_punc + 1]
                else:
                    # 如果一整段都没有标点，则保留原样 (或者你可以根据需求做其他处理)
                    final_response = cleaned_response
                
                st.write(final_response)
                st.session_state.messages.append({"role": "assistant", "content": final_response})

    if st.sidebar.button("Reset Session"):
        st.session_state.clear()
        st.rerun()