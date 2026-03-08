import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Điểm - THCS Phương Thiện", layout="wide")

# --- KIỂM TRA VÀ CẤU HÌNH API ---
def init_ai():
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    else:
        st.error("⚠️ Chưa cấu hình API Key trong mục Secrets của Streamlit.")
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
    **Hướng dẫn:** File cần có các cột: STT, Họ và tên, Lớp, Điểm.
    """)

# --- XỬ LÝ DỮ LIỆU ---
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"Đã tải lên thành công: {uploaded_file.name}")
    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")
        df = pd.DataFrame()
else:
    # Dữ liệu mẫu nếu chưa có file
    data = {
        'STT': [1, 2],
        'Họ và tên': ['Nguyễn Minh Quân', 'Trần Thị Mai'],
        'Lớp': ['9A', '9A'],
        'Điểm': [4.9, 8.5]
    }
    df = pd.DataFrame(data)
    st.info("💡 Đang hiển thị dữ liệu mẫu. Hãy tải file của bạn ở thanh bên.")

# --- HIỂN THỊ BẢNG ĐIỂM ---
st.write("### 📝 Danh sách điểm số học sinh")
edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

# --- TÍNH TOÁN THỐNG KÊ ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Tổng số học sinh", len(edited_df))
with col2:
    avg_score = edited_df['Điểm'].mean() if 'Điểm' in edited_df.columns else 0
    st.metric("Điểm trung bình", f"{avg_score:.2f}")
with col3:
    pass_rate = (len(edited_df[edited_df['Điểm'] >= 5]) / len(edited_df)) * 100 if len(edited_df) > 0 else 0
    st.metric("Tỷ lệ đạt (>=5.0)", f"{pass_rate:.1f}%")

# --- CHỨC NĂNG TRỢ LÝ AI ---
st.divider()
st.write("### 🤖 Trợ lý Giáo dục thông minh")

if st.button("🤖 Thầy Trợ Lý AI: Phân tích & Dự báo"):
    if model:
        with st.spinner("Thầy trợ lý đang phân tích dữ liệu..."):
            # Chuẩn bị dữ liệu cho AI
            data_summary = edited_df.to_string(index=False)
            prompt = f"""
            Bạn là một người thầy trợ lý ảo tại trường THCS Phương Thiện. 
            Hãy phân tích bảng điểm sau đây và đưa ra nhận xét:
            1. Tình hình học tập chung của lớp.
            2. Danh sách các học sinh cần chú ý (điểm thấp).
            3. Đề xuất giải pháp cải thiện cho giáo viên.
            
            Dữ liệu:
            {data_summary}
            
            Hãy trả lời bằng tiếng Việt, giọng điệu chuyên nghiệp, thân thiện và mang tính xây dựng.
            """
            
            try:
                response = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(f"#### 🎓 Nhận xét từ Thầy Trợ Lý AI:")
                st.write(response.text)
            except Exception as e:
                st.error(f"Lỗi khi gọi AI: {e}")
    else:
        st.warning("Vui lòng cấu hình API Key để sử dụng tính năng này.")

# --- CHÂN TRANG ---
st.divider()
st.caption("PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN © 2024")
