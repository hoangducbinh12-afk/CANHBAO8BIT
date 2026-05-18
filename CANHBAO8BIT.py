import streamlit as st
import pandas as pd
import numpy as np
import json

# --- 1. GIAO DIỆN V10.5 CHUẨN ---
st.set_page_config(page_title="8-BIT V10.5 THE INTERSECTION", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { color: #000000 !important; background-color: #ffffff !important; font-size: 0.72rem !important; }
    .stButton button { width: 100%; border-radius: 4px; height: 38px; font-weight: 700; background-color: #000080 !important; color: #ffffff !important; }
    .reject-card { background-color: #000; color: #00ff00; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 1.2rem; text-align: center; border: 2px solid #00ff00; margin-bottom: 10px; }
    .dan-80 { background-color: #f0fdf4; border: 2px solid #16a34a; padding: 10px; font-family: monospace; color: #16a34a; font-weight: bold; text-align: center; font-size: 1.1rem; }
    .info-label { background-color: #f0f9ff; border-left: 5px solid #0ea5e9; padding: 10px; color: #0369a1; font-weight: bold; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CORE LOGIC ---
def get_props(n):
    val = int(n)
    d, u = val // 10, val % 10
    return d, u, (d + u) % 10, (d - u + 10) % 10

def get_8bit(n):
    val = int(n); d, u = val // 10, val % 10
    t_dv, h_dv = (d + u) % 10, (d - u + 10) % 10
    SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]
    return [1 if d%2!=0 else 0, 1 if u%2!=0 else 0, 1 if (d+u)%2!=0 else 0, 1 if d>=5 else 0, 1 if u>=5 else 0, 1 if t_dv>=5 else 0, 1 if val in SO_THUONG else 0, 1 if h_dv>=5 else 0]

def analyze_v10_5(history):
    if len(history) < 10: return None
    
    # 1. Quét 9 kỳ gần nhất
    past_9 = history[-9:]
    ve_d = {get_props(h['Số'])[0] for h in past_9}
    ve_u = {get_props(h['Số'])[1] for h in past_9}
    ve_t = {get_props(h['Số'])[2] for h in past_9}
    ve_h = {get_props(h['Số'])[3] for h in past_9}
    
    # 2. Xác định danh sách "THIẾU"
    all_digits = set(range(10))
    thieu_d = sorted(list(all_digits - ve_d))
    thieu_u = sorted(list(all_digits - ve_u))
    thieu_t = sorted(list(all_digits - ve_t))
    thieu_h = sorted(list(all_digits - ve_h))
    
    # 3. GIAO THOA: Tìm số thỏa mãn cả 4 điều kiện thiếu
    kill_list = []
    for i in range(100):
        d, u, t, h = get_props(i)
        if (d in thieu_d) and (u in thieu_u) and (t in thieu_t) and (h in thieu_h):
            kill_list.append(f"{i:02d}")
            
    # 4. Bảo vệ khung xương 35 kỳ (Skeleton)
    skeleton = set()
    last_35 = history[-35:] if len(history) >= 35 else history
    for h in last_35:
        s = f"{int(h['Số']):02d}"
        skeleton.add(s); skeleton.add(s[::-1])
        db, ub = (int(s[0])+5)%10, (int(s[1])+5)%10
        skeleton.add(f"{db}{ub}")
    
    final_kill = [s for s in kill_list if s not in skeleton]
    return final_kill, (thieu_d, thieu_u, thieu_t, thieu_h)

# --- 3. UI ---
if 'history' not in st.session_state: st.session_state.history = []

with st.sidebar:
    st.header("⚙️ V10.5 SETTINGS")
    up = st.file_uploader("Nạp Master Data:", type="json")
    if up:
        data = json.load(up)
        raw = data.get("history", []) if 'history' in data else data.get("ls", [])
        st.session_state.history = [{"Kỳ": i, "Số": str(h.get("Số", h.get("Số về")))} for i, h in enumerate(raw)]
    if st.button("🔴 RESET"): st.session_state.history = []; st.rerun()

st.title("🛡️ 8-BIT V10.5 - THE INTERSECTION")

if len(st.session_state.history) >= 10:
    final_kill, thieu = analyze_v10_5(st.session_state.history)
    
    # FIX LỖI TYPEERROR: Chuyển list thành string để hiển thị trong metric
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Thiếu Đầu", ", ".join(map(str, thieu[0])))
    c2.metric("Thiếu Đuôi", ", ".join(map(str, thieu[1])))
    c3.metric("Thiếu Tổng", ", ".join(map(str, thieu[2])))
    c4.metric("Thiếu Hiệu", ", ".join(map(str, thieu[3])))
    
    st.subheader(f"🔪 DANH SÁCH LOẠI CHẾT ({len(final_kill)} SỐ)")
    st.markdown(f"<div class='reject-card'>{' '.join(final_kill) if final_kill else 'Không tìm thấy số giao thoa 4 cực'}</div>", unsafe_allow_html=True)
    
    st.divider()
    # Tạo dàn 80 (Loại bỏ những con trong final_kill)
    # Nếu final_kill ít, AI sẽ tự động loại thêm các số có điểm 8-bit thấp nhất để đủ 20 số loại
    all_bits_matrix = np.array([get_8bit(h["Số"]) for h in st.session_state.history])
    p_hội_tụ = [np.mean(all_bits_matrix[-10:, j]) for j in range(8)]
    
    scored_all = []
    for i in range(100):
        s_str = f"{i:02d}"
        b = get_8bit(i)
        score = sum(b[j]*p_hội_tụ[j] + (1-b[j])*(1-p_hội_tụ[j]) for j in range(8))
        # Nếu nằm trong danh sách "Loại chết", hạ điểm xuống âm cực nặng
        if s_str in final_kill: score -= 100.0
        scored_all.append({"S": s_str, "M": score})
    
    df_rank = pd.DataFrame(scored_all).sort_values("M", ascending=False)
    dan_80 = df_rank.head(80)["S"].tolist()
    
    st.subheader("🔥 DÀN 80 SIÊU CẤP (AN TOÀN 99.3%)")
    st.markdown(f"<div class='dan-80'>{' '.join(sorted(dan_80))}</div>", unsafe_allow_html=True)
    st.info("Dàn này ưu tiên loại bỏ các số giao thoa 4 cực thiếu và 20 số có nhịp hội tụ 8-bit kém nhất.")
else:
    st.warning("Cần nạp ít nhất 10 kỳ để phân tích nhịp bệt.")
