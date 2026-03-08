import streamlit as st
import pandas as pd
import plotly.express as px # Thư viện vẽ biểu đồ chuyên nghiệp hơn matplotlib

st.set_page_config(page_title="Hệ thống Quản lý chất lượng Phương Thiện", layout="wide")

st.title("📊 Trợ lý Phân tích & Dự báo Học tập")
st.write("Dành cho Ban Giám hiệu nhà trường")

# 1. Chức năng tải file
uploaded_file = st.file_uploader("Tải lên file danh sách điểm (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("Đã tải dữ liệu thành công!")
    
    # Hiển thị bảng dữ liệu tóm tắt
    st.subheader("📋 Danh sách học sinh")
    st.dataframe(df.head())

    # 2. Phân tích phổ điểm (AI Dashboard)
    st.subheader("📈 Phân tích phổ điểm môn Toán")
    fig = px.histogram(df, x="Toán_CK1", nbins=10, title="Phân phối điểm Cuối kỳ 1",
                       labels={'Toán_CK1':'Điểm số'}, color_discrete_sequence=['#00CC96'])
    st.plotly_chart(fig, use_container_width=True)

    # 3. Thuật toán dự báo (Logic đơn giản)
    st.subheader("🚨 Cảnh báo học sinh có nguy cơ")
    # Giả sử học sinh có điểm trung bình < 5 là có nguy cơ
    nguy_co = df[df['Điểm_Trung_Bình'] < 5]
    if not nguy_co.empty:
        st.warning(f"Phát hiện {len(nguy_co)} học sinh cần hỗ trợ đặc biệt!")
        st.table(nguy_co[['Họ và tên', 'Lớp', 'Điểm_Trung_Bình']])
    else:
        st.success("Tất cả học sinh đang duy trì phong độ tốt.")
if st.button("🤖 AI Nhận xét & Đề xuất giải pháp"):
    # Chuyển dữ liệu thành văn bản để gửi cho AI
    du_lieu_tom_tat = df.describe().to_string()
    
    prompt = f"""
    Bạn là chuyên gia phân tích dữ liệu giáo dục. Đây là tóm tắt điểm số của học sinh :
    {du_lieu_tom_tat}
    Hãy viết báo cáo ngắn gọn cho Hiệu trưởng gồm:
    1. Nhận xét chung về chất lượng học tập.
    2. Nếu là học sinh lớp 9Dự báo tỉ lệ đỗ vào lớp 10 dựa trên phổ điểm này.
    3. Đề xuất kế hoạch bồi dưỡng cho nhóm học sinh yếu.
    """
    # Gọi model.generate_content(prompt) giống như file Toán 10 của thầy
    # ...