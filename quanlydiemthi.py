import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Điểm - THCS Phương Thiện", layout="wide")

# --- KIỂM TRA VÀ CẤU HÌNH API ---
def init_ai():
    """Khởi tạo cấu hình AI từ Secrets của Streamlit với kiểm tra lỗi định dạng cực kỳ chặt chẽ."""
    api_key = st.secrets.get("GOOGLE_API_KEY")
    
    if not api_key:
        return None, "Chưa tìm thấy GOOGLE_API_KEY trong mục Secrets của Streamlit."
    
    # Làm sạch Key (xóa khoảng trắng thừa)
    api_key = str(api_key).strip()
    
    # Kiểm tra định dạng cơ bản (Ảnh lỗi 400 cho thấy Key có thể bị dán thiếu hoặc sai)
    if not api_key.startswith("AIza"):
        return None, "API Key không hợp lệ. Key chuẩn phải bắt đầu bằng chữ 'AIza'. Hãy kiểm tra lại thao tác Copy của bạn."

    try:
        genai.configure(api_key=api_key)
        # Sử dụng tên mô hình chuẩn nhất hiện nay
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model, None
    except Exception as e:
        return None, f"Lỗi hệ thống AI: {str(e)}"

# Khởi tạo mô hình
model, ai_error = init_ai()

# --- GIAO DIỆN CHÍNH ---
st.title("📊 PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN")
st.subheader("Hệ thống Quản lý Điểm thi & Trợ lý AI")

# --- SIDEBAR: NHẬP LIỆU ---
with st.sidebar:
    st.header("📥 Nhập dữ liệu")
    uploaded_file = st.file_uploader("Tải lên file điểm (Excel hoặc CSV)", type=['xlsx', 'csv'])
    
    st.info("""
    **Hướng dẫn file:**
    - Chương trình tự tìm cột chứa từ: 'Điểm', 'Diem', 'Số điểm'.
    - Bạn có thể sửa trực tiếp trên bảng.
    """)
    
    if st.button("🔄 Làm mới hệ thống"):
        st.cache_data.clear()
        st.rerun()

# --- XỬ LÝ DỮ LIỆU ---
@st.cache_data
def load_data(file):
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    except Exception as e:
        st.error(f"Lỗi khi mở file: {e}")
        return None

# Khởi tạo dữ liệu
if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    # Dữ liệu mẫu ban đầu để app luôn có cái để hiện
    df = pd.DataFrame({
        'STT': [1, 2, 3],
        'Họ và tên': ['Nguyễn Minh Quân', 'Trần Thị Mai', 'Lê Văn Tám'],
        'Lớp': ['9A', '9A', '9B'],
        'Điểm': [4.5, 8.5, 7.0]
    })

# --- HIỂN THỊ VÀ XỬ LÝ ---
if df is not None:
    st.write("### 📝 Bảng quản lý điểm số")
    # Sử dụng data_editor để người dùng có thể sửa điểm trực tiếp
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    # THUẬT TOÁN TÌM CỘT ĐIỂM THÔNG MINH (Sửa triệt để lỗi KeyError trong ảnh của bạn)
    score_col = None
    possible_names = ['điểm', 'diem', 'score', 'điểm thi', 'số điểm', 'điem']
    
    for col in edited_df.columns:
        clean_col = str(col).strip().lower()
        if any(name in clean_col for name in possible_names):
            score_col = col
            break

    # Chỉ thực hiện tính toán nếu tìm thấy cột điểm
    if score_col:
        try:
            # Chuyển đổi sang số an toàn
            edited_df[score_col] = pd.to_numeric(edited_df[score_col], errors='coerce').fillna(0)
            
            # --- KHỐI THỐNG KÊ ---
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Sĩ số", len(edited_df))
            with c2:
                avg_score = edited_df[score_col].mean()
                st.metric("Trung bình lớp", f"{avg_score:.2f}")
            with c3:
                # Dùng score_col thay vì viết cứng 'Điểm' để tránh lỗi
                pass_count = len(edited_df[edited_df[score_col] >= 5])
                rate = (pass_count / len(edited_df) * 100) if len(edited_df) > 0 else 0
                st.metric("Tỷ lệ Đạt (>=5)", f"{rate:.1f}%")

            # --- TRỢ LÝ AI ---
            st.divider()
            st.write("### 🤖 Trợ lý AI Phân tích")
            
            if st.button("🚀 Thầy Trợ Lý AI: Phân tích kết quả"):
                if model:
                    with st.spinner("AI đang đọc bảng điểm và chuẩn bị nhận xét..."):
                        try:
                            data_str = edited_df.to_string(index=False)
                            prompt = f"""
                            Bạn là một người thầy trợ lý ảo tại trường THCS Phương Thiện.
                            Hãy phân tích bảng điểm sau và đưa ra nhận xét:
                            1. Tình hình học tập chung.
                            2. Những em cần chú ý (điểm thấp).
                            3. Giải pháp cải thiện chất lượng.
                            
                            Dữ liệu: {data_str}
                            """
                            response = model.generate_content(prompt)
                            st.info("🎓 **Nhận xét chuyên môn:**")
                            st.markdown(response.text)
                        except Exception as e:
                            # Xử lý lỗi 404/400 (như trong ảnh bạn gửi)
                            if "404" in str(e):
                                st.error("Lỗi 404: Mô hình 'gemini-1.5-flash' không tìm thấy. Có thể Key của bạn chưa được cấp quyền dùng mô hình này.")
                            elif "400" in str(e):
                                st.error("Lỗi 400: API Key không hợp lệ (API_KEY_INVALID). Hãy kiểm tra lại mục Secrets.")
                            else:
                                st.error(f"AI chưa phản hồi được. Lỗi: {e}")
                else:
                    st.error(f"❌ {ai_error}")
                    st.markdown("""
                    **Hướng dẫn sửa lỗi:**
                    1. Vào [Google AI Studio](https://aistudio.google.com/) tạo Key mới.
                    2. Kiểm tra lại mục **Secrets** trên Streamlit Cloud:
                       - Tên biến: `GOOGLE_API_KEY`
                       - Giá trị: `"MÃ_CỦA_BẠN"` (nhớ để trong dấu ngoặc kép).
                    """)
        except Exception as calc_error:
            st.error(f"Lỗi tính toán dữ liệu: {calc_error}")
    else:
        st.warning("⚠️ Không tìm thấy cột 'Điểm'. Hãy đổi tên cột trong file Excel hoặc sửa tên trực tiếp ở bảng trên.")

# --- CHÂN TRANG ---
st.divider()
st.caption("PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN © 2024")
