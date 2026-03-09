import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Điểm - THCS Phương Thiện", layout="wide")

# --- KIỂM TRA VÀ CẤU HÌNH API TỰ ĐỘNG ---
@st.cache_resource
def setup_ai():
    if "API_KEY" not in st.secrets:
        return None, "Thiếu API_KEY trong Secrets"
    
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        # Liệt kê các mô hình mà mã API này được phép dùng
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ưu tiên chọn theo thứ tự tốt nhất
        priority = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        selected_model_name = None
        
        for p in priority:
            if p in available_models:
                selected_model_name = p
                break
        
        if not selected_model_name and available_models:
            selected_model_name = available_models[0]
            
        if selected_model_name:
            return genai.GenerativeModel(selected_model_name), f"Đang dùng: {selected_model_name}"
        return None, "Không tìm thấy mô hình khả dụng"
    except Exception as e:
        return None, str(e)
model, status_msg = setup_ai()
def get_gemini_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    
    # Bắt lỗi khi vượt quá số lượng request (Rate Limit)
    except exceptions.ResourceExhausted:
        st.error("Hệ thống đang bận do quá nhiều yêu cầu (Rate Limit). Vui lòng đợi 30-60 giây rồi thử lại.")
        return None
    
    # Bắt các lỗi hệ thống khác
    except Exception as e:
        st.error(f"Đã xảy ra lỗi: {e}")
        return None
# --- GIAO DIỆN CHÍNH ---
st.title("📊 PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN")
st.subheader("Hệ thống Quản lý Điểm thi & Trợ lý AI")

# Hiển thị trạng thái AI dựa trên phản hồi từ hệ thống
if model:
    st.success(f"✅ AI Sẵn sàng! Đang sử dụng mô hình: `{model_name}`")
else:
    st.error(f"⚠️ Trợ lý AI đang tạm nghỉ: {ai_error}")
    if ai_error and ("403" in ai_error or "400" in ai_error):
        st.info("💡 **Hướng dẫn:** Truy cập [Google AI Studio](https://aistudio.google.com/) để lấy API Key mới và cập nhật vào mục Secrets.")

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
    # Dữ liệu mẫu giúp người dùng làm quen với hệ thống
    df = pd.DataFrame({
        'STT': [1, 2, 3],
        'Họ và tên': ['Nguyễn Minh Quân', 'Trần Thị Mai', 'Lê Văn Tám'],
        'Lớp': ['9A', '9A', '9B'],
        'Điểm': [4.5, 8.5, 7.0]
    })

# --- HIỂN THỊ VÀ TÍNH TOÁN ---
if df is not None:
    st.write("### 📝 Bảng quản lý điểm số học sinh")
    # Sử dụng data_editor để chỉnh sửa dữ liệu linh hoạt
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    # Thuật toán tìm cột điểm thông minh (Để sửa lỗi KeyError: 'Điểm' trong ảnh của bạn)
    score_col = None
    keywords = ['điểm', 'diem', 'score', 'số điểm', 'điem', 'điểm thi']
    for col in edited_df.columns:
        if any(key in str(col).lower().strip() for key in keywords):
            score_col = col
            break

    if score_col:
        try:
            # Đảm bảo dữ liệu trong cột điểm là dạng số để tính toán
            edited_df[score_col] = pd.to_numeric(edited_df[score_col], errors='coerce').fillna(0)
            
            # --- KHỐI THỐNG KÊ (Sửa lỗi tính toán pass_rate bằng score_col thay vì tên cứng) ---
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Sĩ số", len(edited_df))
            with c2:
                avg = edited_df[score_col].mean()
                st.metric("Trung bình lớp", f"{avg:.2f}")
            with c3:
                # Tính tỷ lệ đạt (>= 5.0) một cách an toàn
                pass_count = len(edited_df[edited_df[score_col] >= 5])
                rate = (pass_count / len(edited_df) * 100) if len(edited_df) > 0 else 0
                st.metric("Tỷ lệ Đạt (>=5)", f"{rate:.1f}%")

            # --- TRỢ LÝ AI ---
            st.divider()
            st.write("### 🤖 Trợ lý Giáo dục AI")
            
            if st.button("🚀 Thầy Trợ Lý AI: Phân tích kết quả học tập"):
                if model:
                    with st.spinner(f"Thầy trợ lý AI ({model_name}) đang nghiên cứu dữ liệu..."):
                        try:
                            data_str = edited_df.to_string(index=False)
                            prompt = f"""
                            Bạn là một người thầy trợ lý ảo tại trường THCS Phương Thiện.
                            Dựa trên bảng điểm sau, hãy đưa ra nhận xét:
                            1. Đánh giá sơ bộ về lực học của lớp.
                            2. Những em học sinh có điểm dưới 5.0 cần giáo viên hỗ trợ thêm.
                            3. Đề xuất giải pháp sư phạm để nâng cao kết quả học tập.
                            
                            Dữ liệu bảng điểm:
                            {data_str}
                            """
                            response = model.generate_content(prompt)
                            st.info("🎓 **Lời khuyên từ Thầy Trợ Lý AI:**")
                            st.markdown(response.text)
                        except Exception as e:
                            st.error(f"AI gặp sự cố khi xử lý dữ liệu: {e}")
                            if "429" in str(e):
                                st.warning("Mẹo: Hệ thống đang bị quá tải yêu cầu, vui lòng đợi vài phút.")
                else:
                    st.warning("⚠️ Chức năng AI hiện chưa khả dụng do lỗi API Key. Vui lòng kiểm tra lại cấu hình.")
        except Exception as err:
            st.error(f"Lỗi khi xử lý dữ liệu điểm số: {err}")
    else:
        st.warning("⚠️ Không tìm thấy cột nào liên quan đến 'Điểm'. Hãy đổi tên cột trong file hoặc sửa trực tiếp ở bảng trên thành 'Điểm'.")

st.divider()
st.caption("HỆ THỐNG QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN © 2024")


