import streamlit as st
import requests
import re

# --- 1. 配置（这里填入你刚才在 Hugging Face 复制的 Token） ---
HF_TOKEN = "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" 
API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def query_api(payload):
    # 通过 API 联网请求，不再占用本地内存
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    return response.json()

# --- 2. 维度映射表（项目核心逻辑） ---
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

st.set_page_config(page_title="Prism of Thought", page_icon="💎")

if "stage" not in st.session_state: st.session_state.stage = 1
if "messages" not in st.session_state: st.session_state.messages = []

# --- STAGE 1: 议题投射 ---
if st.session_state.stage == 1:
    st.title("💎 STAGE 1: ISSUE PROJECTION")
    topic = st.text_area("Project a question into the prism:", height=100)
    if st.button("Initiate Issue"):
        if topic:
            st.session_state.topic = topic
            st.session_state.stage = 2
            st.rerun()

# --- STAGE 2: 灵魂校准 ---
elif st.session_state.stage == 2:
    st.title("🧬 STAGE 2: CALIBRATE THE MIRROR")
    st.info(f"🎯 Topic: {st.session_state.topic}")
    col1, col2 = st.columns(2)
    with col1:
        p_val = st.select_slider("Politics", options=[1, 2, 3], value=2)
        s_val = st.select_slider("Gender", options=[1, 2, 3], value=2)
    with col2:
        c_val = st.select_slider("Class", options=[1, 2, 3], value=2)
        o_val = st.select_slider("Openness", options=[1, 2, 3], value=2)

    if st.button("Anchor Soul"):
        def get_dim(val, l, r):
            s = l if val <= 2 else r
            i = val if val <= 2 else val - 1 
            return s, i
        p_s, p_i = get_dim(p_val, "L", "R")
        s_s, s_i = get_dim(s_val, "F", "E")
        c_s, c_i = get_dim(c_val, "W", "U")
        o_s, o_i = get_dim(o_val, "O", "C")
        
        st.session_state.persona_display = f"- Politics: {DIMENSION_MAP['Politics'][p_s][p_i]}\n- Gender: {DIMENSION_MAP['Gender'][s_s][s_i]}\n- Class: {DIMENSION_MAP['Class'][c_s][c_i]}\n- Openness: {DIMENSION_MAP['Openness'][o_s][o_i]}"
        st.session_state.persona = f"Identity: Human. Protocol: Incisive, biased, no preamble, max 80 words. Worldview:\n{st.session_state.persona_display}"
        st.session_state.ai_id = f"{p_s}{p_i}-{s_s}{s_i}-{c_s}{c_i}-{o_s}{o_i}"
        st.session_state.stage = 3
        st.rerun()

# --- STAGE 3: 对话（解决断句与崩溃） ---
elif st.session_state.stage == 3:
    st.title(f"⚖️ STAGE 3: DIALOGUE [{st.session_state.ai_id}]")
    with st.expander("🛠️ Active Persona Details", expanded=True):
        st.markdown(st.session_state.persona_display)
    st.divider()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if user_input := st.chat_input("Talk to the prism..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.write(user_input)

        with st.chat_message("assistant"):
            # 使用标准的指令格式引导 AI
            prompt = f"<|im_start|>system\n{st.session_state.persona}<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
            with st.spinner("Refracting through the prism..."):
                output = query_api({"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.8}})
                try:
                    res = output[0]['generated_text'].split("assistant\n")[-1].strip()
                    # 解决“断头句”：自动截断至最后一个完整标点
                    last_p = max(res.rfind('.'), res.rfind('!'), res.rfind('?'))
                    if last_p != -1: res = res[:last_p+1]
                    st.write(res)
                    st.session_state.messages.append({"role": "assistant", "content": res})
                except:
                    st.error("API 正在预热，请等待约 15 秒后再试。")
