import streamlit as st
import pandas as pd
import numpy as np
import json

# --- 1. GIAO DIỆN PHÁO ĐÀI V11.2 ---
st.set_page_config(page_title="8-BIT V11.2 THE DECISION", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { color: #000000 !important; background-color: #ffffff !important; font-size: 0.75rem !important; }
    .stButton button { width: 100%; border-radius: 4px; height: 38px; font-weight: 700; background-color: #000080 !important; color: #ffffff !important; }
    div[data-testid="stTextInput"] input { font-size: 1.8rem !important; font-weight: bold !important; color: #ff0000 !important; text-align: center; border: 2px solid #ff0000 !important; }
    .bit-header { background: #000080; color: white; text-align: center; font-weight: bold; border-radius: 3px; margin-bottom: 2px; }
    .bit-card { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 4px; padding: 5px; margin-bottom: 2px; text-align: center; }
    .dan-box { background-color: #f0fdf4; border: 2px solid #16a34a; padding: 15px; font-family: monospace; color: #16a34a; font-weight: bold; text-align: center; font-size: 1.3rem; line-height: 1.8; border-radius: 10px; }
    .kill-box { background-color: #000; color: #ff0000; padding: 10px; border-radius: 5px; font-family: monospace; text-align: center; font-weight: bold; border: 2px solid #ff0000; }
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

def analyze_v11_2(history):
    if len(history) < 35: return None
    
    # BƯỚC 1: Quét 8 biến nổ
    def find_8(idx):
        found = []
        for h in reversed(history):
            p = get_props(h['Số'])[idx]
            if p not in found: found.append(p)
            if len(found) == 8: break
        return set(found)
    ve_8 = (find_8(0), find_8(1), find_8(2), find_8(3))
    thieu_8 = (set(range(10))-ve_8[0], set(range(10))-ve_8[1], set(range(10))-ve_8[2], set(range(10))-ve_8[3])
    
    # Vùng an toàn & Khung 30 kỳ (Untouchables)
    skeleton = set()
    for h in history[-30:]:
        s = h['Số']
        skeleton.add(s); skeleton.add(s[::-1])
    
    safe_810 = {f"{i:02d}" for i in range(100) if all(get_props(i)[j] in ve_8[j] for j in range(4))}
    untouchables = safe_810 | skeleton

    # BƯỚC 2: Loại cứng 9 kỳ (4 cực thiếu)
    past_9 = history[-9:]
    t9 = [set(range(10)) - {get_props(h['Số'])[j] for h in past_9} for j in range(4)]
    hard_kill = {f"{i:02d}" for i in range(100) if all(get_props(i)[j] in t9[j] for j in range(4))}

    # BƯỚC 3: 8-BIT QUYẾT ĐỊNH TRONG VÙNG XÉT LOẠI
    all_bits = np.array([get_8bit(h["Số"]) for h in history])
    p_hội_tụ = [np.mean(all_bits[-10:, j]) for j in range(8)]
    
    scored_all = []
    for i in range(100):
        s_str = f"{i:02d}"
        d, u, t, h = get_props(i)
        # Đếm số vị thiếu (Vùng xét loại)
        penalty_tier = sum([1 for cond, pool in zip([d,u,t,h], thieu_8) if cond in pool])
        
        # Chấm điểm 8-bit
        b = get_8bit(i)
        q_score = sum(b[j]*p_hội_tụ[j] + (1-b[j])*(1-p_hội_tụ[j]) for j in range(8))
        
        # LOGIC RANK MỚI:
        final_m = q_score
        if s_str in untouchables: final_m += 100.0 # Ưu tiên nhẹ để 8-bit vẫn có quyền điều phối
        if s_str in hard_kill: final_m -= 1000.0   # Loại cứng tuyệt đối
        
        # Vùng xét loại (Tier 4,3,2): KHÔNG TRỪ ĐIỂM CỐ ĐỊNH. 
        # Để 8-bit (q_score) tự phân loại trong vùng này.
        if penalty_tier >= 2:
            final_m -= 0.1 # Chỉ trừ cực nhẹ để đánh dấu vùng xét loại, quyền sinh sát thuộc về 8-bit

        scored_all.append({"S": s_str, "M": final_m, "Tier": penalty_tier, "Q": q_score})
        
    return scored_all, hard_kill, p_hội_tụ

# --- UI & XỬ LÝ ---
if 'history' not in st.session_state: st.session_state.history = []
with st.sidebar:
    up = st.file_uploader("Nạp Master:", type="json")
    if up:
        data = json.load(up); raw = data.get("history", data.get("ls", []))
        st.session_state.history = [{"Kỳ": int(h.get("Kỳ", 0)), "Số": f"{int(h.get('Số', h.get('Số về', 0))):02d}", "Rank": h.get("Rank", 0)} for h in raw]
    if st.button("🔴 RESET"): st.session_state.history = []; st.rerun()

st.title("🛡️ 8-BIT V11.2 - THE DECISION")
c1, c2, c3 = st.columns([1.5, 1, 1.5])
n_in = c1.text_input("SỐ VỪA NỔ:", key="in_so")
ky_curr = int(st.session_state.history[-1]["Kỳ"])+1 if st.session_state.history else 1
ky_in = c2.number_input("KỲ:", value=ky_curr)

if c3.button("🚀 PHÂN TÍCH"):
    if n_in:
        val = f"{int(n_in[-2:]):02d}"; r_v = 0
        if len(st.session_state.history) >= 35:
            scored, _, _ = analyze_v11_2(st.session_state.history)
            df_rank = pd.DataFrame(scored).sort_values("M", ascending=False)
            df_rank['Rank'] = range(1, 101)
            r_v = int(df_rank[df_rank['S'] == val]['Rank'].values[0])
        st.session_state.history.append({"Kỳ": int(ky_in), "Số": val, "Rank": r_v}); st.rerun()

if len(st.session_state.history) >= 35:
    scored, hard_kill, probs = analyze_v11_2(st.session_state.history)
    cols = st.columns(8); 
    for i in range(8): cols[i].markdown(f"<div class='bit-header'>{BIT_LABELS[i]}</div><div class='bit-card'><b>{int(probs[i]*100)}%</b></div>", unsafe_allow_html=True)
    
    if hard_kill:
        st.subheader(f"🔪 TỬ HÌNH 9 KỲ: {len(hard_kill)} SỐ")
        st.markdown(f"<div class='kill-box'>{' '.join(sorted(list(hard_kill)))}</div>", unsafe_allow_html=True)

    df_f = pd.DataFrame(scored).sort_values("M", ascending=False)
    dan_80 = sorted(df_f.head(80)["S"].tolist())
    st.subheader("🔥 DÀN 80 SỐ (8-BIT QUYẾT ĐỊNH RANK)")
    st.markdown(f"<div class='dan-box'>{' '.join(dan_80)}</div>", unsafe_allow_html=True)

    st.subheader("📊 NHẬT KÝ")
    disp = []
    for h in sorted(st.session_state.history, key=lambda x: x['Kỳ'], reverse=True):
        d, u, t, hi = get_props(h["Số"])
        disp.append({"Kỳ": h["Kỳ"], "Số": h["Số"], "Rank": h.get("Rank", "-"), "Đầu": d, "Đuôi": u, "Tổng": t, "Hiệu": hi})
    st.dataframe(pd.DataFrame(disp), use_container_width=True, hide_index=True)
