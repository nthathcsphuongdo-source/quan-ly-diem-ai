import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Điểm - THCS Phương Thiện", layout="wide")

# --- KIỂM TRA VÀ CẤU HÌNH API TỰ ĐỘNG ---
def init_ai():
    """Tự động tìm kiếm mô hình phù hợp với API Key trong Secrets."""
    api_key = st.secrets.get("GOOGLE_API_KEY")
    
    if not api_key:
        return None, None, "Chưa tìm thấy GOOGLE_API_KEY trong mục Secrets."
    
    api_key = str(api_key).strip()
    try:
        genai.configure(api_key=api_key)
        
        # Tự động quét danh sách mô hình khả dụng cho Key này
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            return None, None, "Key này không có quyền sử dụng bất kỳ mô hình tạo nội dung nào."

        # Ưu tiên chọn gemini-1.5-flash, nếu không có thì lấy cái đầu tiên trong danh sách
        target_model = "models/gemini-1.5-flash"
        if target_model not in available_models:
            target_model = available_models[0]
            
        model = genai.GenerativeModel(target_model)
        return model, target_model, None
        
    except Exception as e:
        return None, None, f"Lỗi kết nối API: {str(e)}"

# Khởi tạo AI và lấy thông tin mô hình
model, model_name, ai_error = init_ai()

# --- GIAO DIỆN CHÍNH ---
st.title("📊 PHẦN MỀM HỖ TRỢ PHÂN TÍCH VÀ DỰ BÁO ĐIỂM THÔNG MINH - THCS PHƯƠNG THIỆN")
st.subheader("Hệ thống giúp phân tích và dự báo điểm thi các môn học")

# Hiển thị trạng thái AI
if model:
    st.success(f"✅ Đã kết nối thành công mô hình: `{model_name}`")
else:
    st.warning(f"⚠️ Trợ lý AI đang tạm nghỉ: {ai_error}")

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
    # Dữ liệu mẫu
    df = pd.DataFrame({
        'STT': [1, 2, 3],
        'Họ và tên': ['Nguyễn Minh Quân', 'Trần Thị Mai', 'Lê Văn Tám'],
        'Lớp': ['9A', '9A', '9B'],
        'Điểm': [4.5, 8.5, 7.0]
    })

# --- HIỂN THỊ VÀ TÍNH TOÁN ---
if df is not None:
    st.write("### 📝 Bảng quản lý điểm số")
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    # Tìm cột điểm thông minh (Tránh lỗi KeyError)
    score_col = None
    keywords = ['điểm', 'diem', 'score', 'số điểm']
    for col in edited_df.columns:
        if any(key in str(col).lower().strip() for key in keywords):
            score_col = col
            break

    if score_col:
        try:
            edited_df[score_col] = pd.to_numeric(edited_df[score_col], errors='coerce').fillna(0)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Sĩ số", len(edited_df))
            with c2:
                avg = edited_df[score_col].mean()
                st.metric("Trung bình lớp", f"{avg:.2f}")
            with c3:
                pass_count = len(edited_df[edited_df[score_col] >= 5])
                rate = (pass_count / len(edited_df) * 100) if len(edited_df) > 0 else 0
                st.metric("Tỷ lệ Đạt (>=5)", f"{rate:.1f}%")

            # --- TRỢ LÝ AI ---
            st.divider()
            st.write("### 🤖 Trợ lý AI Phân tích")
            
            if st.button("🚀 Thầy Trợ Lý AI: Phân tích kết quả"):
                if model:
                    with st.spinner(f"Đang dùng {model_name} để phân tích..."):
                        try:
                            data_str = edited_df.to_string(index=False)
                            prompt = f"Phân tích bảng điểm trường THCS Phương Thiện:\n{data_str}"
                            response = model.generate_content(prompt)
                            st.info("🎓 **Nhận xét chuyên môn:**")
                            st.markdown(response.text)
                        except Exception as e:
                            st.error(f"AI không thể phản hồi: {e}")
                else:
                    st.error("Chưa cấu hình API Key hợp lệ.")
        except Exception as err:
            st.error(f"Lỗi xử lý dữ liệu: {err}")
    else:
        st.warning("⚠️ Không tìm thấy cột 'Điểm'. Hãy đổi tên cột trong file hoặc sửa trực tiếp ở bảng trên.")

st.divider()
st.caption("PHẦN MỀM HỖ TRỢ PHÂN TÍCH VÀ DỰ BÁO - THCS PHƯƠNG THIỆN © 2026")
