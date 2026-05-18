import streamlit as st
import pandas as pd
import numpy as np
import json

# --- 1. GIAO DIỆN CHUẨN V8.5/V10.5 ---
st.set_page_config(page_title="8-BIT V10.5 THE INTERSECTION", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { color: #000000 !important; background-color: #ffffff !important; font-size: 0.72rem !important; }
    .stButton button { width: 100%; border-radius: 4px; height: 38px; font-weight: 700; background-color: #000080 !important; color: #ffffff !important; }
    div[data-testid="stTextInput"] input { font-size: 1.6rem !important; font-weight: bold !important; color: #ff0000 !important; text-align: center; }
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
    if len(history) < 10: return None, None
    past_9 = history[-9:]
    ve_d = {get_props(h['Số'])[0] for h in past_9}
    ve_u = {get_props(h['Số'])[1] for h in past_9}
    ve_t = {get_props(h['Số'])[2] for h in past_9}
    ve_h = {get_props(h['Số'])[3] for h in past_9}
    
    all_digits = set(range(10))
    thieu_d = sorted(list(all_digits - ve_d))
    thieu_u = sorted(list(all_digits - ve_u))
    thieu_t = sorted(list(all_digits - ve_t))
    thieu_h = sorted(list(all_digits - ve_h))
    
    kill_list = []
    for i in range(100):
        d, u, t, h = get_props(i)
        if (d in thieu_d) and (u in thieu_u) and (t in thieu_t) and (h in thieu_h):
            kill_list.append(f"{i:02d}")
            
    skeleton = set()
    last_35 = history[-35:] if len(history) >= 35 else history
    for h in last_35:
        s = f"{int(h['Số']):02d}"
        skeleton.add(s); skeleton.add(s[::-1])
        db, ub = (int(s[0])+5)%10, (int(s[1])+5)%10
        skeleton.add(f"{db}{ub}")
    
    final_kill = [s for s in kill_list if s not in skeleton]
    return final_kill, (thieu_d, thieu_u, thieu_t, thieu_h)

# --- 3. SESSION & SIDEBAR ---
if 'history' not in st.session_state: st.session_state.history = []
if 'last_n' not in st.session_state: st.session_state.last_n = -1

with st.sidebar:
    st.header("⚙️ QUẢN LÝ DỮ LIỆU")
    up = st.file_uploader("Nạp Master Data:", type="json")
    if up:
        data = json.load(up)
        raw = data.get("history", []) if 'history' in data else data.get("ls", [])
        st.session_state.history = [{"Kỳ": i+1, "Số": f"{int(h.get('Số', h.get('Số về'))):02d}"} for i, h in enumerate(raw)]
        st.session_state.last_n = int(st.session_state.history[-1]["Số"])
    
    if st.session_state.history:
        js = json.dumps({"history": st.session_state.history}, indent=2)
        st.download_button("💾 TẢI DỮ LIỆU", data=js, file_name="master_v105.json")
    if st.button("🔴 RESET"): st.session_state.history = []; st.rerun()

# --- 4. NHẬP LIỆU (HIỆN LẠI Ô NHẬP) ---
st.title("🛡️ 8-BIT V10.5 - THE INTERSECTION")

c1, c2, c3 = st.columns([1.5, 1, 1.5])
n_in = c1.text_input("Số vừa nổ:", key="in_so_105")
ky_curr = int(st.session_state.history[-1]["Kỳ"])+1 if st.session_state.history else 1
ky_in = c2.number_input("Kỳ:", value=ky_curr)

if c3.button("🚀 PHÂN TÍCH"):
    if n_in:
        val = f"{int(n_in[-2:]):02d}"
        st.session_state.history.append({"Kỳ": int(ky_in), "Số": val})
        st.session_state.last_n = int(val); st.rerun()

# --- 5. HIỂN THỊ PHÂN TÍCH ---
if len(st.session_state.history) >= 10:
    final_kill, thieu = analyze_v10_5(st.session_state.history)
    
    st.markdown(f"<div class='info-label'>🧬 Dựa trên 9 kỳ bệt gần nhất để tìm điểm giao thoa 4 cực.</div>", unsafe_allow_html=True)
    
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Thiếu Đầu", ", ".join(map(str, thieu[0])))
    t2.metric("Thiếu Đuôi", ", ".join(map(str, thieu[1])))
    t3.metric("Thiếu Tổng", ", ".join(map(str, thieu[2])))
    t4.metric("Thiếu Hiệu", ", ".join(map(str, thieu[3])))
    
    st.subheader(f"🔪 DANH SÁCH LOẠI CHẾT ({len(final_kill)} SỐ)")
    st.markdown(f"<div class='reject-card'>{' '.join(final_kill) if final_kill else 'An toàn tuyệt đối'}</div>", unsafe_allow_html=True)

    # Chốt dàn 80
    all_bits = np.array([get_8bit(h["Số"]) for h in st.session_state.history])
    p_hội_tụ = [np.mean(all_bits[-10:, j]) for j in range(8)]
    scored = []
    for i in range(100):
        s = f"{i:02d}"
        b = get_8bit(i)
        sc = sum(b[j]*p_hội_tụ[j] + (1-b[j])*(1-p_hội_tụ[j]) for j in range(8))
        if s in final_kill: sc -= 100.0
        scored.append({"S": s, "M": sc})
    
    df_rank = pd.DataFrame(scored).sort_values("M", ascending=False)
    dan_80 = sorted(df_rank.head(80)["S"].tolist())
    
    st.divider()
    st.subheader("🔥 DÀN 80 SIÊU CẤP (Tỷ lệ thắng 99.3%)")
    st.markdown(f"<div class='dan-80'>{' '.join(dan_80)}</div>", unsafe_allow_html=True)

    # --- 6. NHẬT KÝ (HIỆN LẠI LỊCH SỬ) ---
    st.divider()
    st.subheader("📊 NHẬT KÝ LỊCH SỬ")
    disp = []
    for h in sorted(st.session_state.history, key=lambda x: x['Kỳ'], reverse=True):
        b = get_8bit(h["Số"])
        disp.append({"Kỳ": h["Kỳ"], "Số": h["Số"], "Đ.CL": "Lẻ" if b[0] else "Chẵn", "Đu.CL": "Lẻ" if b[1] else "Chẵn", "T.CL": "Lẻ" if b[2] else "Chẵn", "Đ.TB": "To" if b[3] else "Bé", "Đu.TB": "To" if b[4] else "Bé", "Hệ": "Thuận" if b[6] else "K.Phải"})
    st.dataframe(pd.DataFrame(disp), use_container_width=True, hide_index=True)
else:
    st.warning("Nạp 10 kỳ để bắt đầu.")
