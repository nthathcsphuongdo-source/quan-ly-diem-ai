import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Điểm - THCS Phương Thiện", layout="wide")

# --- KIỂM TRA VÀ CẤU HÌNH API ---
def init_ai():
    """Khởi tạo cấu hình AI từ Secrets của Streamlit với cơ chế dự phòng."""
    # Sử dụng .get() để tránh lỗi nếu key không tồn tại
    api_key = st.secrets.get("GOOGLE_API_KEY")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Sử dụng mô hình gemini-1.5-flash là phiên bản ổn định và nhanh nhất
            return genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error(f"Lỗi khởi tạo AI: {e}")
            return None
    return None

model = init_ai()

# --- GIAO DIỆN CHÍNH ---
st.title("📊 PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN")
st.subheader("Hệ thống Quản lý Điểm thi & Trợ lý AI")

# --- SIDEBAR: NHẬP LIỆU ---
with st.sidebar:
    st.header("📥 Nhập dữ liệu")
    uploaded_file = st.file_uploader("Tải lên file điểm (Excel hoặc CSV)", type=['xlsx', 'csv'])
    
    st.info("""
    **Hướng dẫn file:**
    - Chương trình sẽ tự động tìm cột chứa từ: 'Điểm', 'Diem', 'Số điểm', 'Score'.
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
    # Dữ liệu mẫu (Giúp app không bị trống khi mới mở)
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

    # Thuật toán tìm cột điểm thông minh (Sửa lỗi KeyError)
    score_col = None
    # Danh sách các tên cột tiềm năng
    possible_names = ['điểm', 'diem', 'score', 'điểm thi', 'số điểm', 'điem']
    for col in edited_df.columns:
        # Kiểm tra xem tên cột có chứa bất kỳ từ khóa nào trong danh sách không
        if any(name in str(col).lower() for name in possible_names):
            score_col = col
            break

    # Chỉ thực hiện tính toán nếu tìm thấy cột điểm
    if score_col:
        # Ép kiểu dữ liệu về số, các giá trị lỗi hoặc trống sẽ thành 0 (fillna(0))
        edited_df[score_col] = pd.to_numeric(edited_df[score_col], errors='coerce').fillna(0)
        
        # --- KHỐI THỐNG KÊ (Visual Metrics) ---
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Sĩ số học sinh", len(edited_df))
        with c2:
            avg_score = edited_df[score_col].mean()
            st.metric("Điểm trung bình lớp", f"{avg_score:.2f}")
        with c3:
            pass_count = len(edited_df[edited_df[score_col] >= 5])
            rate = (pass_count / len(edited_df) * 100) if len(edited_df) > 0 else 0
            st.metric("Tỷ lệ Đạt (>=5.0)", f"{rate:.1f}%")

        # --- PHÂN TÍCH AI ---
        st.divider()
        st.write("### 🤖 Trợ lý AI Phân tích")
        
        if st.button("🚀 Yêu cầu Thầy Trợ Lý AI nhận xét"):
            if model:
                with st.spinner("AI đang đọc bảng điểm và chuẩn bị nội dung..."):
                    # Chuyển đổi dữ liệu bảng thành văn bản gửi cho AI
                    data_summary = edited_df.to_string(index=False)
                    prompt = f"""
                    Bạn là Thầy trợ lý AI tại trường THCS Phương Thiện. 
                    Hãy phân tích bảng điểm sau đây bằng tiếng Việt:
                    1. Nhận xét chung về lực học của lớp.
                    2. Liệt kê tên những học sinh có điểm dưới 5.0 và cần giúp đỡ.
                    3. Đưa ra 3 lời khuyên cụ thể cho giáo viên để nâng cao chất lượng.
                    
                    Dữ liệu:
                    {data_summary}
                    """
                    try:
                        response = model.generate_content(prompt)
                        st.info("🎓 **Nhận xét chuyên môn từ Thầy Trợ Lý AI:**")
                        st.markdown(response.text)
                    except Exception as e:
                        # Xử lý lỗi 404 hoặc lỗi kết nối (như trong ảnh bạn gửi)
                        st.error(f"AI không thể phản hồi lúc này. Chi tiết lỗi: {e}")
                        st.warning("Gợi ý: Kiểm tra lại API Key trong Secrets có đúng loại 'Gemini API' không.")
            else:
                # Thông báo lỗi Secrets rõ ràng hơn (như ảnh 1)
                st.error("❌ **Lỗi: Chưa có API Key!**")
                st.markdown("""
                Bạn cần cấu hình API Key để sử dụng tính năng này:
                1. Truy cập [Google AI Studio](https://aistudio.google.com/) để lấy Key.
                2. Vào **Settings** -> **Secrets** trên bảng điều khiển Streamlit.
                3. Thêm dòng: `GOOGLE_API_KEY = "MÃ_API_CỦA_BẠN"`
                """)
    else:
        # Thông báo nếu file tải lên không có cột điểm
        st.warning("⚠️ Hệ thống không tìm thấy cột 'Điểm' trong dữ liệu.")
        st.write("Vui lòng đảm bảo file có cột tên là 'Điểm' hoặc sửa tên cột trực tiếp ở bảng trên.")

# --- CHÂN TRANG ---
st.divider()
st.caption("PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN © 2024")
