import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Điểm - THCS Phương Thiện", layout="wide")

# --- KIỂM TRA VÀ CẤU HÌNH API ---
def init_ai():
    """Khởi tạo cấu hình AI từ Secrets của Streamlit."""
    if "GOOGLE_API_KEY" in st.secrets and st.secrets["GOOGLE_API_KEY"]:
        try:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            return genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error(f"Lỗi cấu hình AI: {e}")
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
    **Mẹo nhỏ:** Chương trình sẽ tự động tìm cột điểm. 
    Hãy đảm bảo file có cột chứa từ 'Điểm' hoặc 'Diem'.
    """)
    
    if st.button("Làm mới hệ thống"):
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
        st.error(f"Lỗi đọc file: {e}")
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
    st.write("### 📝 Bảng dữ liệu hiện tại")
    # Cho phép chỉnh sửa trực tiếp trên giao diện
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    # Tự động tìm cột Điểm (không phân biệt hoa thường, có dấu hay không)
    score_col = None
    possible_names = ['điểm', 'diem', 'score', 'điểm thi']
    for col in edited_df.columns:
        if any(name in col.lower() for name in possible_names):
            score_col = col
            break

    if score_col:
        # Chuyển đổi dữ liệu sang dạng số
        edited_df[score_col] = pd.to_numeric(edited_df[score_col], errors='coerce').fillna(0)
        
        # --- THỐNG KÊ ---
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Sĩ số", len(edited_df))
        with c2:
            avg = edited_df[score_col].mean()
            st.metric("Trung bình lớp", f"{avg:.2f}")
        with c3:
            pass_count = len(edited_df[edited_df[score_col] >= 5])
            rate = (pass_count / len(edited_df) * 100) if len(edited_df) > 0 else 0
            st.metric("Tỷ lệ đạt", f"{rate:.1f}%")

        # --- TRỢ LÝ AI ---
        st.divider()
        st.write("### 🤖 Phân tích thông minh")
        
        if st.button("🚀 Yêu cầu Thầy Trợ Lý AI phân tích"):
            if model:
                with st.spinner("AI đang nghiên cứu bảng điểm..."):
                    summary = edited_df.to_string(index=False)
                    prompt = f"""
                    Bạn là thầy giáo trợ lý AI tại THCS Phương Thiện. 
                    Dựa trên bảng điểm sau, hãy đưa ra nhận xét ngắn gọn về:
                    - Học sinh xuất sắc và học sinh cần phụ đạo.
                    - Đề xuất hướng cải thiện cho lớp.
                    
                    Dữ liệu: {summary}
                    """
                    try:
                        res = model.generate_content(prompt)
                        st.info("🎓 **Nhận xét chuyên môn:**")
                        st.write(res.text)
                    except Exception as e:
                        st.error(f"AI gặp sự cố: {e}")
            else:
                st.warning("⚠️ Vui lòng cấu hình GOOGLE_API_KEY trong mục Secrets để dùng tính năng này.")
    else:
        st.warning("⚠️ Không tìm thấy cột nào liên quan đến 'Điểm'. Hãy đổi tên cột trong file hoặc sửa trực tiếp trên bảng trên.")

# --- CHÂN TRANG ---
st.divider()
st.caption("Ứng dụng phát triển bởi THCS Phương Thiện - 2024")
