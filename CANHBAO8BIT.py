import streamlit as st
import pandas as pd
import numpy as np
import json

# --- 1. GIAO DIỆN V9.2 (GIỮ V8.5 + THÊM RADAR & CLUSTER) ---
st.set_page_config(page_title="CANH BAO 8 BIT V9.2", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { color: #000000 !important; background-color: #ffffff !important; font-size: 0.75rem !important; }
    .stButton button { 
        width: 100%; border-radius: 4px; height: 38px; font-weight: 700; 
        background-color: #000080 !important; color: #ffffff !important;
    }
    .dan-box { 
        background-color: #f1f5f9; border: 1px solid #000080; border-radius: 5px; 
        padding: 10px; font-family: monospace; font-weight: 700; color: #000080; text-align: center; font-size: 1.1rem;
    }
    .bit-header { background: #000080; color: white; text-align: center; font-weight: bold; border-radius: 3px; margin-bottom: 2px; }
    .bit-card { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 4px; padding: 5px; margin-bottom: 2px; line-height: 1.2; }
    .status-safe { background-color: #d1fae5; border-left: 5px solid #10b981; padding: 10px; color: #065f46; font-weight: bold; border-radius: 5px; }
    .status-chaos { background-color: #fee2e2; border-left: 5px solid #ef4444; padding: 10px; color: #991b1b; font-weight: bold; border-radius: 5px; }
    .cluster-card { border: 1px solid #7c3aed; padding: 8px; border-radius: 5px; background: #f5f3ff; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CORE LOGIC ---
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]
BIT_LABELS = ["Đ.CL", "Đu.CL", "T.CL", "Đ.TB", "Đu.TB", "T.TB", "Hệ", "Hi.TB"]

def get_8bit(n):
    val = int(n); d, u = val // 10, val % 10
    return [1 if d % 2 != 0 else 0, 1 if u % 2 != 0 else 0, 1 if (d+u) % 2 != 0 else 0,
            1 if d >= 5 else 0, 1 if u >= 5 else 0, 1 if (d+u) % 10 >= 5 else 0,
            1 if val in SO_THUONG else 0, 1 if (d-u+10) % 10 >= 5 else 0]

def get_8bit_str(n): return "".join(map(str, get_8bit(n)))

def analyze_v92(history, last_n):
    if len(history) < 15: return None, None, None, None
    all_bits = np.array([get_8bit(h["Số"]) for h in history])
    curr_bits = np.array(get_8bit(last_n))
    
    # Chaos Detection (Ý tưởng 3)
    ranks = [h.get("Rank", 50) for h in history[-10:]]
    entropy = np.std(ranks)
    is_chaotic = entropy > 22 or np.mean(ranks) > 60

    # Bit Resonance (Ý tưởng 2)
    recent_10 = all_bits[-10:]
    bit_resonance = [abs(np.mean(recent_10[:, i]) - 0.5) * 2 for i in range(8)]

    # Tính Gan cho 44 Cụm Bit
    bit_history_str = ["".join(map(str, b)) for b in all_bits]
    unique_clusters = {}
    for i in range(100):
        s_bit = get_8bit_str(i)
        if s_bit not in unique_clusters: unique_clusters[s_bit] = []
        unique_clusters[s_bit].append(f"{i:02d}")
    
    cluster_gan_data = []
    for s_bit, members in unique_clusters.items():
        try:
            last_idx = len(bit_history_str) - 1 - bit_history_str[::-1].index(s_bit)
            gan_days = len(bit_history_str) - 1 - last_idx
        except ValueError: gan_days = len(bit_history_str)
        cluster_gan_data.append({"bit": s_bit, "members": members, "gan": gan_days})

    # Tính Hội tụ (Mỏ neo 66-22-11)
    results = []
    for i in range(8):
        res_w = bit_resonance[i]
        # Nhịp 4K (11m)
        s4 = "".join(map(str, all_bits[-4:, i].astype(int)))
        m4 = [all_bits[k+4, i] for k in range(len(all_bits)-5) if "".join(map(str, all_bits[k:k+4, i].astype(int))) == s4]
        p4 = np.mean(m4[-11:]) if len(m4) > 0 else 0.5
        # Nhịp 3K (22m)
        s3 = "".join(map(str, all_bits[-3:, i].astype(int)))
        m3 = [all_bits[k+3, i] for k in range(len(all_bits)-4) if "".join(map(str, all_bits[k:k+3, i].astype(int))) == s3]
        p3 = np.mean(m3[-22:]) if len(m3) > 0 else 0.5
        # Đối trọng 66m
        pm = []
        for j in range(8):
            if i==j: continue
            matches = [all_bits[k+1, i] for k in range(len(all_bits)-1) if all_bits[k, i] == curr_bits[i] and all_bits[k, j] == curr_bits[j]]
            pm.extend(matches[-66:])
        pb = np.mean(pm) if len(pm) > 0 else 0.5
        # Tổng hợp trọng số linh hoạt
        f_prob = (p4 * 0.4) + (p3 * 0.2) + (pb * 0.2) + (np.mean(all_bits[-10:, i]) * 0.2)
        results.append({"l": BIT_LABELS[i], "f": f_prob, "p4": p4, "p3": p3, "pb": pb, "c4": len(m4[-11:]), "c3": len(m3[-22:]), "cb": len(pm)})
        
    return results, is_chaotic, cluster_gan_data, entropy

# --- 3. SESSION ---
if 'history' not in st.session_state: st.session_state.history = []
if 'last_n' not in st.session_state: st.session_state.last_n = -1

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ V9.2 CONFIG")
    up = st.file_uploader("Nạp Master:", type="json")
    if up:
        data = json.load(up); raw = data.get("history", [])
        st.session_state.history = sorted([{"Kỳ": int(h["Kỳ"]), "Số": f"{int(h['Số']):02d}", "Rank": int(h.get("Rank", 0))} for h in raw], key=lambda x: x["Kỳ"])
        st.session_state.last_n = int(st.session_state.history[-1]["Số"])
    if st.button("🔴 RESET"): st.session_state.history = []; st.rerun()

# --- 5. MAIN ---
st.title("🚨 CANH BAO 8 BIT V9.2")

if st.session_state.history:
    results, is_chaotic, cluster_gan, entropy = analyze_v92(st.session_state.history, st.session_state.last_n)
    
    # Radar Cảnh báo
    if is_chaotic: st.markdown(f"<div class='status-chaos'>⚠️ LỒNG QUAY ĐANG LOẠN (Entropy: {entropy:.2f}). Nên đánh Dàn 59 để bảo vệ vốn!</div>", unsafe_allow_html=True)
    else: st.markdown(f"<div class='status-safe'>✅ LỒNG QUAY NGOAN (Entropy: {entropy:.2f}). Tự tin Dàn 30 Tinh Anh!</div>", unsafe_allow_html=True)

    # Nhập liệu
    c1, c2, c3 = st.columns([1,1,1.5])
    n_in = c1.text_input("Số nổ:")
    ky_in = c2.number_input("Kỳ:", value=int(st.session_state.history[-1]["Kỳ"])+1)
    if c3.button("🚀 PHÂN TÍCH KỲ MỚI"):
        if n_in:
            val = int(n_in[-2:]); probs = [r["f"] for r in results]
            # Tính Rank (Cộng thưởng Gan cụm)
            scr = []
            gan_dict = {c['bit']: c['gan'] for c in cluster_gan}
            for i in range(100):
                s_bit = get_8bit_str(i); b = get_8bit(i)
                m_score = sum(b[j]*probs[j] + (1-b[j])*(1-probs[j]) for j in range(8))
                bonus = 0.05 * (gan_dict[s_bit] / 30) # Ưu tiên cụm gan
                scr.append({"S": f"{i:02d}", "M": m_score + bonus})
            df_t = pd.DataFrame(scr).sort_values("M", ascending=False); df_t['R'] = range(1, 101)
            r_v = df_t[df_t['S'] == f"{val:02d}"]['R'].values[0]
            st.session_state.history.append({"Kỳ": int(ky_in), "Số": f"{val:02d}", "Rank": r_v}); st.session_state.last_n = val; st.rerun()

    tab1, tab2, tab3 = st.tabs(["🎯 DÀN CHIẾN THUẬT", "🚨 CẢNH BÁO CỤM GAN", "📊 NHẬT KÝ V8.5"])
    
    with tab1:
        cols = st.columns(8)
        for i, r in enumerate(results):
            with cols[i]:
                st.markdown(f"<div class='bit-header'>{BIT_LABELS[i]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='bit-card'>4K: {int(r['p4']*100)}%<br><small>Mẫu:{r['c4']}</small></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='bit-card'>3K: {int(r['p3']*100)}%<br><small>Mẫu:{r['c3']}</small></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='bit-card'>Hậu: {int(r['pb']*100)}%<br><small>Mẫu:{r['cb']}</small></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='bit-card' style='border:1px solid #000080'><b>Hội tụ: {int(r['f']*100)}%</b></div>", unsafe_allow_html=True)
        
        num_q = 59 if is_chaotic else 30
        probs = [r["f"] for r in results]
        gan_dict = {c['bit']: c['gan'] for c in cluster_gan}
        final_list = [{"S": f"{i:02d}", "M": sum(get_8bit(i)[j]*probs[j] + (1-get_8bit(i)[j])*(1-probs[j]) for j in range(8)) + (0.05 * (gan_dict[get_8bit_str(i)]/30))} for i in range(100)]
        df_rank = pd.DataFrame(final_list).sort_values("M", ascending=False)
        st.subheader(f"🔥 DÀN {num_q} QUÂN CHỐT HẠ")
        st.markdown(f"<div class='dan-box'>{' '.join(df_rank.head(num_q)['S'].tolist())}</div>", unsafe_allow_html=True)

    with tab2:
        st.subheader("🕵️ SĂN CỤM BIT GAN LÝ TƯỞNG")
        top_clusters = sorted(cluster_gan, key=lambda x: x['gan'], reverse=True)[:5]
        for c in top_clusters:
            with st.expander(f"Mã Bit: {c['bit']} — ĐANG GAN {c['gan']} KỲ"):
                st.write(f"**Danh sách số:** {', '.join(c['members'])}")
                st.progress(min(c['gan']/35, 1.0))

    with tab3:
        disp = []
        for h in sorted(st.session_state.history, key=lambda x: x['Kỳ'], reverse=True):
            b = get_8bit(h["Số"])
            disp.append({"Kỳ": h["Kỳ"], "Số": h["Số"], "Rank": h["Rank"], "Đ.CL": "Lẻ" if b[0] else "Chẵn", "Đu.CL": "Lẻ" if b[1] else "Chẵn", "T.CL": "Lẻ" if b[2] else "Chẵn", "Đ.TB": "To" if b[3] else "Bé", "Đu.TB": "To" if b[4] else "Bé", "Hệ": "Thuận" if b[6] else "K.Phải"})
        st.dataframe(pd.DataFrame(disp), use_container_width=True, hide_index=True)
else:
    st.info("Nạp Master Data để kích hoạt Radar 8-Bit.")
