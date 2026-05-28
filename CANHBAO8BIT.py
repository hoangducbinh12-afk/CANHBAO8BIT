import streamlit as st
import json
import pandas as pd
from collections import Counter
import re
import numpy as np

# --- 1. CSS CHUẨN MOBILE ---
st.set_page_config(page_title="AI MATRIX PRO V15.6", layout="wide")
st.markdown("""
    <style>
    html, body { font-size: 14px !important; background-color: #f8f9fa; }
    .bit-container { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 10px; }
    .bit-card { background: #000080; color: white; padding: 10px; border-radius: 8px; text-align: center; min-width: 80px; flex-shrink: 0; }
    .bit-val { font-size: 16px; font-weight: bold; color: #00ff00; }
    .dan-box { padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 15px; background: white; }
    .dan-title { font-weight: bold; font-size: 15px; margin-bottom: 8px; }
    .dan-content { line-height: 1.8; font-family: monospace; font-size: 17px; color: #2d3436; }
    div.stButton > button { width: 100%; height: 3.8em; border-radius: 10px; font-weight: bold; background: #FF4B4B; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC 8-BIT ---
BIT_LABELS = ["Đ.CL", "Đu.CL", "T.CL", "Đ.TB", "Đu.TB", "T.TB", "Hệ", "Hi.TB"]
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]

def get_8bit(n):
    val = int(n); d, u = val // 10, val % 10
    t_dv, h_dv = (d + u) % 10, (d - u + 10) % 10
    return [1 if d%2!=0 else 0, 1 if u%2!=0 else 0, 1 if (d+u)%2!=0 else 0, 
            1 if d>=5 else 0, 1 if u>=5 else 0, 1 if t_dv>=5 else 0, 
            1 if val in SO_THUONG else 0, 1 if h_dv>=5 else 0]

# --- 3. UI & LOGIC ---
if 'data_list' not in st.session_state: st.session_state.data_list = []
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'last_danh_sach' not in st.session_state: st.session_state.last_danh_sach = None

with st.sidebar:
    st.title("⚙️ HỆ THỐNG")
    up = st.file_uploader("Nạp Data", type=['json'])
    if up:
        raw = json.load(up)
        st.session_state.data_list = raw.get('data', [])
        st.session_state.history_log = raw.get('history', [])

st.title("🎯 AI MATRIX V15.6")

if st.session_state.data_list:
    data = st.session_state.data_list
    
    # Dashboard Nhịp Bit hiện tại
    all_bits = np.array([get_8bit(x) for x in data[-10:]])
    probs = np.mean(all_bits, axis=0)
    st.markdown('<div class="bit-container">' + "".join([f'<div class="bit-card"><div>{BIT_LABELS[i]}</div><div class="bit-val">{int(probs[i]*100)}%</div></div>' for i in range(8)]) + '</div>', unsafe_allow_html=True)

    # Bước 1: Nhập KQ
    with st.expander("📌 BƯỚC 1: CẬP NHẬT KẾT QUẢ", expanded=True):
        c1, c2 = st.columns([2, 1])
        new_res = c1.text_input("GĐB vừa nổ:", placeholder="Ví dụ: 23")
        if c2.button("XÁC NHẬN") and new_res:
            val = int(new_res[-2:])
            st.session_state.data_list.append(val)
            st.rerun()

    st.write("---")
    
    # Bước 2: Phân tích theo THUỘC TÍNH
    if st.button("🚀 QUÉT NHỊP THUỘC TÍNH (10 LẦN GẦN NHẤT)"):
        # 1. Lấy trạng thái Bit của con số hiện tại
        current_num = data[-1]
        current_bit_pattern = get_8bit(current_num)
        
        # 2. Tìm 10 kỳ gần nhất có trạng thái Bit y hệt
        follower_bits = []
        follower_nums = []
        
        # Quét ngược lịch sử
        count = 0
        for i in range(len(data) - 2, -1, -1):
            if get_8bit(data[i]) == current_bit_pattern:
                follower_nums.append(data[i+1])
                follower_bits.append(get_8bit(data[i+1]))
                count += 1
                if count == 10: break # Chỉ lấy 10 lần gần nhất
        
        # 3. Chấm điểm dựa trên "Gen Bit" của nhóm Follower
        if follower_bits:
            f_bits_arr = np.array(follower_bits)
            # Tìm xu hướng Bit tiếp theo (Top nhịp)
            target_pattern = [1 if np.mean(f_bits_arr[:, j]) >= 0.5 else 0 for j in range(8)]
            
            scores = {}
            global_counts = Counter(data)
            f_num_counts = Counter(follower_nums)
            
            for i in range(100):
                s = 0
                # Tầng 1: Ưu tiên con số thực tế hay về sau trạng thái này
                if i in f_num_counts: s += f_num_counts[i] * 1000000
                
                # Tầng 2: Ưu tiên con số KHỚP BỘ BIT xu hướng (Cực quan trọng)
                curr_i_bits = get_8bit(i)
                match_count = sum(1 for a, b in zip(curr_i_bits, target_pattern) if a == b)
                s += match_bit * 10000 # Thằng nào khớp Bit thì ngoi lên
                
                # Tầng 3: Vía lịch sử
                s += global_counts.get(i, 0)
                scores[i] = s
            
            full_ranked = [n for n, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
            
            st.session_state.last_danh_sach = {
                "🔥 DÀN KẾT (19s)": sorted(full_ranked[:19]),
                "⭐ DÀN ĐẸP (20s)": sorted(full_ranked[19:39]),
                "💎 TRUNG BÌNH (20s)": sorted(full_ranked[39:59]),
                "🛡️ XÉT LÓT (20s)": sorted(full_ranked[59:79]),
                "🚫 DÀN LOẠI (19s)": sorted(full_ranked[79:])
            }
        else:
            st.warning("Không tìm thấy trạng thái Bit tương tự trong lịch sử.")

    # Hiển thị
    if st.session_state.last_danh_sach:
        for label, s_list in st.session_state.last_danh_sach.items():
            st.markdown(f'<div class="dan-box"><div class="dan-title">{label}</div><div class="dan-content">{" ".join([f"<b>{x:02d}</b>" for x in s_list])}</div></div>', unsafe_allow_html=True)

    # Xuất file
    export = json.dumps({"data": st.session_state.data_list, "history": st.session_state.history_log}, indent=4)
    st.download_button("📥 LƯU DATA", export, "Matrix_V15_6.json", "application/json")
