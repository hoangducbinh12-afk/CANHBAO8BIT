import streamlit as st
import pandas as pd
import numpy as np
import json

# --- 1. CẤU HÌNH GIAO DIỆN PHÁO ĐÀI ---
st.set_page_config(page_title="CANH BAO 8 BIT V11.0", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { color: #000000 !important; background-color: #ffffff !important; font-size: 0.72rem !important; }
    .stButton button { width: 100%; border-radius: 4px; height: 38px; font-weight: 700; background-color: #000080 !important; color: #ffffff !important; }
    div[data-testid="stTextInput"] input { font-size: 1.8rem !important; font-weight: bold !important; color: #ff0000 !important; text-align: center; border: 2px solid #ff0000 !important; }
    .bit-header { background: #000080; color: white; text-align: center; font-weight: bold; border-radius: 3px; margin-bottom: 2px; }
    .bit-card { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 4px; padding: 5px; margin-bottom: 2px; text-align: center; }
    .dan-box { background-color: #f0fdf4; border: 2px solid #16a34a; padding: 15px; font-family: monospace; color: #16a34a; font-weight: bold; text-align: center; font-size: 1.3rem; line-height: 1.8; border-radius: 10px; }
    .kill-box { background-color: #000; color: #ff0000; padding: 10px; border-radius: 5px; font-family: monospace; text-align: center; font-weight: bold; border: 2px solid #ff0000; }
    .info-tag { background: #fffbeb; border-left: 5px solid #f59e0b; padding: 10px; color: #b45309; font-weight: bold; margin-bottom: 10px; font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HÀM LOGIC CỐT LÕI ---
BIT_LABELS = ["Đ.CL", "Đu.CL", "T.CL", "Đ.TB", "Đu.TB", "T.TB", "Hệ", "Hi.TB"]
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]

def get_props(n):
    val = int(n); d, u = val // 10, val % 10
    return d, u, (d + u) % 10, (d - u + 10) % 10

def get_8bit(n):
    val = int(n); d, u = val // 10, val % 10
    t_dv, h_dv = (d + u) % 10, (d - u + 10) % 10
    return [1 if d%2!=0 else 0, 1 if u%2!=0 else 0, 1 if (d+u)%2!=0 else 0, 1 if d>=5 else 0, 1 if u>=5 else 0, 1 if t_dv>=5 else 0, 1 if val in SO_THUONG else 0, 1 if h_dv>=5 else 0]

def analyze_v11(history):
    if len(history) < 35: return None
    
    # BƯỚC 1: Quét 8 biến số đã nổ để tìm Vùng An Toàn & Dàn Xét Loại
    def find_8(idx):
        found = []
        for h in reversed(history):
            p = get_props(h['Số'])[idx]
            if p not in found: found.append(p)
            if len(found) == 8: break
        return set(found)
    
    ve_d, ve_u, ve_t, ve_h = find_8(0), find_8(1), find_8(2), find_8(3)
    thieu_8 = (set(range(10))-ve_d, set(range(10))-ve_u, set(range(10))-ve_t, set(range(10))-ve_h)
    
    # BƯỚC 2: Khung xương 30 kỳ + Nghịch đảo (Giữ chặt)
    skeleton = set()
    for h in history[-30:]:
        s = h['Số']
        skeleton.add(s); skeleton.add(s[::-1])
        
    # BƯỚC 3: Quét 9 kỳ thiếu (Loại cứng 4 cực)
    past_9 = history[-9:]
    t9_d = set(range(10)) - {get_props(h['Số'])[0] for h in past_9}
    t9_u = set(range(10)) - {get_props(h['Số'])[1] for h in past_9}
    t9_t = set(range(10)) - {get_props(h['Số'])[2] for h in past_9}
    t9_h = set(range(10)) - {get_props(h['Số'])[3] for h in past_9}
    
    hard_kill = []
    for i in range(100):
        d, u, t, h = get_props(i)
        if all([d in t9_d, u in t9_u, t in t9_t, h in t9_h]):
            hard_kill.append(f"{i:02d}")

    # BƯỚC 4: Chấm điểm Quantum & Phân tầng
    all_bits = np.array([get_8bit(h["Số"]) for h in history])
    p_hội_tụ = [np.mean(all_bits[-10:, j]) for j in range(8)]
    
    final_scores = []
    for i in range(100):
        s_str = f"{i:02d}"
        d, u, t, h = get_props(i)
        
        # Đếm lỗi (dựa trên Bước 1)
        penalty_count = sum([1 for cond, pool in zip([d,u,t,h], thieu_8) if cond in pool])
        
        # Điểm 8-Bit
        b = get_8bit(i)
        q_score = sum(b[j]*p_hội_tụ[j] + (1-b[j])*(1-p_hội_tụ[j]) for j in range(8))
        
        # TRỌNG SỐ THỨ HẠNG
        m_total = q_score
        # Ưu tiên 1: An toàn 8/10 (0 thuộc tính thiếu)
        if penalty_count == 0: m_total += 500.0
        # Ưu tiên 2: Khung xương 30 kỳ
        if s_str in skeleton: m_total += 300.0
        # Hình phạt: Loại cứng 4 cực
        if s_str in hard_kill: m_total -= 5000.0
        # Hình phạt theo tầng thiếu (4,3,2)
        m_total -= (penalty_count * 50.0)
        
        final_scores.append({"S": s_str, "M": m_total, "Tier": penalty_count})
        
    return final_scores, hard_kill, p_hội_tụ, thieu_8

# --- 3. SESSION & SIDEBAR ---
if 'history' not in st.session_state: st.session_state.history = []
if 'num_quan' not in st.session_state: st.session_state.num_quan = 80

with st.sidebar:
    st.header("⚙️ QUẢN TRỊ V11.0")
    up = st.file_uploader("Nạp Master Data:", type="json")
    if up:
        data = json.load(up); raw = data.get("history", data.get("ls", []))
        st.session_state.history = sorted([{"Kỳ": int(h.get("Kỳ", 0)), "Số": f"{int(h.get('Số', h.get('Số về', 0))):02d}", "Rank": h.get("Rank", 0)} for h in raw], key=lambda x: x["Kỳ"])
    if st.session_state.history:
        js = json.dumps({"history": st.session_state.history}, indent=2)
        st.download_button("💾 XUẤT MASTER", js, "master_v11.json")
    if st.button("🔴 RESET TOÀN BỘ"): st.session_state.history = []; st.rerun()

# --- 4. NHẬP LIỆU GIAO DIỆN ---
st.title("🛡️ 8-BIT V11.0 - QUANTUM SUPREMACY")
c1, c2, c3 = st.columns([1.5, 1, 1.5])
n_in = c1.text_input("SỐ VỪA NỔ (AB):", key="in_so")
ky_curr = int(st.session_state.history[-1]["Kỳ"])+1 if st.session_state.history else 1
ky_in = c2.number_input("KỲ NỔ:", value=ky_curr)

if c3.button("🚀 KÍCH HOẠT PHÂN TÍCH"):
    if n_in:
        val = f"{int(n_in[-2:]):02d}"; r_v = 0
        if len(st.session_state.history) >= 35:
            scored, _, _, _ = analyze_v11(st.session_state.history)
            df_rank = pd.DataFrame(scored).sort_values("M", ascending=False)
            df_rank['Rank'] = range(1, 101)
            r_v = int(df_rank[df_rank['S'] == val]['Rank'].values[0])
        st.session_state.history.append({"Kỳ": int(ky_in), "Số": val, "Rank": r_v}); st.rerun()

# --- 5. HIỂN THỊ KẾT QUẢ ---
if len(st.session_state.history) >= 35:
    scored, hard_kill, probs, thieu_8 = analyze_v11(st.session_state.history)
    
    # Chỉ số 8 Bit
    cols = st.columns(8)
    for i in range(8):
        with cols[i]:
            st.markdown(f"<div class='bit-header'>{BIT_LABELS[i]}</div><div class='bit-card'><b>{int(probs[i]*100)}%</b></div>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown(f"<div class='info-tag'>🔍 4 Cực Thiếu (Quét 8 biến): Đầu {list(thieu_8[0])} | Đuôi {list(thieu_8[1])} | Tổng {list(thieu_8[2])} | Hiệu {list(thieu_8[3])}</div>", unsafe_allow_html=True)
    
    # Máy chém Hard Kill
    if hard_kill:
        st.subheader(f"🔪 LOẠI CỨNG (TỬ HÌNH 4 CỰC): {len(hard_kill)} SỐ")
        st.markdown(f"<div class='kill-box'>{' '.join(hard_kill)}</div>", unsafe_allow_html=True)

    # Thanh lấy số quân & Dàn Rank
    st.divider()
    sl1, sl2 = st.columns([3, 1])
    st.session_state.num_quan = sl1.slider("Thanh trượt lấy số quân (Ưu tiên vùng an toàn & Khung xương):", 40, 95, st.session_state.num_quan)
    
    df_f = pd.DataFrame(scored).sort_values("M", ascending=False)
    dan_rank = df_f.head(st.session_state.num_quan)["S"].tolist()
    
    st.subheader(f"🔥 DÀN {st.session_state.num_quan} QUÂN - THỨ TỰ THEO RANK")
    st.markdown(f"<div class='dan-box'>{' '.join(dan_rank)}</div>", unsafe_allow_html=True)

    # Nhật ký lịch sử đầy đủ
    st.divider()
    st.subheader("📊 NHẬT KÝ LỊCH SỬ CHI TIẾT")
    disp = []
    for h in sorted(st.session_state.history, key=lambda x: x['Kỳ'], reverse=True):
        b = get_8bit(h["Số"]); d, u, t, hi = get_props(h["Số"])
        r_val = h.get("Rank", 0)
        disp.append({"Kỳ": h["Kỳ"], "Số": h["Số"], "Rank": r_val if r_val != 0 else "-", "Đầu": d, "Đuôi": u, "Tổng": t, "Hiệu": hi, "Hệ": "Thuận" if b[6] else "Khác"})
    st.dataframe(pd.DataFrame(disp), use_container_width=True, hide_index=True)
else:
    st.warning("Nạp ít nhất 35 kỳ Master Data để hệ thống thiết lập Pháo đài V11.0.")
