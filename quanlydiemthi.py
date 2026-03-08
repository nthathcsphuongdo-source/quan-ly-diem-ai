import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Điểm - THCS Phương Thiện", layout="wide")

# --- KIỂM TRA VÀ CẤU HÌNH API ---
def init_ai():
    # Kiểm tra xem GOOGLE_API_KEY có tồn tại trong Secrets không
    if "GOOGLE_API_KEY" in st.secrets and st.secrets["GOOGLE_API_KEY"]:
        try:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            return genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error(f"Lỗi cấu hình AI: {e}")
            return None
    else:
        # Thay vì st.error làm dừng app, ta dùng st.warning ở khu vực AI
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
    **Yêu cầu định dạng file:**
    - Cần có cột tên chính xác là: **Điểm**
    - Các cột bổ trợ: STT, Họ và tên, Lớp.
    """)
    
    if st.button("Xóa dữ liệu hiện tại"):
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
        st.error(f"Không thể đọc file: {e}")
        return None

if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    # Dữ liệu mẫu
    data = {
        'STT': [1, 2],
        'Họ và tên': ['Nguyễn Minh Quân', 'Trần Thị Mai'],
        'Lớp': ['9A', '9A'],
        'Điểm': [4.9, 8.5]
    }
    df = pd.DataFrame(data)

# --- HIỂN THỊ VÀ KIỂM TRA CỘT ---
if df is not None:
    st.write("### 📝 Danh sách điểm số học sinh")
    
    # Cho phép sửa dữ liệu trực tiếp
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    # KIỂM TRA CỘT 'Điểm' TRƯỚC KHI TÍNH TOÁN (Tránh lỗi KeyError)
    if 'Điểm' in edited_df.columns:
        # Chuyển đổi cột điểm sang dạng số (nếu chẳng may có dữ liệu rác)
        edited_df['Điểm'] = pd.to_numeric(edited_df['Điểm'], errors='coerce').fillna(0)
        
        # --- TÍNH TOÁN THỐNG KÊ ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tổng số học sinh", len(edited_df))
        with col2:
            avg_score = edited_df['Điểm'].mean()
            st.metric("Điểm trung bình", f"{avg_score:.2f}")
        with col3:
            pass_count = len(edited_df[edited_df['Điểm'] >= 5])
            pass_rate = (pass_count / len(edited_df)) * 100 if len(edited_df) > 0 else 0
            st.metric("Tỷ lệ đạt (>=5.0)", f"{pass_rate:.1f}%")
            
        # --- CHỨC NĂNG TRỢ LÝ AI ---
        st.divider()
        st.write("### 🤖 Trợ lý Giáo dục thông minh")

        if st.button("🤖 Thầy Trợ Lý AI: Phân tích & Dự báo"):
            if model:
                with st.spinner("Thầy trợ lý đang phân tích dữ liệu..."):
                    data_summary = edited_df.to_string(index=False)
                    prompt = f"Phân tích bảng điểm trường THCS Phương Thiện:\n{data_summary}"
                    try:
                        response = model.generate_content(prompt)
                        st.info("🎓 **Nhận xét từ Thầy Trợ Lý AI:**")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"Lỗi khi gọi AI: {e}")
            else:
                st.warning("⚠️ Chức năng AI hiện chưa khả dụng. Vui lòng kiểm tra lại GOOGLE_API_KEY trong mục Secrets của Streamlit.")
    else:
        st.error("❌ Không tìm thấy cột 'Điểm' trong file của bạn. Vui lòng kiểm tra lại tên cột (phải viết đúng chữ 'Điểm' có dấu).")
        st.write("Các cột hiện có trong file của bạn là:", list(edited_df.columns))

# --- CHÂN TRANG ---
st.divider()
st.caption("PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN © 2024")
