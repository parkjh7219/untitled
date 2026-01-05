import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import time

# ===============================
# DB 연결
# ===============================
engine = create_engine(
    "mysql+pymysql://ATCMAIN:atc12345!@atc-main.cpwsus2yubp1.ap-northeast-2.rds.amazonaws.com/ATCMAIN",
    future=True
)

st.set_page_config(
    layout="wide",
    page_title="ATC Cyber Security Advanced Console",
    page_icon="🛰️"
)

# ===============================
# 상태 색상
# ===============================
def style_row(row):
    color_map = {
        'Normal': 'color:#00FF88;',
        'DDoS': 'color:#FF4B4B;',
        'Scanning': 'color:#E67E22;',
        'Unauthorized': 'color:#F1C40F;',
        'Exploit': 'color:#9B59B6;'
    }
    return [color_map.get(row['status'], '')] * len(row)

# ===============================
# 트래픽 데이터 로드
# ===============================
def load_traffic():
    try:
        with engine.connect() as conn:
            return pd.read_sql(
                text("SELECT * FROM traffic ORDER BY id DESC LIMIT 100"),
                conn
            )
    except:
        return pd.DataFrame()

st.title("🛰️ ATC Cyber Security Advanced Console")

df = load_traffic()

if df.empty:
    st.info("📡 데이터 수신 대기 중...")
    time.sleep(2)
    st.rerun()

# ===============================
# 상단 요약 지표
# ===============================
m1, m2, m3, m4 = st.columns(4)
m1.metric("총 수신 패킷", f"{len(df)} Pkts")
m2.metric("위협 탐지", f"{len(df[df['status'] != 'Normal'])} 건")
m3.metric("평균 패킷 크기", f"{int(df['size'].mean())} B")
m4.metric("시스템 상태", "ACTIVE", delta="Secure")

st.divider()

# ===============================
# 탭 구성
# ===============================
tab1, tab2, tab3 = st.tabs([
    "📈 실시간 트래픽 밀도",
    "📋 실시간 상세 로그",
    "🚫 IP 차단 / 블랙리스트"
])

# ===============================
# TAB 1 : 실시간 트래픽
# ===============================
with tab1:
    fig = px.line(
        df,
        x="time",
        y="size",
        color="status",
        color_discrete_map={
            'Normal':'#00FF88',
            'DDoS':'#FF4B4B',
            'Scanning':'#E67E22',
            'Unauthorized':'#F1C40F',
            'Exploit':'#9B59B6'
        },
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

# ===============================
# TAB 2 : 상세 로그
# ===============================
with tab2:
    st.dataframe(
        df.style.apply(style_row, axis=1),
        use_container_width=True,
        height=500
    )

# ===============================
# TAB 3 : IP 차단 / 블랙리스트
# ===============================
with tab3:
    st.subheader("🚫 수동 아이피 차단")

    c1, c2 = st.columns(2)
    with c1:
        b_ip = st.text_input("차단할 IP")
    with c2:
        b_reason = st.text_input("차단 사유", value="관리자 수동 차단")

    if st.button("즉시 차단"):
        if b_ip:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                         INSERT INTO blacklist (ip, reason)
                         VALUES (:ip, :reason)
                             ON DUPLICATE KEY UPDATE reason = :reason
                         """),
                    {"ip": b_ip, "reason": b_reason}
                )
            st.success(f"✅ {b_ip} 차단 완료")

    st.divider()
    st.subheader("📛 블랙리스트 목록")

    try:
        with engine.connect() as conn:
            bl_df = pd.read_sql(
                text("SELECT ip, reason FROM blacklist ORDER BY ip"),
                conn
            )

        if bl_df.empty:
            st.info("블랙리스트 데이터 없음")
        else:
            st.dataframe(bl_df, use_container_width=True)

    except Exception as e:
        st.error(f"블랙리스트 조회 오류: {e}")

# ===============================
# 자동 새로고침
# ===============================
time.sleep(2)
st.rerun()
