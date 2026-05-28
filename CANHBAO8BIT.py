import streamlit as st
import json
import pandas as pd
from collections import Counter
import re
import numpy as np

# --- 1. CẤU HÌNH GIAO DIỆN CHUẨN MOBILE ---
st.set_page_config(page_title="AI MATRIX PRO V15.5", layout="wide")

st.markdown("""
    <style>
    /* Tối ưu hóa cho màn hình nhỏ */
    html, body { font-size: 14px !important; background-color: #f8f9fa; }
    .main .block-container { padding: 1rem !important; }
    
    /* Dashboard Bit - Cuộn ngang trên mobile */
    .bit-container { 
        display: flex; gap: 8px; overflow-x: auto; padding-bottom: 10px;
        scrollbar-width: none; -ms-overflow-style: none;
    }
    .bit-container::-webkit-scrollbar { display: none; }
    .bit-card { 
        background: #000080; color: white; padding: 10px; border-radius: 8px; 
        text-align: center; min-width: 75px; flex-shrink: 0;
    }
    .bit-val { font-size: 16px; font-weight: bold; color: #00ff00; }
    
    /* Dàn số Card */
    .dan-box { 
        padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; 
        margin-bottom: 15px; background: white; 
    }
    .dan-title { font-weight: bold; font-size: 15px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
    .dan-content { line-height: 1.8; font-family: monospace; font-size: 17px; color: #2d3436; }
    
    /* Thẻ lịch sử gọn */
    .hist-card {
        background: white; border-left: 5px solid #ddd; padding: 10px;
        margin-bottom: 8px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .hist-win { border-left-color: #2ecc71 !important; background: #fafffb; }
    .hist-loss { border-left-color: #e74c3c !important; background: #fffafa; }

    /* Nút bấm to cho mobile */
    div.stButton > button { 
        width: 100%; height: 3.8em; border-radius: 10px; 
        font-weight: bold; font-size: 15px; background: #FF4B4B; color: white; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM LOGIC ---
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
    return ((d + 5) % 10) * 10 + ((u + 5) % 10)

# --- 3. QUẢN LÝ STATE ---
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'data_list' not in st.session_state: st.session_state.data_list = []
if 'last_danh_sach' not in st.session_state: st.session_state.last_danh_sach = None
if 'last_num_soi' not in st.session_state: st.session_state.last_num_soi = None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ HỆ THỐNG")
    up_file = st.file_uploader("Nạp Data", type=['json'])
    if up_file:
        raw = json.load(up_file)
        st.session_state.data_list = raw.get('data', [])
        st.session_state.history_log = raw.get('history', [])
        st.success("Đã nạp dữ liệu!")
    
    if st.button("🚨 RESET ALL"):
        st.session_state.clear(); st.rerun()

# --- 5. GIAO DIỆN CHÍNH ---
st.title("🎯 AI MATRIX PRO")

if st.session_state.data_list:
    data = st.session_state.data_list
    
    # Dashboard 8-Bit Mobile
    all_bits = np.array([get_8bit(x) for x in data[-10:]])
    probs = np.mean(all_bits, axis=0)
    st.markdown('<div class="bit-container">' + "".join([
        f'<div class="bit-card"><div>{BIT_LABELS[i]}</div><div class="bit-val">{int(probs[i]*100)}%</div></div>' 
        for i in range(8)]) + '</div>', unsafe_allow_html=True)

    # Nhập số vừa về
    with st.expander("📌 BƯỚC 1: CẬP NHẬT KẾT QUẢ", expanded=True):
        c1, c2 = st.columns([2, 1])
        new_res = c1.text_input("GĐB vừa nổ:", placeholder="Ví dụ: 50")
        if c2.button("XÁC NHẬN") and new_res:
            val = int(new_res[-2:])
            tag = "❌ Loại"
            if st.session_state.last_danh_sach:
                for label, s_list in st.session_state.last_danh_sach.items():
                    if val in s_list: tag = label; break
            
            st.session_state.history_log.insert(0, {
                "Kỳ": f"Sau {st.session_state.last_num_soi:02d}" if st.session_state.last_num_soi is not None else "---",
                "Số": f"{val:02d}",
                "Kết quả": tag
            })
            st.session_state.data_list.append(val)
            st.rerun()

    # Phân tích
    st.write("---")
    num_soi = st.number_input("SOI SAU CON SỐ:", 0, 99, value=data[-1])

    if st.button("🔥 PHÂN TÍCH MA TRẬN"):
        # Logic Scoring chuyên gia
        global_counts = Counter(data)
        indices = [i for i, x in enumerate(data[:-1]) if x == num_soi]
        followers = [data[i+1] for i in indices]
        after_counts = Counter(followers)
        
        # Nhịp Bit mục tiêu
        if followers:
            f_bits = np.array([get_8bit(x) for x in followers])
            target_pattern = [1 if np.mean(f_bits[:, j]) >= 0.5 else 0 for j in range(8)]
        else:
            target_pattern = [1 if p >= 0.5 else 0 for p in probs]

        scores = {}
        for i in range(100):
            s = 0
            if i in after_counts: s += after_counts[i] * 10000000
            rev = (i % 10 * 10) + (i // 10)
            if rev in after_counts: s += after_counts[rev] * 50000
            if get_bóng(i) in after_counts: s += after_counts[get_bóng(i)] * 10000
            
            # Bit Match
            curr_bits = get_8bit(i)
            s += sum(1 for a, b in zip(curr_bits, target_pattern) if a == b) * 5000
            s += global_counts.get(i, 0)
            scores[i] = s

        full_ranked = [n for n, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
        st.session_state.last_danh_sach = {
            "🔥 DÀN KẾT": sorted(full_ranked[:19]),
            "⭐ DÀN ĐẸP": sorted(full_ranked[19:39]),
            "💎 TRUNG BÌNH": sorted(full_ranked[39:59]),
            "🛡️ XÉT LÓT": sorted(full_ranked[59:79]),
            "🚫 DÀN LOẠI": sorted(full_ranked[79:])
        }
        st.session_state.last_num_soi = num_soi

    # HIỂN THỊ DÀN SỐ
    if st.session_state.last_danh_sach:
        ds = st.session_state.last_danh_sach
        colors = ["#FF4B4B", "#FFA500", "#1C83E1", "#28A745", "#6C757D"]
        for i, (label, s_list) in enumerate(ds.items()):
            st.markdown(f"""
                <div class="dan-box">
                    <div class="dan-title" style="color:{colors[i]};">{label}</div>
                    <div class="dan-content">{' '.join([f"<b>{x:02d}</b>" for x in s_list])}</div>
                </div>
            """, unsafe_allow_html=True)

    # LỊCH SỬ MOBILE STYLE
    if st.session_state.history_log:
        st.write("---")
        st.subheader("📋 LỊCH SỬ ĐỐI SOÁT")
        for h in st.session_state.history_log[:15]: # Hiển thị 15 kỳ gần nhất
            is_win = " Loại" not in h["Kết quả"]
            win_class = "hist-win" if is_win else "hist-loss"
            st.markdown(f"""
                <div class="hist-card {win_class}">
                    <div style="display:flex; justify-content:space-between;">
                        <span><b>{h['Kỳ']}</b> ➔ Về: <b style="font-size:16px;">{h['Số']}</b></span>
                        <span style="color:{'#2ecc71' if is_win else '#e74c3c'}; font-weight:bold;">{h['Kết quả']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Xuất file
    st.divider()
    export = json.dumps({"data": st.session_state.data_list, "history": st.session_state.history_log}, indent=4)
    st.download_button("📥 LƯU DỮ LIỆU (.JSON)", export, "Matrix_Pro_V15.json", "application/json")
else:
    st.warning("👋 Hãy nạp dữ liệu ở Sidebar để bắt đầu.")
