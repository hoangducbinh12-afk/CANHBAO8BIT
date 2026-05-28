import streamlit as st
import json
import pandas as pd
from collections import Counter
import re
import numpy as np

# --- 1. CSS CHUẨN MOBILE ---
st.set_page_config(page_title="AI MATRIX PRO V15.8", layout="wide")
st.markdown("""
    <style>
    html, body { font-size: 14px !important; background-color: #f8f9fa; }
    .bit-container { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 10px; }
    .bit-card { background: #000080; color: white; padding: 10px; border-radius: 8px; text-align: center; min-width: 85px; flex-shrink: 0; }
    .bit-val { font-size: 16px; font-weight: bold; color: #00ff00; }
    .dan-box { padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 15px; background: white; }
    .dan-title { font-weight: bold; font-size: 15px; margin-bottom: 8px; }
    .dan-content { line-height: 1.8; font-family: monospace; font-size: 17px; color: #2d3436; }
    .hist-card { background: white; border-left: 5px solid #ddd; padding: 10px; margin-bottom: 5px; border-radius: 4px; font-size: 13px; }
    .win { border-left-color: #28a745; background: #f0fff4; }
    .loss { border-left-color: #dc3545; background: #fff5f5; }
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

# --- 3. UI & STATE ---
if 'data_list' not in st.session_state: st.session_state.data_list = []
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'last_danh_sach' not in st.session_state: st.session_state.last_danh_sach = None
if 'last_num_soi' not in st.session_state: st.session_state.last_num_soi = None

with st.sidebar:
    st.title("⚙️ V15.8 ELITE")
    up = st.file_uploader("Nạp Data", type=['json'])
    if up:
        raw = json.load(up)
        st.session_state.data_list = raw.get('data', [])
        st.session_state.history_log = raw.get('history', [])
        if st.session_state.data_list: st.session_state.last_num_soi = st.session_state.data_list[-1]
    if st.button("🚨 RESET ALL"): st.session_state.clear(); st.rerun()

st.title("🎯 AI MATRIX PRO")

if st.session_state.data_list:
    data = st.session_state.data_list
    
    # Dashboard Nhịp 10 kỳ
    all_bits = np.array([get_8bit(x) for x in data[-10:]])
    probs = np.mean(all_bits, axis=0)
    st.markdown('<div class="bit-container">' + "".join([f'<div class="bit-card"><div>{BIT_LABELS[i]}</div><div class="bit-val">{int(probs[i]*100)}%</div></div>' for i in range(8)]) + '</div>', unsafe_allow_html=True)

    with st.expander("📌 BƯỚC 1: NHẬP KẾT QUẢ", expanded=True):
        c1, c2 = st.columns([2, 1])
        new_res = c1.text_input("GĐB vừa về:", placeholder="Ví dụ: 88")
        if c2.button("XÁC NHẬN") and new_res:
            val = int(new_res[-2:])
            tag = "🚫 DÀN LOẠI"
            if st.session_state.last_danh_sach:
                for label, s_list in st.session_state.last_danh_sach.items():
                    if val in s_list: tag = label; break
            
            st.session_state.history_log.insert(0, {"Kỳ": f"Sau {st.session_state.last_num_soi:02d}", "Về": f"{val:02d}", "Dàn": tag})
            st.session_state.data_list.append(val)
            st.session_state.last_num_soi = val; st.rerun()

    st.write("---")
    current_val = st.number_input("SOI SAU CON SỐ:", 0, 99, value=st.session_state.last_num_soi if st.session_state.last_num_soi is not None else data[-1])
    
    if st.button("🚀 PHÂN TÍCH ELITE (100 KỲ)"):
        current_bit_pattern = get_8bit(current_val)
        follower_bits = []; follower_nums = []
        count = 0
        for i in range(len(data) - 2, -1, -1):
            if get_8bit(data[i]) == current_bit_pattern:
                follower_nums.append(data[i+1])
                follower_bits.append(get_8bit(data[i+1]))
                count += 1
                if count == 100: break
        
        if follower_bits:
            f_bits_arr = np.array(follower_bits)
            target_probs = np.mean(f_bits_arr, axis=0)
            target_pattern = [1 if p >= 0.5 else 0 for p in target_probs]
            
            scores = {}; global_counts = Counter(data); f_num_counts = Counter(follower_nums)
            for i in range(100):
                s = 0
                curr_i_bits = get_8bit(i)
                # ĐIỂM KHỚP BIT (Trọng số cao)
                match_score = sum([target_probs[j] if curr_i_bits[j] == 1 else (1 - target_probs[j]) for j in range(8)])
                s += match_score * 100000 
                
                # ƯU TIÊN SỐ TRÙNG LỊCH SỬ (Nếu nổ trong 100 kỳ mà còn KHỚP BIT thì tặng thêm điểm)
                if i in f_num_counts:
                    s += f_num_counts[i] * 500000
                    # Thưởng thêm nếu con số lịch sử đó TRÙNG THUỘC TÍNH dự báo
                    if curr_i_bits == target_pattern: s += 1000000 
                
                s += global_counts.get(i, 0)
                scores[i] = s
            
            full_ranked = [n for n, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
            st.session_state.last_danh_sach = {
                "🔥 DÀN KẾT (19s)": sorted(full_ranked[:19]), "⭐ DÀN ĐẸP (20s)": sorted(full_ranked[19:39]),
                "💎 TRUNG BÌNH (20s)": sorted(full_ranked[39:59]), "🛡️ XÉT LÓT (20s)": sorted(full_ranked[59:79]),
                "🚫 DÀN LOẠI (19s)": sorted(full_ranked[79:])
            }
            st.session_state.last_num_soi = current_val
        else:
            st.warning("Không đủ dữ liệu 100 lần quét cho trạng thái này.")

    # Hiển thị dàn số
    if st.session_state.last_danh_sach:
        for label, s_list in st.session_state.last_danh_sach.items():
            st.markdown(f'<div class="dan-box"><div class="dan-title">{label}</div><div class="dan-content">{" ".join([f"<b>{x:02d}</b>" for x in s_list])}</div></div>', unsafe_allow_html=True)

    # THỐNG KÊ LỊCH SỬ DÀN ĂN
    if st.session_state.history_log:
        st.write("### 📋 LỊCH SỬ ĐỐI SOÁT DÀN")
        for h in st.session_state.history_log[:10]:
            is_win = "🚫" not in h["Dàn"]
            cls = "win" if is_win else "loss"
            st.markdown(f"""<div class="hist-card {cls}"><b>{h['Kỳ']}</b> ➔ Về: <b>{h['Số']}</b> | <span style="color:{'green' if is_win else 'red'}">{h['Dàn']}</span></div>""", unsafe_allow_html=True)

    export = json.dumps({"data": st.session_state.data_list, "history": st.session_state.history_log}, indent=4)
    st.download_button("📥 LƯU DỮ LIỆU", export, "Matrix_V15_8.json", "application/json")
