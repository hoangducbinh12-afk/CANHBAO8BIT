import streamlit as st
import pandas as pd
import json

# --- 1. GIAO DIỆN V10.5 ---
st.set_page_config(page_title="8-BIT V10.5 THE INTERSECTION", layout="wide")
st.markdown("""
    <style>
    .stButton button { background-color: #000080 !important; color: white !important; font-weight: bold; }
    .reject-card { background-color: #000; color: #00ff00; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 1.2rem; text-align: center; border: 2px solid #00ff00; }
    .dan-80 { background-color: #f0fdf4; border: 2px solid #16a34a; padding: 10px; font-family: monospace; color: #16a34a; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

def get_props(n):
    d, u = n // 10, n % 10
    return d, u, (d + u) % 10, (d - u + 10) % 10

def analyze_v10_5(history):
    if len(history) < 10: return None
    
    # 1. Lấy 9 kỳ gần nhất
    past_9 = history[-9:]
    ve_d = {get_props(int(h['Số']))[0] for h in past_9}
    ve_u = {get_props(int(h['Số']))[1] for h in past_9}
    ve_t = {get_props(int(h['Số']))[2] for h in past_9}
    ve_h = {get_props(int(h['Số']))[3] for h in past_9}
    
    # 2. Xác định danh sách "THIẾU" (0-9)
    all_digits = set(range(10))
    thieu_d = all_digits - ve_d
    thieu_u = all_digits - ve_u
    thieu_t = all_digits - ve_t
    thieu_h = all_digits - ve_h
    
    # 3. GIAO THOA: Chỉ lấy những số thỏa mãn CẢ 4 ĐIỀU KIỆN THIẾU
    kill_list = []
    for i in range(100):
        d, u, t, h = get_props(i)
        if (d in thieu_d) and (u in thieu_u) and (t in thieu_t) and (h in thieu_h):
            kill_list.append(f"{i:02d}")
            
    # 4. Bảo vệ khung xương 35 kỳ (Dù nằm trong kill_list vẫn cứu lại)
    skeleton = set()
    for h in history[-35:]:
        s = f"{int(h['Số']):02d}"
        skeleton.add(s); skeleton.add(s[::-1])
        db, ub = (int(s[0])+5)%10, (int(s[1])+5)%10
        skeleton.add(f"{db}{ub}")
    
    final_kill = [s for s in kill_list if s not in skeleton]
    return final_kill, (thieu_d, thieu_u, thieu_t, thieu_h)

# --- PHẦN UI ---
if 'history' not in st.session_state: st.session_state.history = []

with st.sidebar:
    st.header("⚙️ V10.5 SETTINGS")
    up = st.file_uploader("Nạp Master Data:", type="json")
    if up:
        data = json.load(up)
        st.session_state.history = data.get("history", []) if 'history' in data else data.get("ls", [])

st.title("🛡️ 8-BIT V10.5 - THE INTERSECTION")

if len(st.session_state.history) >= 10:
    final_kill, thieu = analyze_v10_5(st.session_state.history)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Thiếu Đầu", list(thieu[0]))
    col2.metric("Thiếu Đuôi", list(thieu[1]))
    col3.metric("Thiếu Tổng", list(thieu[2]))
    col4.metric("Thiếu Hiệu", list(thieu[3]))
    
    st.subheader(f"🔪 DANH SÁCH LOẠI CHẾT ({len(final_kill)} SỐ)")
    st.markdown(f"<div class='reject-card'>{' '.join(final_kill) if final_kill else 'Không có số nào thỏa mãn 4 đ/k thiếu'}</div>", unsafe_allow_html=True)
    
    st.divider()
    # Dàn 80/90 số
    full_100 = [f"{i:02d}" for i in range(100)]
    dan_8x = [s for s in full_100 if s not in final_kill]
    
    st.subheader(f"🔥 DÀN AN TOÀN ({len(dan_8x)} SỐ)")
    st.markdown(f"<div class='dan-80'>{' '.join(dan_8x)}</div>", unsafe_allow_html=True)
else:
    st.warning("Cần nạp ít nhất 10 kỳ để phân tích.")
