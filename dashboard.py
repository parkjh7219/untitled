import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import time

# DB 연결 1
engine = create_engine("mysql+pymysql://ATCMAIN:atc12345!@atc-main.cpwsus2yubp1.ap-northeast-2.rds.amazonaws.com/ATCMAIN")

st.set_page_config(layout="wide", page_title="ATC Advanced Console")
st.title("🛰️ ATC Cyber Security Advanced Console")

def get_data():
    try:
        return pd.read_sql("SELECT * FROM traffic ORDER BY id DESC LIMIT 100", con=engine)
    except:
        return pd.DataFrame()

df = get_data()

if not df.empty:
    # [1번: 요약]
    c1, c2, c3 = st.columns(3)
    c1.metric("전체 패킷", f"{len(df)}개")
    c2.metric("위협 탐지", f"{len(df[df['status']=='Attack'])}개")
    c3.metric("평균 패킷 크기", f"{int(df['size'].mean())} Bytes")

    # [2, 3번: 시각화]
    col1, col2 = st.columns([0.6, 0.4])
    with col1:
        st.plotly_chart(px.line(df, x='time', y='size', title="실시간 트래픽 밀도", template="plotly_dark"), use_container_width=True)
    with col2:
        st.plotly_chart(px.pie(df, names='status', title="공격 분포", hole=0.4, template="plotly_dark"), use_container_width=True)

    # [4번: 상세 로그]
    st.subheader("📋 실시간 상세 네트워크 로그 (Packet Inspection)")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("📡 수신된 데이터가 없습니다. 클라이언트를 조작해 보세요.")

time.sleep(2)
st.rerun()