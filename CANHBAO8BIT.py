import streamlit as st
import json
import pandas as pd
from collections import Counter
import re
import numpy as np

# --- 1. CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="AI MATRIX PRO V15.5", layout="wide")

st.markdown("""
    <style>
    html, body { font-size: 14px !important; background-color: #f4f4f9; }
    .main .block-container { padding-top: 1.5rem; }
    
    /* Dashboard Bit */
    .bit-container { display: flex; gap: 5px; justify-content: space-between; margin-bottom: 20px; }
    .bit-card { background: #000080; color: white; padding: 10px; border-radius: 5px; text-align: center; flex: 1; min-width: 80px; }
    .bit-val { font-size: 18px; font-weight: bold; color: #00ff00; }
    
    /* Dàn số */
    .dan-box { padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 15px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .dan-title { font-weight: bold; font-size: 16px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
    .dan-content { line-height: 2; letter-spacing: 1px; font-family: 'Courier New', monospace; font-size: 16px; }
    
    /* Button */
    div.stButton > button { width: 100%; height: 3.5em; border-radius: 8px; font-weight: bold; background: #FF4B4B; color: white; border: none; }
    div.stButton > button:hover { background: #ff3333; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM LOGIC CHUYÊN GIA ---
BIT_LABELS = ["Đ.CL", "Đu.CL", "T.CL", "Đ.TB", "Đu.TB", "T.TB", "Hệ", "Hi.TB"]
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]

def get_8bit(n):
    val = int(n); d, u = val // 10, val % 10
    t_dv, h_dv = (d + u) % 10, (d - u + 10) % 10
    return [1 if d%2!=0 else 0, 1 if u%2!=0 else 0, 1 if (d+u)%2!=0 else 0, 
            1 if d>=5 else 0, 1 if u>=5 else 0, 1 if t_dv>=5 else 0, 
            1 if val in SO_THUONG else 0, 1 if h_dv>=5 else 0]

def get_bóng(n):
    val = int(n); d, u = val // 10, val % 10
    b_d = (d + 5) % 10; b_u = (u + 5) % 10
    return b_d * 10 + b_u

# --- 3. QUẢN LÝ STATE ---
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'data_list' not in st.session_state: st.session_state.data_list = []
if 'last_danh_sach' not in st.session_state: st.session_state.last_danh_sach = None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ SETTINGS")
    up_file = st.file_uploader("Nạp Data (JSON)", type=['json'])
    if up_file:
        raw = json.load(up_file)
        st.session_state.data_list = raw.get('data', [])
        st.session_state.history_log = raw.get('history', [])
        st.success("Hệ thống đã sẵn sàng!")
    
    if st.button("🚨 RESET HỆ THỐNG"):
        st.session_state.clear(); st.rerun()

# --- 5. GIAO DIỆN CHÍNH ---
st.title("🎯 AI MATRIX PRO V15.5")

if st.session_state.data_list:
    data = st.session_state.data_list
    
    # Dashboard 8-Bit (Nhịp 10 kỳ gần nhất)
    all_bits = np.array([get_8bit(x) for x in data[-10:]])
    probs = np.mean(all_bits, axis=0)
    
    st.markdown('<div class="bit-container">' + "".join([
        f'<div class="bit-card"><div>{BIT_LABELS[i]}</div><div class="bit-val">{int(probs[i]*100)}%</div></div>' 
        for i in range(8)]) + '</div>', unsafe_allow_html=True)

    with st.container():
        c1, c2 = st.columns([3, 1])
        new_res = c1.text_input("SỐ VỪA VỀ:", placeholder="Nhập 2 số cuối...")
        if c2.button("XÁC NHẬN") and new_res:
            val = int(new_res[-2:])
            st.session_state.data_list.append(val)
            st.rerun()

    st.write("---")
    num_soi = st.number_input("SOI SAU CON SỐ:", 0, 99, value=data[-1])

    if st.button("🚀 PHÂN TÍCH MA TRẬN TỔNG LỰC"):
        # A. Phân tích Follower & Bit hội tụ
        global_counts = Counter(data)
        indices = [i for i, x in enumerate(data[:-1]) if x == num_soi]
        followers = [data[i+1] for i in indices]
        
        # Lấy xu hướng Bit của những con nổ sau num_soi
        if followers:
            f_bits = np.array([get_8bit(x) for x in followers])
            target_pattern = [1 if np.mean(f_bits[:, j]) >= 0.5 else 0 for j in range(8)]
        else:
            target_pattern = [1 if p >= 0.5 else 0 for p in probs]

        # B. HỆ THỐNG CHẤM ĐIỂM SCORING
        scores = {}
        after_counts = Counter(followers)
        
        for i in range(100):
            s = 0
            # 1. Bạc nhớ trực tiếp (P1)
            if i in after_counts: s += after_counts[i] * 5000000
            
            # 2. Nghịch đảo & Bóng (P2)
            rev = (i % 10 * 10) + (i // 10)
            bóng = get_bóng(i)
            if rev in after_counts: s += after_counts[rev] * 50000
            if bóng in after_counts: s += after_counts[bóng] * 10000
            
            # 3. Khớp 8-Bit hội tụ (P3)
            current_bits = get_8bit(i)
            match_bit = sum(1 for a, b in zip(current_bits, target_pattern) if a == b)
            s += match_bit * 5000
            
            # 4. Tie-breaker Lịch sử 2700 kỳ
            s += global_counts.get(i, 0)
            
            scores[i] = s

        # C. Sắp xếp và chia dàn
        full_ranked = [n for n, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
        
        st.session_state.last_danh_sach = {
            "🔥 DÀN KẾT (19s)": sorted(full_ranked[:19]),
            "⭐ DÀN ĐẸP (20s)": sorted(full_ranked[19:39]),
            "💎 TRUNG BÌNH (20s)": sorted(full_ranked[39:59]),
            "🛡️ XÉT LÓT (20s)": sorted(full_ranked[59:79]),
            "🚫 DÀN LOẠI (19s)": sorted(full_ranked[79:])
        }

    # --- HIỂN THỊ DÀN SỐ ---
    if st.session_state.last_danh_sach:
        ds = st.session_state.last_danh_sach
        icons = ["🎯", "✨", "📈", "🛡️", "💀"]
        colors = ["#FF4B4B", "#FFA500", "#1C83E1", "#28A745", "#6C757D"]
        
        for i, (label, s_list) in enumerate(ds.items()):
            st.markdown(f"""
                <div class="dan-box">
                    <div class="dan-title" style="color:{colors[i]};">{icons[i]} {label}</div>
                    <div class="dan-content">
                        {' '.join([f"<b>{x:02d}</b>" for x in s_list])}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Lịch sử
    if st.session_state.history_log:
        with st.expander("📋 XEM LỊCH SỬ ĐỐI SOÁT"):
            st.table(pd.DataFrame(st.session_state.history_log))

    # Xuất file
    st.divider()
    export_json = json.dumps({"data": st.session_state.data_list, "history": st.session_state.history_log}, indent=4)
    st.download_button("📥 XUẤT DATA JSON", export_json, "AI_Matrix_V15_5.json", "application/json")

else:
    st.warning("👋 Chào mày! Hãy nạp dữ liệu 2700 kỳ ở Sidebar để kích hoạt Ma trận.")
