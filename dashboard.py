import socket
import pymysql
import random

# [DB 연결 설정]
DB_CONFIG = {
    'host': 'atc-database.cbi6ewck0l9a.ap-northeast-2.rds.amazonaws.com',
    'user': 'admin',
    'password': 'miniproject123456789',
    'db': 'ATCMAIN',
    'charset': 'utf8mb4'
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9999))
print("🚀 [ATC Receiver] 가동 중... (실시간 위협 분류 시스템 활성화)")

while True:
    try:
        data, addr = sock.recvfrom(1024)
        raw_msg = data.decode()

        # 데이터를 IP와 메시지로 분리
        v_ip, msg = raw_msg.split("|", 1) if "|" in raw_msg else (addr[0], raw_msg)

        # 메시지 키워드에 따른 위협 등급 분류
        msg_upper = msg.upper()
        if "ATTACK" in msg_upper:
            status = "Attack"    # 2번: DDoS (빨강)
        elif "WARN" in msg_upper:
            status = "Warning"   # 3번: 포트 스캔 (주황)
        elif "CAUTION" in msg_upper:
            status = "Caution"   # 4번: 미승인 접근 (노랑)
        elif "CRITICAL" in msg_upper:
            status = "Exploit"   # 5번: 시스템 침투 (보라)
        else:
            status = "Normal"    # 1번: 정상 (초록)

        # 가짜 MAC 주소 생성 (랜덤)
        src_mac = f"00:{random.randint(10,99)}:95:9D:{random.randint(10,99)}:16"

        # DB 저장
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            sql = """INSERT INTO traffic (ip, src_mac, dst_ip, dst_mac, protocol, port, size, msg, status)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cur.execute(sql, (v_ip, src_mac, "13.125.103.140", "00:0C:29:44:FF:01", "UDP", 9999, len(data), msg, status))
        conn.commit()
        conn.close()

        print(f"📡 [수신] {v_ip} -> {status} ({msg})")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")