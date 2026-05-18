import streamlit as st
import pandas as pd
import numpy as np
import json

# --- 1. GIAO DIỆN PHÁO ĐÀI ---
st.set_page_config(page_title="8-BIT V10.7 TIER FILTER", layout="wide")
st.markdown("""
    <style>
    .stButton button { background-color: #000080 !important; color: white !important; font-weight: bold; }
    .tier-card { padding: 10px; border-radius: 5px; margin-bottom: 5px; font-family: monospace; }
    .tier-4 { background-color: #450a0a; color: #fca5a5; border: 1px solid #ef4444; } /* Đỏ đậm */
    .tier-3 { background-color: #78350f; color: #fcd34d; border: 1px solid #f59e0b; } /* Cam đậm */
    .tier-2 { background-color: #1e3a8a; color: #bfdbfe; border: 1px solid #3b82f6; } /* Xanh đậm */
    .dan-80 { background-color: #f0fdf4; border: 2px solid #16a34a; padding: 10px; color: #16a34a; font-weight: bold; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CORE LOGIC ---
def get_props(n):
    val = int(n); d, u = val // 10, val % 10
    return d, u, (d + u) % 10, (d - u + 10) % 10

def analyze_v10_7(history):
    if len(history) < 20: return None
    
    # BƯỚC 1: Tìm 8 biến số đã về gần nhất
    def find_8(idx):
        found = []
        for h in reversed(history):
            p = get_props(h['Số'])[idx]
            if p not in found: found.append(p)
            if len(found) == 8: break
        return set(found)

    ve_d, ve_u, ve_t, ve_h = find_8(0), find_8(1), find_8(2), find_8(3)
    all_dig = set(range(10))
    thieu_d, thieu_u, thieu_t, thieu_h = all_dig-ve_d, all_dig-ve_u, all_dig-ve_t, all_dig-ve_h
    
    # BƯỚC 2: Phân tầng 100 số
    scored_list = []
    for i in range(100):
        d, u, t, h = get_props(i)
        penalty = 0
        if d in thieu_d: penalty += 1
        if u in thieu_u: penalty += 1
        if t in thieu_t: penalty += 1
        if h in thieu_h: penalty += 1
        
        # Lấy điểm 8-bit bổ trợ (từ bản cũ)
        # Giả lập điểm nhịp để làm tiêu chí phụ khi cùng Tier
        scored_list.append({"S": f"{i:02d}", "Tier": penalty})
        
    return scored_list, (thieu_d, thieu_u, thieu_t, thieu_h)

# --- 3. UI & DISPLAY ---
if 'history' not in st.session_state: st.session_state.history = []

with st.sidebar:
    st.header("⚙️ DATA V10.7")
    up = st.file_uploader("Nạp Master:", type="json")
    if up:
        data = json.load(up); raw = data.get("history", data.get("ls", []))
        st.session_state.history = [{"Kỳ": i, "Số": f"{int(h.get('Số', h.get('Số về'))):02d}"} for i, h in enumerate(raw)]

st.title("🛡️ 8-BIT V10.7 - THE TIER FILTER")

if len(st.session_state.history) >= 10:
    scored_list, thieu = analyze_v10_7(st.session_state.history)
    
    # Hiển thị các tầng sát thủ
    t4 = [x['S'] for x in scored_list if x['Tier'] == 4]
    t3 = [x['S'] for x in scored_list if x['Tier'] == 3]
    t2 = [x['S'] for x in scored_list if x['Tier'] == 2]
    t1 = [x['S'] for x in scored_list if x['Tier'] == 1]
    t0 = [x['S'] for x in scored_list if x['Tier'] == 0] # Vùng an toàn

    st.subheader("🕵️ PHÂN TẦNG XÉT LOẠI")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='tier-card tier-4'><b>Tầng 4/4 (Loại ngay):</b><br>{' '.join(t4) if t4 else 'Trống'}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='tier-card tier-3'><b>Tầng 3/4 (Ưu tiên loại):</b><br>{' '.join(t3) if t3 else 'Trống'}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='tier-card tier-2'><b>Tầng 2/4 (Xét loại):</b><br>{' '.join(t2) if t2 else 'Trống'}</div>", unsafe_allow_html=True)

    # Lập dàn 80
    # Ưu tiên giữ Tier 0, Tier 1. Sau đó đến Tier 2 cho đến khi đủ 80.
    # Loại từ Tier 4 -> Tier 3 -> Tier 2.
    all_sorted = sorted(scored_list, key=lambda x: x['Tier']) # Thằng Tier thấp nằm trên
    dan_80 = sorted([x['S'] for x in all_sorted[:80]])
    loai_20 = sorted([x['S'] for x in all_sorted[80:]])

    st.divider()
    st.subheader(f"🔥 DÀN 80 CHIẾN THUẬT (Loại {len(loai_20)} số rác nhất)")
    st.markdown(f"<div class='dan-80'>{' '.join(dan_80)}</div>", unsafe_allow_html=True)
    
    with st.expander("📝 Danh sách 20 số đã bị thanh lọc"):
        st.write(" ".join(loai_20))
else:
    st.warning("Cần nạp data.")
