if st.button("🚀 PHÂN TÍCH ELITE T1-T2 (LAG FIX)"):
        # 1. Xác định các mốc thời gian
        n_t1 = num_soi # Kỳ vừa xong
        n_t2 = data[-2] if len(data) >= 2 else None
        
        def get_f_counts(target, limit=150):
            f_list = []; t_bits = get_8bit(target); cnt = 0
            for i in range(len(data) - 2, -1, -1):
                if get_8bit(data[i]) == t_bits:
                    f_list.append(data[i+1]); cnt += 1
                    if cnt == limit: break
            return Counter(f_list)

        # Bạc nhớ đa tầng
        f1 = get_f_counts(n_t1)
        f2 = get_f_counts(n_t2) if n_t2 is not None else Counter()
        
        # 2. LOGIC "NHỊP RƠI T-2" - Mày mới phát hiện
        # Tao giả lập lại việc tính toán dàn của 2 kỳ trước (T-2) để lấy Top 39 và 59
        # Đây là bước cực kỳ quan quan trọng để lấy "vía" trễ
        t2_scores = {}
        if len(data) >= 3:
            prev_t2_num = data[-2]
            prev_t3_num = data[-3] if len(data) >= 3 else data[-2]
            # Quét nhanh nhịp của kỳ T-2
            pf1 = get_f_counts(prev_t2_num)
            pf2 = get_f_counts(prev_t3_num)
            for i in range(100):
                # Tính điểm nhanh cho kỳ T-2 để xác định Rank
                s_t2 = pf1.get(i, 0) * 600000 + pf2.get(i, 0) * 150000
                t2_scores[i] = s_t2
            
            # Phân hạng kỳ T-2
            t2_ranked = [n for n, s in sorted(t2_scores.items(), key=lambda x: x[1], reverse=True)]
            top_39_t2 = set(t2_ranked[:39])
            top_59_t2 = set(t2_ranked[39:59])
        else:
            top_39_t2, top_59_t2 = set(), set()

        # 3. Pattern Bit kỳ T-1
        cur_bits = get_8bit(n_t1); fol_bits = []
        for i in range(len(data) - 2, -1, -1):
            if get_8bit(data[i]) == cur_bits:
                fol_bits.append(get_8bit(data[i+1]))
                if len(fol_bits) == 150: break
        
        if fol_bits:
            t_probs = np.mean(np.array(fol_bits), axis=0)
            t_pattern = [1 if p >= 0.5 else 0 for p in t_probs]
            
            scores_clean = {}
            for i in range(100):
                s = 0; i_bits = get_8bit(i)
                # A. Khớp Bit
                s += sum([t_probs[j] if i_bits[j]==1 else (1-t_probs[j]) for j in range(8)]) * 100000
                # B. Bạc nhớ T-1 & T-2
                s += f1.get(i, 0) * 600000
                s += f2.get(i, 0) * 150000
                
                # C. CỘNG ĐIỂM "NHỊP RƠI" T-2 (Mày mới phát hiện)
                if i in top_39_t2: s += 800000 # Cộng mạnh cho Top 39 kỳ cũ
                if i in top_59_t2: s += 300000 # Cộng nhẹ cho 20 số tiếp theo
                
                # D. Thưởng Siêu Cối
                if i in f1 and i_bits == t_pattern: s += 2500000
                s += Counter(data).get(i, 0)
                scores_clean[i] = s
            
            ranked_clean = [n for n, s in sorted(scores_clean.items(), key=lambda x: x[1], reverse=True)]
            top_19 = set(ranked_clean[:19])

            # --- SCORES FULL (39+ NGHỊCH ĐẢO) ---
            scores_full = {}
            inv_map = {}
            for n, c in f1.items():
                if c >= 2: inv_map[(n%10)*10 + (n//10)] = c * 400000
            
            for i in range(100):
                s = scores_clean[i]
                if i not in top_19 and i in inv_map: s += inv_map[i]
                scores_full[i] = s
            
            full_ranked = [n for n, s in sorted(scores_full.items(), key=lambda x: x[1], reverse=True)]
            
            st.session_state.last_danh_sach = {
                "🔴 DÀN CỐI (9s)": sorted(full_ranked[:9]),
                "🔥 DÀN KẾT (10s)": sorted(full_ranked[9:19]),
                "⭐ DÀN ĐẸP (20s)": sorted(full_ranked[19:39]),
                "💎 TRUNG BÌNH (20s)": sorted(full_ranked[39:59]),
                "🛡️ XÉT LÓT (20s)": sorted(full_ranked[59:79]),
                "🚫 DÀN LOẠI (21s)": sorted(full_ranked[79:])
            }
            st.session_state.last_num_soi = num_soi
