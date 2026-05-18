import streamlit as st
import pandas as pd
import numpy as np
import json

# --- 1. GIAO DIỆN V9.1 (GIỮ NGUYÊN V8.5 + THÊM HIỂN THỊ) ---
st.set_page_config(page_title="8-BIT QUANTUM V9.1", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { color: #000000 !important; background-color: #ffffff !important; font-size: 0.72rem !important; }
    .stButton button { 
        width: 100%; border-radius: 4px; height: 38px; font-weight: 700; 
        background-color: #000080 !important; color: #ffffff !important;
    }
    .dan-box { 
        background-color: #f1f5f9; border: 1px solid #000080; border-radius: 5px; 
        padding: 8px; font-family: monospace; font-weight: 700; color: #000080; text-align: center; font-size: 1rem;
    }
    .bit-card {
        background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 5px;
        padding: 4px; margin-bottom: 2px; line-height: 1.1;
    }
    .bit-header { background: #000080; color: white; text-align: center; font-weight: bold; border-radius: 3px; margin-bottom: 2px; }
    .alert-gan { color: #7c3aed; font-weight: bold; font-size: 0.75rem; border: 1px solid #7c3aed; padding: 2px; border-radius: 3px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CORE LOGIC V9.1 ---
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]
BIT_LABELS = ["Đ.CL", "Đu.CL", "T.CL", "Đ.TB", "Đu.TB", "T.TB", "Hệ", "Hi.TB"]

def get_8bit(n):
    val = int(n); d, u = val // 10, val % 10
    return [1 if d % 2 != 0 else 0, 1 if u % 2 != 0 else 0, 1 if (d+u) % 2 != 0 else 0,
            1 if d >= 5 else 0, 1 if u >= 5 else 0, 1 if (d+u) % 10 >= 5 else 0,
            1 if val in SO_THUONG else 0, 1 if (d-u+10) % 10 >= 5 else 0]

def get_8bit_str(n):
    return "".join(map(str, get_8bit(n)))

def analyze_v91(history, last_n):
    if len(history) < 10: return None
    all_bits = np.array([get_8bit(h["Số"]) for h in history])
    curr_bits = np.array(get_8bit(last_n))
    
    # 1. TÍNH GAN CỤM (CHO 44 DẠNG BIT)
    bit_history_str = ["".join(map(str, b)) for b in all_bits]
    cluster_gan = {}
    for i in range(100):
        s_bit = get_8bit_str(i)
        try:
            last_idx = len(bit_history_str) - 1 - bit_history_str[::-1].index(s_bit)
            cluster_gan[s_bit] = len(bit_history_str) - 1 - last_idx
        except ValueError:
            cluster_gan[s_bit] = len(bit_history_str)

    results = []
    L11, L22, L66 = 11, 22, 66
    for i in range(8):
        s4 = "".join(map(str, all_bits[-4:, i].astype(int)))
        m4 = [all_bits[k+4, i] for k in range(len(all_bits)-5) if "".join(map(str, all_bits[k:k+4, i].astype(int))) == s4]
        p4 = np.mean(m4[-L11:]) if len(m4) > 0 else 0.5

        s3 = "".join(map(str, all_bits[-3:, i].astype(int)))
        m3 = [all_bits[k+3, i] for k in range(len(all_bits)-4) if "".join(map(str, all_bits[k:k+3, i].astype(int))) == s3]
        p3 = np.mean(m3[-L22:]) if len(m3) > 0 else 0.5

        pm_pair = []
        for j in range(8):
            if i == j: continue
            matches = [all_bits[k+1, i] for k in range(len(all_bits)-1) if all_bits[k, i] == curr_bits[i] and all_bits[k, j] == curr_bits[j]]
            pm_pair.extend(matches[-L66:])
        p_base = np.mean(pm_pair) if len(pm_pair) > 0 else 0.5
        p_mom = np.mean(all_bits[-10:, i])

        f_prob = (p4 * 0.40) + (p_mom * 0.20) + (p3 * 0.20) + (p_base * 0.20)
        results.append({"l": BIT_LABELS[i], "f": f_prob, "p4": p4, "p3": p3, "p_base": p_base, "p_mom": p_mom, "c4": len(m4[-L11:]), "c3": len(m3[-L22:]), "c_base": len(pm_pair)})
        
    return results, cluster_gan

# --- 3. SESSION STATE ---
if 'history' not in st.session_state: st.session_state.history = []
if 'last_n' not in st.session_state: st.session_state.last_n = -1
if 'num_quan' not in st.session_state: st.session_state.num_quan = 59

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("📂 HỆ THỐNG V9.1")
    up = st.file_uploader("Nạp Master Data:", type="json")
    if up:
        data = json.load(up); raw = data.get("history", [])
        st.session_state.history = sorted([{"Kỳ": int(h["Kỳ"]), "Số": f"{int(h['Số']):02d}", "Rank": int(h.get("Rank", 0))} for h in raw], key=lambda x: x["Kỳ"])
        st.session_state.last_n = int(st.session_state.history[-1]["Số"])
    if st.button("🔴 RESET"):
        st.session_state.history = []; st.rerun()

# --- 5. GIAO DIỆN ---
st.title("🛡️ 8-BIT QUANTUM V9.1 - CANH BAO CỤM")

if st.session_state.history:
    results, cluster_gan = analyze_v91(st.session_state.history, st.session_state.last_n)
    
    # Nhập liệu
    c1, c2, c3 = st.columns([1.5, 1, 1.5])
    n_in = c1.text_input("Số vừa nổ:")
    ky_in = c2.number_input("Kỳ:", value=int(st.session_state.history[-1]["Kỳ"])+1)
    if c3.button("🚀 PHÂN TÍCH"):
        if n_in:
            val = int(n_in[-2:]); probs = [r["f"] for r in results]
            # Tính Rank dựa trên Hội tụ + Thưởng điểm cho cụm Gan
            scr = []
            for i in range(100):
                s_bit = get_8bit_str(i); b = get_8bit(i)
                m_score = sum(b[j]*probs[j] + (1-b[j])*(1-probs[j]) for j in range(8))
                # THƯỞNG ĐIỂM GAN: Nếu cụm gan > 10 ngày, ưu tiên hạ Rank
                bonus = 0.05 * (cluster_gan[s_bit] / 20) 
                scr.append({"S": f"{i:02d}", "M": m_score + bonus})
            df_t = pd.DataFrame(scr).sort_values("M", ascending=False); df_t['R'] = range(1, 101)
            r_v = df_t[df_t['S'] == f"{val:02d}"]['R'].values[0]
            st.session_state.history.append({"Kỳ": int(ky_in), "Số": f"{val:02d}", "Rank": r_v})
            st.session_state.last_n = val; st.rerun()

    tab1, tab2 = st.tabs(["🎯 PHÂN TÍCH & DÀN", "📊 NHẬT KÝ ĐẦY ĐỦ"])
    with tab1:
        # Hiển thị 8 Bit (Giữ nguyên V8.5)
        cols = st.columns(8)
        for i, r in enumerate(results):
            with cols[i]:
                st.markdown(f"""
                <div class='bit-header'>{BIT_LABELS[i]}</div>
                <div class='bit-card'><b>4K:</b> {int(r['p4']*100)}% <br><small>Mẫu:{r['c4']}</small></div>
                <div class='bit-card'><b>3K:</b> {int(r['p3']*100)}% <br><small>Mẫu:{r['c3']}</small></div>
                <div class='bit-card'><b>10K:</b> {int(r['p_mom']*100)}%</div>
                <div class='bit-card'><b>Hậu:</b> {int(r['p_base']*100)}% <br><small>Mẫu:{r['c_base']}</small></div>
                <div class='bit-card' style='background:#f1f5f9; border: 1px solid #000080'><b>Hội tụ: {int(r['f']*100)}%</b></div>
                """, unsafe_allow_html=True)
        
        # Hiển thị Dàn
        st.divider()
        probs = [r["f"] for r in results]
        final_list = []
        for i in range(100):
            s_bit = get_8bit_str(i); b = get_8bit(i)
            m_score = sum(b[j]*probs[j] + (1-b[j])*(1-probs[j]) for j in range(8))
            bonus = 0.05 * (cluster_gan[s_bit] / 20) # Bonus nhẹ cho cụm gan
            final_list.append({"S": f"{i:02d}", "M": m_score + bonus, "Gan": cluster_gan[s_bit]})
        
        df_rank = pd.DataFrame(final_list).sort_values("M", ascending=False)
        ca, cb = st.columns([2, 1])
        st.session_state.num_quan = cb.number_input("Số quân:", value=st.session_state.num_quan)
        ca.markdown(f"### 🔥 DÀN TINH ANH {int(st.session_state.num_quan)} SỐ")
        st.markdown(f"<div class='dan-box'>{' '.join(df_rank.head(int(st.session_state.num_quan))['S'].tolist())}</div>", unsafe_allow_html=True)
        
        # Cảnh báo Gan cụm
        top_gan_clusters = df_rank.sort_values("Gan", ascending=False).head(5)
        st.markdown("#### 🚨 CẢNH BÁO CỤM BIT ĐANG GAN")
        g_cols = st.columns(5)
        for idx, row in enumerate(top_gan_clusters.itertuples()):
            g_cols[idx].markdown(f"<div class='alert-gan'>Số {row.S}: Gan {row.Gan} kỳ</div>", unsafe_allow_html=True)

    with tab2:
        disp = []
        for h in sorted(st.session_state.history, key=lambda x: x['Kỳ'], reverse=True):
            b = get_8bit(h["Số"])
            disp.append({"Kỳ": h["Kỳ"], "Số": h["Số"], "Rank": h["Rank"], "Đ.CL": "Lẻ" if b[0] else "Chẵn", "Đu.CL": "Lẻ" if b[1] else "Chẵn", "T.CL": "Lẻ" if b[2] else "Chẵn", "Đ.TB": "To" if b[3] else "Bé", "Đu.TB": "To" if b[4] else "Bé", "T.TB": "To" if b[5] else "Bé", "Hệ": "Thuận" if b[6] else "K.Phải", "Hiệu": "To" if b[7] else "Bé"})
        st.dataframe(pd.DataFrame(disp), use_container_width=True, hide_index=True)
