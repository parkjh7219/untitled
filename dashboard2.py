import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import time

# [DB 연결] 엔진 생성
@st.cache_resource
def get_engine():
    return create_engine("mysql+pymysql://admin:miniproject123456789@atc-database.cbi6ewck0l9a.ap-northeast-2.rds.amazonaws.com/ATCMAIN")

engine = get_engine()

st.set_page_config(layout="wide", page_title="ATC Advanced Console")

# [세션 상태 초기화]
if 'blocked_ips' not in st.session_state:
    st.session_state['blocked_ips'] = []
if 'last_alert_id' not in st.session_state:
    st.session_state['last_alert_id'] = 0
if 'alert_active' not in st.session_state:
    st.session_state['alert_active'] = False
if 'alert_start_time' not in st.session_state:
    st.session_state['alert_start_time'] = 0

# ---------------------------------------------------------
# [새로고침 주기 제어]
# ---------------------------------------------------------
refresh_interval = 500
if st.session_state['alert_active']:
    elapsed_time = time.time() - st.session_state['alert_start_time']
    if elapsed_time > 3:
        st.session_state['alert_active'] = False
    else:
        refresh_interval = 3000

_ = st_autorefresh(interval=refresh_interval, key="atc_refresh")

def get_data():
    try:
        return pd.read_sql("SELECT * FROM traffic ORDER BY id DESC LIMIT 100", con=engine)
    except:
        return pd.DataFrame()

# [중요] 상태별 고정 색상 맵 정의
STATUS_COLORS = {
    'Normal': '#00ff00',   # 초록
    'Attack': '#ff4b4b',   # 빨강
    'Warning': '#ffa500',  # 주황
    'Caution': '#ffff00',  # 노랑
    'Exploit': '#bf00ff'   # 보라
}

def style_text(row):
    color = STATUS_COLORS.get(row['status'], '#00ff00')
    return [f'color: {color}; font-weight: bold'] * len(row)

# ---------------------------------------------------------
# [데이터 처리 및 알림]
# ---------------------------------------------------------
df_raw = get_data()

if not df_raw.empty:
    latest_record = df_raw.iloc[0]
    if latest_record['id'] > st.session_state['last_alert_id']:
        if latest_record['status'] != 'Normal' and latest_record['ip'] not in st.session_state['blocked_ips']:
            st.toast(f"🚨 위협 감지: {latest_record['ip']} ({latest_record['status']})", icon="🔥")
            st.session_state['alert_active'] = True
            st.session_state['alert_start_time'] = time.time()
        st.session_state['last_alert_id'] = latest_record['id']

df = df_raw.copy()
if not df.empty and st.session_state['blocked_ips']:
    df = df[~df['ip'].isin(st.session_state['blocked_ips'])]

# ---------------------------------------------------------
# [메인 화면 내용]
# ---------------------------------------------------------
with st.sidebar:
    st.title("🛡️ ATC 메뉴")
    menu = st.radio("이동할 화면을 선택하세요", ("📊 실시간 트래픽 요약", "📋 상세 네트워크 로그", "🚫 방화벽 설정"))
    st.divider()
    st.info(f"⏱️ 현재 갱신 주기: {refresh_interval/1000}초")

placeholder = st.empty()

with placeholder.container():
    st.title("🛰️ ATC 사이버 보안 고급 콘솔")

    if menu == "📊 실시간 트래픽 요약":
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("전체 패킷", f"{len(df)}개")
            c2.metric("위협 탐지", f"{len(df[df['status']!='Normal'])}개")
            c3.metric("평균 크기", f"{int(df['size'].mean())} Bytes")

            st.divider()
            col1, col2 = st.columns([0.6, 0.4])
            with col1:
                # [수정된 부분] 산점도(Scatter)를 사용하여 패킷별 색상 구분
                fig = px.scatter(
                    df,
                    x='time',
                    y='size',
                    color='status',
                    title="트래픽 실시간 추이 (등급별 색상)",
                    color_discrete_map=STATUS_COLORS, # 위에서 정의한 색상 적용
                    template="plotly_dark"
                )
                # 점들을 선으로 가볍게 연결하여 흐름 표시 (선택 사항)
                fig.update_traces(mode='markers+lines', marker=dict(size=8))
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.plotly_chart(px.pie(df, names='status', title="위협 분포", hole=0.4,
                                       color='status', color_discrete_map=STATUS_COLORS,
                                       template="plotly_dark"), use_container_width=True)
        else:
            st.warning("📡 표시할 데이터가 없습니다.")

    elif menu == "📋 상세 네트워크 로그":
        if not df.empty:
            st.subheader("🕵️ 상세 네트워크 패킷 로그")
            styled_df = df.style.apply(style_text, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=750)
        else:
            st.warning("📡 표시할 데이터가 없습니다.")

    elif menu == "🚫 방화벽 설정":
        st.subheader("🛡️ 네트워크 방화벽(Firewall) 정책 관리")
        with st.form("firewall_form", clear_on_submit=True):
            block_ip = st.text_input("새로운 차단 IP 주소 입력", placeholder="예: 10.10.10.10")
            submit = st.form_submit_button("➕ IP 추가")
            if submit and block_ip:
                if block_ip not in st.session_state['blocked_ips']:
                    st.session_state['blocked_ips'].append(block_ip)
                    st.success(f"{block_ip} 등록 완료")
                    st.rerun()

        st.divider()
        st.write("### 📝 현재 차단된 IP 목록")
        if st.session_state['blocked_ips']:
            for ip in st.session_state['blocked_ips']:
                cl1, cl2 = st.columns([0.8, 0.2])
                cl1.info(f"🚫 {ip}")
                if cl2.button(f"해제", key=f"del_{ip}"):
                    st.session_state['blocked_ips'].remove(ip)
                    st.rerun()
        else:
            st.info("현재 차단된 IP 주소가 없습니다.")