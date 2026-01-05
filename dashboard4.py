import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import time

@st.cache_resource
def get_engine():
    return create_engine("mysql+pymysql://admin:miniproject123456789@atc-database.cbi6ewck0l9a.ap-northeast-2.rds.amazonaws.com/ATCMAIN")

engine = get_engine()

st.set_page_config(layout="wide", page_title="ATC Console v4")

if 'last_alert_id' not in st.session_state:
    st.session_state['last_alert_id'] = 0
if 'alert_active' not in st.session_state:
    st.session_state['alert_active'] = False
if 'alert_start_time' not in st.session_state:
    st.session_state['alert_start_time'] = 0

# 새로고침 설정
refresh_interval = 500
if st.session_state['alert_active']:
    if time.time() - st.session_state['alert_start_time'] > 3:
        st.session_state['alert_active'] = False
    else:
        refresh_interval = 3000

_ = st_autorefresh(interval=refresh_interval, key="atc_refresh_v4")

def get_data():
    try: return pd.read_sql("SELECT * FROM traffic ORDER BY id DESC LIMIT 100", con=engine)
    except: return pd.DataFrame()

def get_blocked_ips():
    try: return pd.read_sql("SELECT ip FROM firewall_rules", con=engine)['ip'].tolist()
    except: return []

STATUS_COLORS = {'Normal': '#00ff00', 'Attack': '#ff4b4b', 'Warning': '#ffa500', 'Caution': '#ffff00', 'Exploit': '#bf00ff'}

# [알림 및 필터링 로직]
df_raw = get_data()
blocked_list = get_blocked_ips()

if not df_raw.empty:
    latest = df_raw.iloc[0]
    if latest['id'] > st.session_state['last_alert_id']:
        # 🛡️ 방화벽 차단 알림
        if latest['status'] == 'Blocked':
            st.toast(f"🛡️ 방화벽 작동: {latest['ip']}의 접근을 차단했습니다.", icon="🚫")
            st.session_state['alert_active'] = True
            st.session_state['alert_start_time'] = time.time()
        # 🚨 새로운 위협 알림
        elif latest['status'] != 'Normal' and latest['ip'] not in blocked_list:
            st.toast(f"🚨 위협 탐지: {latest['ip']} ({latest['status']})", icon="🔥")
            st.session_state['alert_active'] = True
            st.session_state['alert_start_time'] = time.time()
        st.session_state['last_alert_id'] = latest['id']

# [화면 필터링] Blocked 상태는 표와 그래프에서 제외
df = df_raw.copy()
df = df[df['status'] != 'Blocked']
if not df.empty and blocked_list:
    df = df[~df['ip'].isin(blocked_list)]

# [UI 구성 - 요약]
with st.sidebar:
    st.title("🛡️ ATC 메뉴 v4")
    menu = st.radio("이동할 화면", ("📊 실시간 트래픽 요약", "📋 상세 네트워크 로그", "🚫 방화벽 설정"))
    st.info(f"⏱️ 주기: {refresh_interval/1000}s")

placeholder = st.empty()
with placeholder.container():
    st.title("🛰️ ATC 사이버 보안 고급 콘솔 v4")

    if menu == "📊 실시간 트래픽 요약":
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("전체 패킷", f"{len(df)}개")
            c2.metric("위협 탐지", f"{len(df[df['status']!='Normal'])}개")
            c3.metric("평균 크기", f"{int(df['size'].mean())} B")
            st.divider()
            col1, col2 = st.columns([0.6, 0.4])
            with col1:
                fig = px.scatter(df, x='time', y='size', color='status', color_discrete_map=STATUS_COLORS, template="plotly_dark")
                fig.update_traces(mode='markers+lines', marker=dict(size=8))
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.plotly_chart(px.pie(df, names='status', hole=0.4, color='status', color_discrete_map=STATUS_COLORS, template="plotly_dark"), use_container_width=True)
        else: st.warning("📡 데이터 없음")

    elif menu == "📋 상세 네트워크 로그":
        if not df.empty:
            st.subheader("🕵️ 상세 로그 (차단 IP 제외됨)")
            st.dataframe(df.style.apply(lambda r: [f"color: {STATUS_COLORS.get(r['status'], '#00ff00')}; font-weight: bold"]*len(r), axis=1), use_container_width=True, height=750)

    elif menu == "🚫 방화벽 설정":
        st.subheader("🛡️ 실시간 방화벽 정책 관리")
        with st.form("f_form", clear_on_submit=True):
            b_ip = st.text_input("차단 IP 입력").strip()
            if st.form_submit_button("➕ 추가") and b_ip:
                try:
                    with engine.begin() as conn: conn.execute(text("INSERT IGNORE INTO firewall_rules (ip) VALUES (:ip)"), {"ip": b_ip})
                    st.success(f"{b_ip} 등록됨"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"오류: {e}")
        st.divider()
        cur_blocked = get_blocked_ips()
        for ip in cur_blocked:
            cl1, cl2 = st.columns([0.8, 0.2])
            cl1.warning(f"🚫 {ip}")
            if cl2.button("해제", key=f"del_{ip}"):
                with engine.begin() as conn: conn.execute(text("DELETE FROM firewall_rules WHERE ip=:ip"), {"ip": ip})
                st.rerun()