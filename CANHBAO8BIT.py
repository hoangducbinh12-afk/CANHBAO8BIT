import streamlit as st
import pandas as pd
import numpy as np
import json

# --- 1. CONFIG & CSS ---
st.set_page_config(page_title="CANH BAO 8 BIT V10.8", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { color: #000000 !important; background-color: #ffffff !important; font-size: 0.72rem !important; }
    .stButton button { width: 100%; border-radius: 4px; height: 38px; font-weight: 700; background-color: #000080 !important; color: #ffffff !important; }
    div[data-testid="stTextInput"] input { font-size: 1.6rem !important; font-weight: bold !important; color: #ff0000 !important; text-align: center; }
    .bit-header { background: #000080; color: white; text-align: center; font-weight: bold; border-radius: 3px; margin-bottom: 2px; }
    .bit-card { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 4px; padding: 5px; margin-bottom: 2px; text-align: center; }
    .dan-box { background-color: #f0fdf4; border: 2px solid #16a34a; padding: 12px; font-family: monospace; color: #16a34a; font-weight: bold; text-align: center; font-size: 1.2rem; line-height: 1.6; }
    .tier-card { padding: 8px; border-radius: 5px; margin-bottom: 5px; font-family: monospace; font-size: 0.8rem; border-left: 4px solid; }
    .tier-4 { background-color: #fef2f2; border-color: #dc2626; color: #991b1b; }
    .tier-3 { background-color: #fff7ed; border-color: #ea580c; color: #9a3412; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CORE LOGIC ---
BIT_LABELS = ["Đ.CL", "Đu.CL", "T.CL", "Đ.TB", "Đu.TB", "T.TB", "Hệ", "Hi.TB"]
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]

def get_props(n):
    val = int(n); d, u = val // 10, val % 10
    return d, u, (d + u) % 10, (d - u + 10) % 10

def get_8bit(n):
    val = int(n); d, u = val // 10, val % 10
    t_dv, h_dv = (d + u) % 10, (d - u + 10) % 10
    return [1 if d%2!=0 else 0, 1 if u%2!=0 else 0, 1 if (d+u)%2!=0 else 0, 1 if d>=5 else 0, 1 if u>=5 else 0, 1 if t_dv>=5 else 0, 1 if val in SO_THUONG else 0, 1 if h_dv>=5 else 0]

def analyze_v10_8(history):
    if len(history) < 20: return None, None, None
    def find_8(idx):
        found = []
        for h in reversed(history):
            p = get_props(h['Số'])[idx]
            if p not in found: found.append(p)
            if len(found) == 8: break
        return set(found)
    ve_d, ve_u, ve_t, ve_h = find_8(0), find_8(1), find_8(2), find_8(3)
    all_dig = set(range(10))
    thieu = (all_dig-ve_d, all_dig-ve_u, all_dig-ve_t, all_dig-ve_h)
    
    all_bits = np.array([get_8bit(h["Số"]) for h in history])
    p_hội_tụ = [np.mean(all_bits[-10:, j]) for j in range(8)]
    
    scored_all = []
    for i in range(100):
        d, u, t, h = get_props(i)
        penalty = sum([1 for cond, pool in zip([d,u,t,h], thieu) if cond in pool])
        b = get_8bit(i)
        m_score = sum(b[j]*p_hội_tụ[j] + (1-b[j])*(1-p_hội_tụ[j]) for j in range(8))
        scored_all.append({"S": f"{i:02d}", "Tier": penalty, "M": m_score})
    return scored_all, thieu, p_hội_tụ

# --- 3. SESSION & SIDEBAR ---
if 'history' not in st.session_state: st.session_state.history = []
if 'num_quan' not in st.session_state: st.session_state.num_quan = 80

with st.sidebar:
    st.header("⚙️ DATA CENTER")
    up = st.file_uploader("Nạp Master:", type="json")
    if up:
        data = json.load(up); raw = data.get("history", data.get("ls", []))
        st.session_state.history = sorted([{"Kỳ": int(h.get("Kỳ", 0)), "Số": f"{int(h.get('Số', h.get('Số về', 0))):02d}", "Rank": h.get("Rank", 0)} for h in raw], key=lambda x: x["Kỳ"])
    if st.button("🔴 RESET"): st.session_state.history = []; st.rerun()

# --- 4. NHẬP LIỆU ---
st.title("🛡️ 8-BIT V10.8 - RANKING SYSTEM")
c1, c2, c3 = st.columns([1.5, 1, 1.5])
n_in = c1.text_input("Số vừa nổ:", key="in_so")
ky_curr = int(st.session_state.history[-1]["Kỳ"])+1 if st.session_state.history else 1
ky_in = c2.number_input("Kỳ:", value=ky_curr)

if c3.button("🚀 PHÂN TÍCH"):
    if n_in:
        val = f"{int(n_in[-2:]):02d}"; r_v = 0
        if len(st.session_state.history) >= 10:
            scored, _, _ = analyze_v10_8(st.session_state.history)
            df_rank = pd.DataFrame(scored).sort_values(["Tier", "M"], ascending=[True, False])
            df_rank['Rank'] = range(1, 101)
            r_v = int(df_rank[df_rank['S'] == val]['Rank'].values[0])
        st.session_state.history.append({"Kỳ": int(ky_in), "Số": val, "Rank": r_v}); st.rerun()

# --- 5. PHÂN TÍCH & HIỂN THỊ DÀN ---
if len(st.session_state.history) >= 10:
    scored, thieu, probs = analyze_v10_8(st.session_state.history)
    
    # 8 Cột chỉ số Bit
    cols = st.columns(8)
    for i in range(8):
        with cols[i]:
            st.markdown(f"<div class='bit-header'>{BIT_LABELS[i]}</div><div class='bit-card'><b>{int(probs[i]*100)}%</b></div>", unsafe_allow_html=True)
    
    st.divider()
    # Thanh lấy số quân
    cl1, cl2 = st.columns([3, 1])
    st.session_state.num_quan = cl1.slider("Thanh lấy số quân (Ưu tiên Rank cao):", 10, 95, st.session_state.num_quan)
    cl2.write(f"### 🔥 {st.session_state.num_quan} SỐ")

    # Xử lý Ranking: Sắp xếp theo Tier (thấp nhất lên đầu) và Score (cao nhất lên đầu)
    df_final = pd.DataFrame(scored).sort_values(["Tier", "M"], ascending=[True, False])
    dan_rank = df_final.head(st.session_state.num_quan)["S"].tolist()
    
    st.markdown(f"<div class='dan-box'>{' '.join(dan_rank)}</div>", unsafe_allow_html=True)

    # Phân tầng để soi
    with st.expander("🕵️ Soi các tầng sát thủ (20% vùng nguy hiểm)"):
        st.markdown(f"<div class='tier-card tier-4'><b>Tầng 4/4 (Chém):</b> {' '.join([x['S'] for x in scored if x['Tier']==4])}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='tier-card tier-3'><b>Tầng 3/4 (Rác):</b> {' '.join([x['S'] for x in scored if x['Tier']==3])}</div>", unsafe_allow_html=True)

    # Nhật ký lịch sử
    st.divider()
    st.subheader("📊 NHẬT KÝ LỊCH SỬ")
    disp = []
    for h in sorted(st.session_state.history, key=lambda x: x['Kỳ'], reverse=True):
        b = get_8bit(h["Số"]); d, u, t, hi = get_props(h["Số"])
        rank_val = h.get("Rank", 0)
        disp.append({"Kỳ": h["Kỳ"], "Số": h["Số"], "Rank": rank_val if rank_val != 0 else "-", "Đầu": d, "Đuôi": u, "Tổng": t, "Hiệu": hi, "Hệ": "Thuận" if b[6] else "Khác"})
    st.dataframe(pd.DataFrame(disp), use_container_width=True, hide_index=True)
else:
    st.warning("Nạp Master Data để bắt đầu.")
