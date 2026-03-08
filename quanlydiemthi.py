import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Điểm - THCS Phương Thiện", layout="wide")

# --- KIỂM TRA VÀ CẤU HÌNH API ---
def init_ai():
    """Khởi tạo cấu hình AI từ Secrets của Streamlit với xử lý lỗi chặt chẽ."""
    # Sử dụng .get() để tránh lỗi nếu key không tồn tại trong dict
    api_key = st.secrets.get("GOOGLE_API_KEY")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Thử nghiệm với tên mô hình chuẩn nhất
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
    - Chương trình tự tìm cột chứa từ: 'Điểm', 'Diem', 'Số điểm'.
    - Bạn có thể sửa trực tiếp trên bảng sau khi tải lên.
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
    # Dữ liệu mặc định nếu chưa tải file
    df = pd.DataFrame({
        'STT': [1, 2, 3],
        'Họ và tên': ['Nguyễn Minh Quân', 'Trần Thị Mai', 'Lê Văn Tám'],
        'Lớp': ['9A', '9A', '9B'],
        'Điểm': [4.5, 8.5, 7.0]
    })

# --- HIỂN THỊ VÀ XỬ LÝ ---
if df is not None:
    st.write("### 📝 Bảng quản lý điểm số")
    # Cho phép sửa trực tiếp
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    # Tìm cột điểm một cách thông minh (Xử lý lỗi KeyError trong ảnh của bạn)
    score_col = None
    possible_names = ['điểm', 'diem', 'score', 'điểm thi', 'số điểm']
    for col in edited_df.columns:
        if any(name in str(col).lower() for name in possible_names):
            score_col = col
            break

    if score_col:
        # Ép kiểu dữ liệu về số để tính toán an toàn
        edited_df[score_col] = pd.to_numeric(edited_df[score_col], errors='coerce').fillna(0)
        
        # --- KHỐI THỐNG KÊ ---
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Sĩ số", len(edited_df))
        with c2:
            avg_score = edited_df[score_col].mean()
            st.metric("Điểm TB lớp", f"{avg_score:.2f}")
        with c3:
            # Tính tỷ lệ đạt (Sử dụng biến score_col thay vì viết cứng 'Điểm')
            pass_count = len(edited_df[edited_df[score_col] >= 5])
            rate = (pass_count / len(edited_df) * 100) if len(edited_df) > 0 else 0
            st.metric("Tỷ lệ Đạt (>=5)", f"{rate:.1f}%")

        # --- TRỢ LÝ AI ---
        st.divider()
        st.write("### 🤖 Phân tích học tập từ AI")
        
        if st.button("🚀 Thầy Trợ Lý AI: Phân tích kết quả"):
            if model:
                with st.spinner("AI đang đọc bảng điểm và chuẩn bị nhận xét..."):
                    # Chuyển bảng điểm thành văn bản để gửi cho AI
                    data_str = edited_df.to_string(index=False)
                    prompt = f"""
                    Bạn là một giáo viên trợ lý AI tại trường THCS Phương Thiện.
                    Dựa trên danh sách điểm dưới đây, hãy:
                    1. Đánh giá sơ bộ tình hình học tập.
                    2. Chỉ ra những em điểm thấp cần giúp đỡ.
                    3. Đề xuất một vài hoạt động để cải thiện điểm số.
                    
                    Dữ liệu:
                    {data_str}
                    """
                    try:
                        response = model.generate_content(prompt)
                        st.info("🎓 **Lời khuyên từ Thầy Trợ Lý AI:**")
                        st.markdown(response.text)
                    except Exception as e:
                        # Xử lý lỗi 404 hoặc lỗi API khác (như trong ảnh thứ 3 bạn gửi)
                        st.error(f"AI chưa phản hồi được. Lỗi chi tiết: {e}")
                        st.info("Mẹo: Hãy kiểm tra xem API Key của bạn có quyền truy cập mô hình 'gemini-1.5-flash' không.")
            else:
                st.warning("⚠️ **Lỗi cấu hình:** Bạn chưa nhập API Key hoặc nhập sai định dạng trong mục Secrets.")
                st.markdown("""
                **Cách khắc phục:**
                1. Vào mục **Settings** -> **Secrets** trên Streamlit Cloud.
                2. Nhập đúng: `GOOGLE_API_KEY = "MÃ_CỦA_BẠN"`
                """)
    else:
        st.warning("⚠️ Không tìm thấy cột 'Điểm'. Hãy đặt tên cột trong file là 'Điểm' hoặc sửa trực tiếp ở bảng trên.")

# --- CHÂN TRANG ---
st.divider()
st.caption("PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN © 2024")
