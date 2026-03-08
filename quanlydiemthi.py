import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Điểm - THCS Phương Thiện", layout="wide")

# --- KIỂM TRA VÀ CẤU HÌNH API TỰ ĐỘNG ---
def init_ai():
    """Tự động tìm kiếm mô hình phù hợp và xử lý các lỗi API phổ biến."""
    api_key = st.secrets.get("GOOGLE_API_KEY")
    
    if not api_key:
        return None, None, "Chưa tìm thấy GOOGLE_API_KEY trong mục Secrets của Streamlit."
    
    api_key = str(api_key).strip()
    try:
        genai.configure(api_key=api_key)
        
        # Tự động quét danh sách mô hình khả dụng
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg:
                return None, None, "Lỗi 403: API Key của bạn đã bị lộ (Leaked). Hãy tạo Key mới tại Google AI Studio."
            if "400" in error_msg:
                return None, None, "Lỗi 400: API Key không hợp lệ. Hãy kiểm tra lại thao tác sao chép."
            return None, None, f"Lỗi kết nối: {error_msg}"
        
        if not available_models:
            return None, None, "Key này không có quyền sử dụng bất kỳ mô hình tạo nội dung nào."

        # Ưu tiên chọn các dòng Gemini 1.5, nếu không có thì lấy cái đầu tiên
        target_model = None
        for name in ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]:
            if name in available_models:
                target_model = name
                break
        
        if not target_model:
            target_model = available_models[0]
            
        model = genai.GenerativeModel(target_model)
        return model, target_model, None
        
    except Exception as e:
        return None, None, f"Lỗi khởi tạo hệ thống: {str(e)}"

# Khởi tạo AI
model, model_name, ai_error = init_ai()

# --- GIAO DIỆN CHÍNH ---
st.title("📊 PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN")
st.subheader("Hệ thống Quản lý Điểm thi & Trợ lý AI")

# Hiển thị trạng thái AI dựa trên các lỗi từ ảnh người dùng
if model:
    st.success(f"✅ AI Sẵn sàng! Đang sử dụng mô hình: `{model_name}`")
else:
    st.error(f"⚠️ Trợ lý AI đang tạm nghỉ: {ai_error}")
    if "403" in str(ai_error) or "400" in str(ai_error):
        st.info("💡 **Hướng dẫn:** Truy cập [Google AI Studio](https://aistudio.google.com/) để tạo lại API Key mới và dán vào Secrets.")

# --- SIDEBAR: NHẬP LIỆU ---
with st.sidebar:
    st.header("📥 Nhập dữ liệu")
    uploaded_file = st.file_uploader("Tải lên file điểm (Excel hoặc CSV)", type=['xlsx', 'csv'])
    
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

if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    # Dữ liệu mẫu giúp người dùng hình dung
    df = pd.DataFrame({
        'STT': [1, 2, 3],
        'Họ và tên': ['Nguyễn Minh Quân', 'Trần Thị Mai', 'Lê Văn Tám'],
        'Lớp': ['9A', '9A', '9B'],
        'Điểm': [4.5, 8.5, 7.0]
    })

# --- HIỂN THỊ VÀ TÍNH TOÁN ---
if df is not None:
    st.write("### 📝 Bảng quản lý điểm số")
    # Sử dụng data_editor để sửa trực tiếp, tránh lỗi KeyError khi cột bị thay đổi
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    # Tìm cột điểm thông minh (Giải quyết lỗi KeyError trong ảnh của bạn)
    score_col = None
    keywords = ['điểm', 'diem', 'score', 'số điểm', 'điem']
    for col in edited_df.columns:
        if any(key in str(col).lower().strip() for key in keywords):
            score_col = col
            break

    if score_col:
        try:
            # Ép kiểu dữ liệu số để tính toán an toàn
            edited_df[score_col] = pd.to_numeric(edited_df[score_col], errors='coerce').fillna(0)
            
            # --- KHỐI THỐNG KÊ (Sửa lỗi tại dòng 68 như trong ảnh) ---
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Sĩ số", len(edited_df))
            with c2:
                avg = edited_df[score_col].mean()
                st.metric("Trung bình lớp", f"{avg:.2f}")
            with c3:
                # Tính tỷ lệ đạt một cách an toàn bằng biến score_col
                pass_count = len(edited_df[edited_df[score_col] >= 5])
                rate = (pass_count / len(edited_df) * 100) if len(edited_df) > 0 else 0
                st.metric("Tỷ lệ Đạt (>=5)", f"{rate:.1f}%")

            # --- TRỢ LÝ AI ---
            st.divider()
            st.write("### 🤖 Trợ lý AI Phân tích")
            
            if st.button("🚀 Thầy Trợ Lý AI: Phân tích kết quả"):
                if model:
                    with st.spinner(f"Thầy trợ lý ({model_name}) đang nghiên cứu bảng điểm..."):
                        try:
                            data_str = edited_df.to_string(index=False)
                            prompt = f"Bạn là trợ lý giáo dục tại THCS Phương Thiện. Hãy phân tích bảng điểm này:\n{data_str}"
                            response = model.generate_content(prompt)
                            st.info("🎓 **Nhận xét chuyên môn:**")
                            st.markdown(response.text)
                        except Exception as e:
                            st.error(f"AI gặp sự cố khi xử lý: {e}")
                else:
                    st.warning("Tính năng AI hiện chưa thể sử dụng do lỗi cấu hình API.")
        except Exception as err:
            st.error(f"Lỗi xử lý dữ liệu: {err}")
    else:
        st.warning("⚠️ Không tìm thấy cột nào liên quan đến 'Điểm'. Hãy đổi tên cột trong file hoặc sửa trực tiếp ở bảng trên thành 'Điểm'.")

st.divider()
st.caption("PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN © 2026")
