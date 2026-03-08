import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Điểm - THCS Phương Thiện", layout="wide")

# --- KIỂM TRA VÀ CẤU HÌNH API ---
def init_ai():
    """Khởi tạo cấu hình AI từ Secrets của Streamlit với kiểm tra lỗi định dạng."""
    api_key = st.secrets.get("GOOGLE_API_KEY")
    
    if not api_key:
        return None, "Chưa tìm thấy GOOGLE_API_KEY trong mục Secrets."
    
    # Kiểm tra cơ bản định dạng API Key (thường bắt đầu bằng AIza)
    api_key = str(api_key).strip()
    if not api_key.startswith("AIza"):
        return None, "API Key không hợp lệ (thường phải bắt đầu bằng 'AIza'). Hãy kiểm tra lại thao tác Copy."

    try:
        genai.configure(api_key=api_key)
        # Sử dụng mô hình ổn định nhất
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model, None
    except Exception as e:
        return None, f"Lỗi hệ thống AI: {str(e)}"

# Khởi tạo mô hình và lấy thông báo lỗi nếu có
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
    - Bạn có thể chỉnh sửa dữ liệu trực tiếp trên bảng.
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

# Khởi tạo dữ liệu ban đầu
if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    # Dữ liệu mẫu ban đầu
    df = pd.DataFrame({
        'STT': [1, 2, 3],
        'Họ và tên': ['Nguyễn Minh Quân', 'Trần Thị Mai', 'Lê Văn Tám'],
        'Lớp': ['9A', '9A', '9B'],
        'Điểm': [4.5, 8.5, 7.0]
    })

# --- HIỂN THỊ VÀ XỬ LÝ ---
if df is not None:
    st.write("### 📝 Bảng quản lý điểm số")
    # Cho phép sửa trực tiếp (Data Editor)
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    # Tìm cột điểm thông minh để tránh lỗi KeyError (như trong ảnh lỗi bạn gửi)
    score_col = None
    possible_names = ['điểm', 'diem', 'score', 'điểm thi', 'số điểm', 'điem']
    
    for col in edited_df.columns:
        # Làm sạch tên cột để so sánh chính xác hơn
        clean_col = str(col).strip().lower()
        if any(name in clean_col for name in possible_names):
            score_col = col
            break

    if score_col:
        try:
            # Chuyển đổi sang số và xử lý lỗi dữ liệu rác
            edited_df[score_col] = pd.to_numeric(edited_df[score_col], errors='coerce').fillna(0)
            
            # --- KHỐI THỐNG KÊ ---
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Sĩ số", len(edited_df))
            with c2:
                avg_score = edited_df[score_col].mean()
                st.metric("Trung bình lớp", f"{avg_score:.2f}")
            with c3:
                pass_count = len(edited_df[edited_df[score_col] >= 5])
                rate = (pass_count / len(edited_df) * 100) if len(edited_df) > 0 else 0
                st.metric("Tỷ lệ Đạt (>=5)", f"{rate:.1f}%")

            # --- TRỢ LÝ AI ---
            st.divider()
            st.write("### 🤖 Trợ lý AI Phân tích")
            
            if st.button("🚀 Thầy Trợ Lý AI: Phân tích kết quả"):
                if model:
                    with st.spinner("AI đang nghiên cứu bảng điểm..."):
                        try:
                            data_summary = edited_df.to_string(index=False)
                            prompt = f"""
                            Bạn là Thầy trợ lý AI tại trường THCS Phương Thiện. 
                            Hãy phân tích dữ liệu điểm sau:
                            {data_summary}
                            Yêu cầu: Nhận xét ngắn gọn, chỉ ra học sinh cần lưu ý và đề xuất giải pháp.
                            """
                            response = model.generate_content(prompt)
                            st.info("🎓 **Nhận xét từ Thầy Trợ Lý AI:**")
                            st.markdown(response.text)
                        except Exception as e:
                            # Xử lý lỗi 404/400 (như trong ảnh lỗi)
                            st.error(f"AI chưa phản hồi được. Chi tiết: {str(e)}")
                            if "404" in str(e):
                                st.warning("Mẹo: Mô hình 'gemini-1.5-flash' có thể chưa khả dụng với Key này hoặc ở vùng này. Hãy kiểm tra lại Google AI Studio.")
                            elif "API_KEY_INVALID" in str(e) or "400" in str(e):
                                st.error("Lỗi: API Key của bạn không hợp lệ hoặc đã hết hạn.")
                else:
                    st.error(f"❌ **Lỗi cấu hình AI:** {ai_error}")
                    st.markdown("""
                    **Hướng dẫn sửa lỗi:**
                    1. Vào [Google AI Studio](https://aistudio.google.com/) tạo Key mới.
                    2. Kiểm tra lại mục **Secrets** trên Streamlit Cloud:
                       - Tên biến: `GOOGLE_API_KEY`
                       - Giá trị: `"MÃ_CỦA_BẠN"` (phải nằm trong dấu ngoặc kép).
                    """)
        except Exception as calc_error:
            st.error(f"Lỗi tính toán dữ liệu: {calc_error}")
    else:
        st.warning("⚠️ Hệ thống không tìm thấy cột 'Điểm'. Hãy đổi tên cột trong file hoặc sửa trực tiếp ở bảng trên thành 'Điểm'.")

# --- CHÂN TRANG ---
st.divider()
st.caption("PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN © 2024")
