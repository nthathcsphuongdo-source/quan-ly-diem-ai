import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# 1. Cấu hình trang và Giao diện
st.set_page_config(page_title="Quản lý chất lượng - Phương Thiện", layout="wide")

def setup_ai():
    """Thiết lập kết nối với Google Gemini AI"""
    if "API_KEY" in st.secrets:
        try:
            genai.configure(api_key=st.secrets["API_KEY"])
            return genai.GenerativeModel('gemini-1.5-flash')
        except Exception:
            return None
    return None

model = setup_ai()

st.title("📊 Trợ lý Phân tích Dữ liệu & Dự báo Học tập")
st.write("Dành cho Ban Giám hiệu trường THCS Phương Thiện")
st.markdown("---")

# 2. Sidebar - Tải dữ liệu
st.sidebar.header("📁 Dữ liệu đầu vào")
uploaded_file = st.sidebar.file_uploader("Tải lên file điểm Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ Đã nạp dữ liệu thành công!")
        
        # Hiển thị bảng dữ liệu mẫu
        with st.expander("👀 Xem bảng dữ liệu thô"):
            st.dataframe(df)

        # 3. Xử lý lỗi KeyError bằng cách cho người dùng chọn cột
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Cấu hình phân tích")
        
        all_columns = df.columns.tolist()
        
        # Tự động gợi ý cột có chữ 'Điểm' hoặc 'Trung bình'
        default_index = 0
        for i, col in enumerate(all_columns):
            if "điểm" in col.lower() or "tb" in col.lower() or "trung bình" in col.lower():
                default_index = i
                break
        
        target_col = st.sidebar.selectbox(
            "Chọn cột chứa Điểm Tổng Kết để phân tích:",
            options=all_columns,
            index=default_index
        )

        # 4. Hiển thị Dashboard Thống kê
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📋 Thống kê nhanh")
            total_students = len(df)
            avg_score = df[target_col].mean()
            max_score = df[target_col].max()
            min_score = df[target_col].min()
            
            st.metric("Tổng số học sinh", f"{total_students}")
            st.metric("Điểm trung bình khối", f"{avg_score:.2f}")
            st.metric("Điểm cao nhất", f"{max_score:.1f}")
            
        with col2:
            st.subheader("📈 Biểu đồ Phổ điểm")
            fig = px.histogram(
                df, 
                x=target_col, 
                nbins=10, 
                title=f"Phân phối điểm số (Cột: {target_col})",
                labels={target_col: 'Điểm số'},
                color_discrete_sequence=['#3366ff']
            )
            st.plotly_chart(fig, use_container_width=True)

        # 5. Cảnh báo nguy cơ
        st.markdown("---")
        st.subheader("🚨 Danh sách học sinh cần hỗ trợ (Dưới 5.0)")
        
        nguy_co = df[df[target_col] < 5]
        if not nguy_co.empty:
            st.warning(f"Phát hiện {len(nguy_co)} học sinh có kết quả dưới trung bình.")
            st.dataframe(nguy_co)
        else:
            st.success("Tất cả học sinh đều đạt mức điểm an toàn.")

        # 6. AI Nhận xét & Dự báo
        if st.button("🤖 Thầy Trợ Lý AI: Phân tích & Dự báo"):
            if model:
                with st.spinner("AI đang đọc bảng điểm và soạn báo cáo..."):
                    # Tóm tắt dữ liệu để gửi cho AI
                    stats_summary = df[target_col].describe().to_dict()
                    prompt = f"""
                    Bạn là Chuyên gia Quản lý Giáo dục tại Hà Giang. 
                    Dữ liệu điểm môn Toán (cột {target_col}) của khối 9 như sau:
                    - Tổng số: {total_students} học sinh.
                    - Trung bình: {stats_summary['mean']:.2f}
                    - Thấp nhất: {stats_summary['min']:.1f}
                    - Cao nhất: {stats_summary['max']:.1f}
                    
                    Hãy viết báo cáo ngắn gọn (khoảng 200 chữ) gửi Hiệu trưởng:
                    1. Đánh giá chất lượng hiện tại.
                    2. Dự báo khả năng thi đỗ vào lớp 10 (biết điểm chuẩn thường quanh mức 5.0).
                    3. Đề xuất 2 hành động cụ thể cho tháng tới.
                    """
                    
                    try:
                        response = model.generate_content(prompt)
                        st.info("### 📝 Báo cáo phân tích từ AI")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"Lỗi AI: {e}")
            else:
                st.error("Chưa cấu hình API Key trong mục Secrets của Streamlit.")

    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")
        st.info("Lưu ý: Hãy đảm bảo file Excel của thầy có cột chứa điểm số.")

else:
    st.info("👈 Vui lòng tải lên file Excel điểm số ở thanh bên trái để bắt đầu.")

# Chân trang
st.markdown("---")
st.caption("PHẦN MỀM QUẢN LÝ THÔNG MINH - THCS PHƯƠNG THIỆN")
