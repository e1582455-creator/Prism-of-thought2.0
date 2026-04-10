import streamlit as st
import requests
import re

# --- 1. 云端配置 (已填入你的 Token) ---
# 这样不需要在本地加载 3GB 权重，彻底解决 Connection error
HF_TOKEN = "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"
API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def query_api(payload):
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    return response.json()

# --- 2. 维度映射表 (保持你的原始设定) ---
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
        def get_dim_setting(val, l, r):
            side = l if val <= 2 else r
            intensity = val if val <= 2 else val - 1 
            return side, intensity

        p_s, p_i = get_dim_setting(p_val, "L", "R")
        s_s, s_i = get_dim_setting(s_val, "F", "E")
        c_s, c_i = get_dim_setting(c_val, "W", "U")
        o_s, o_i = get_dim_setting(o_val, "O", "C")

        display_details = (
            f"- **Politics**: {DIMENSION_MAP['Politics'][p_s][p_i]}\n"
            f"- **Gender**: {DIMENSION_MAP['Gender'][s_s][s_i]}\n"
            f"- **Class**: {DIMENSION_MAP['Class'][c_s][c_i]}\n"
            f"- **Openness**: {DIMENSION_MAP['Openness'][o_s][o_i]}"
        )
        st.session_state.persona_summary = f"P:{p_val}, G:{s_val}, C:{c_val}, O:{o_val}"
        st.session_state.persona_display = display_details
        st.session_state.persona = f"Identity: Human. Protocol: Incisive, no preamble, max 80 words. Worldview:\n{display_details}"
        st.session_state.ai_id = f"{p_s}{p_i}-{s_s}{s_i}-{c_s}{c_i}-{o_s}{o_i}"
        st.session_state.stage = 3
        st.rerun()

# --- STAGE 3: THE DIALOGUE (强化语义完整版) ---
elif st.session_state.stage == 3:
    st.title(f"⚖️ STAGE 3: DIALOGUE [{st.session_state.ai_id}]")
    
    with st.expander("🛠️ Active Persona & Issue Details", expanded=True):
        st.markdown(f"**Topic:** {st.session_state.topic}")
        st.markdown(st.session_state.persona_display)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if user_input := st.chat_input("Input your thought..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.write(user_input)

        with st.chat_message("assistant"):
            # 采用标注对话格式
            prompt = f"<|im_start|>system\n{st.session_state.persona}<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
            
            with st.spinner(f"Refracting as {st.session_state.ai_id}..."):
                output = query_api({"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.8}})
                try:
                    res = output[0]['generated_text'].split("assistant\n")[-1].strip()
                    
                    # 解决断头句：自动截断至最后一个完整标点
                    last_punc = max(res.rfind('.'), res.rfind('!'), res.rfind('?'))
                    if last_punc != -1:
                        final_res = res[:last_punc + 1]
                    else:
                        final_res = res
                    
                    st.write(final_res)
                    st.session_state.messages.append({"role": "assistant", "content": final_res})
                except:
                    st.error("API 正在加载，请等 15 秒后重试。")

    if st.sidebar.button("Reset Session"):
        st.session_state.clear()
        st.rerun()
