import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import time

# [DB 연결] 엔진 생성
@st.cache_resource
def get_engine():
    return create_engine("mysql+pymysql://admin:miniproject123456789@atc-database.cbi6ewck0l9a.ap-northeast-2.rds.amazonaws.com/ATCMAIN")

engine = get_engine()

st.set_page_config(layout="wide", page_title="ATC Advanced Console")

# [세션 상태] 차단 목록 및 알림 추적용
if 'blocked_ips' not in st.session_state:
    st.session_state['blocked_ips'] = []
if 'last_alert_id' not in st.session_state:
    st.session_state['last_alert_id'] = 0

def get_data():
    try:
        return pd.read_sql("SELECT * FROM traffic ORDER BY id DESC LIMIT 100", con=engine)
    except:
        return pd.DataFrame()

def style_text(row):
    colors = {'Attack': '#ff4b4b', 'Warning': '#ffa500', 'Caution': '#ffff00', 'Exploit': '#bf00ff'}
    color = colors.get(row['status'], '#00ff00')
    return [f'color: {color}; font-weight: bold'] * len(row)

# ---------------------------------------------------------
# [사이드바 메뉴]
# ---------------------------------------------------------
with st.sidebar:
    st.title("🛡️ ATC 메뉴")
    menu = st.radio(
        "이동할 화면을 선택하세요",
        ("📊 실시간 트래픽 요약", "📋 상세 네트워크 로그", "🚫 방화벽 설정")
    )
    st.divider()
    st.write(f"🕒 시스템 가동 중: {time.strftime('%H:%M:%S')}")

# ---------------------------------------------------------
# [데이터 처리 및 알림 로직]
# ---------------------------------------------------------
df_raw = get_data()

# 🔔 실시간 알림: 새로운 위협 패킷 탐지 시 팝업 전송
if not df_raw.empty:
    latest_record = df_raw.iloc[0]
    if latest_record['id'] > st.session_state['last_alert_id']:
        # 차단되지 않은 새로운 위험 IP만 알림
        if latest_record['status'] != 'Normal' and latest_record['ip'] not in st.session_state['blocked_ips']:
            st.toast(f"🚨 위협 감지: {latest_record['ip']} ({latest_record['status']})", icon="🔥")
        st.session_state['last_alert_id'] = latest_record['id']

# 차단 리스트 기반 필터링
df = df_raw.copy()
if not df.empty and st.session_state['blocked_ips']:
    df = df[~df['ip'].isin(st.session_state['blocked_ips'])]

# ---------------------------------------------------------
# [메인 화면 내용]
# ---------------------------------------------------------
st.title("🛰️ ATC 사이버 보안 고급 콘솔")

# 1. 요약 화면
if menu == "📊 실시간 트래픽 요약":
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("전체 패킷", f"{len(df)}개")
        c2.metric("위협 탐지", f"{len(df[df['status']!='Normal'])}개")
        c3.metric("평균 크기", f"{int(df['size'].mean())} Bytes")
        st.divider()
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            st.plotly_chart(px.line(df, x='time', y='size', title="트래픽 실시간 추이", template="plotly_dark"), use_container_width=True)
        with col2:
            st.plotly_chart(px.pie(df, names='status', title="위협 분포", hole=0.4, template="plotly_dark"), use_container_width=True)
    else:
        st.warning("📡 표시할 데이터가 없습니다.")

# 2. 상세 로그 화면
elif menu == "📋 상세 네트워크 로그":
    if not df.empty:
        st.subheader("🕵️ 상세 네트워크 패킷 로그")
        styled_df = df.style.apply(style_text, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=750)
    else:
        st.warning("📡 표시할 데이터가 없습니다.")

# 3. 방화벽 관리 화면
elif menu == "🚫 방화벽 설정":
    st.subheader("🛡️ 네트워크 방화벽(Firewall) 정책 관리")
    col_in1, col_in2 = st.columns([0.7, 0.3])
    with col_in1:
        block_ip = st.text_input("새로운 차단 IP 주소 입력", placeholder="예: 10.10.10.10")
    with col_in2:
        st.write(" ")
        st.write(" ")
        if st.button("➕ IP 추가", use_container_width=True):
            if block_ip and block_ip not in st.session_state['blocked_ips']:
                st.session_state['blocked_ips'].append(block_ip)
                st.success(f"{block_ip} 블랙리스트 등록 완료")
                time.sleep(0.5)
                st.rerun()

    st.divider()
    st.write("### 📝 현재 차단된 IP 목록 (개별 해제 가능)")
    if st.session_state['blocked_ips']:
        for i, ip in enumerate(st.session_state['blocked_ips']):
            cl1, cl2 = st.columns([0.8, 0.2])
            with cl1:
                st.info(f"🚫 {ip}")
            with cl2:
                if st.button(f"해제", key=f"del_{ip}_{i}", use_container_width=True):
                    st.session_state['blocked_ips'].remove(ip)
                    st.rerun()
    else:
        st.info("현재 차단된 IP 주소가 없습니다.")

# ---------------------------------------------------------
# 자동 새로고침 (3초 주기로 리로드)
# ---------------------------------------------------------
time.sleep(3)
st.rerun()