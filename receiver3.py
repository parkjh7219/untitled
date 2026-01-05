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

def get_blocked_ips(cursor):
    """firewall_rules 테이블에서 실시간 차단 IP 목록을 가져옵니다."""
    cursor.execute("SELECT ip FROM firewall_rules")
    return [row['ip'] for row in cursor.fetchall()]

# UDP 소켓 설정
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9999))
print("🚀 [ATC Receiver v3] 가동 중... (방화벽 및 자동 용량 관리 활성화)")

while True:
    try:
        # 데이터 수신
        data, addr = sock.recvfrom(1024)
        raw_msg = data.decode()

        # 데이터를 IP와 메시지로 분리
        v_ip, msg = raw_msg.split("|", 1) if "|" in raw_msg else (addr[0], raw_msg)

        # DB 연결 (DictCursor 사용)
        conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

        with conn.cursor() as cur:
            # 1. 실시간 차단 목록 확인
            blocked_ips = get_blocked_ips(cur)

            if v_ip in blocked_ips:
                print(f"🚫 [보안 정책 차단] {v_ip} -> 패킷 폐기됨")
                conn.close()
                continue

            # 2. [추가] 오래된 데이터 자동 삭제 로직 (최신 1000개만 유지)
            # 이 코드는 DB 이벤트 설정 여부와 상관없이 무조건 작동하여 용량을 관리합니다.
            cleanup_sql = """
                          DELETE FROM traffic
                          WHERE id NOT IN (
                              SELECT id FROM (
                                                 SELECT id FROM traffic ORDER BY id DESC LIMIT 1000
                                             ) AS tmp
                          ) \
                          """
            cur.execute(cleanup_sql)

            # 3. 위협 등급 분류
            msg_upper = msg.upper()
            if "ATTACK" in msg_upper:
                status = "Attack"
            elif "WARN" in msg_upper:
                status = "Warning"
            elif "CAUTION" in msg_upper:
                status = "Caution"
            elif "CRITICAL" in msg_upper:
                status = "Exploit"
            else:
                status = "Normal"

            # 가짜 MAC 주소 생성
            src_mac = f"00:{random.randint(10,99)}:95:9D:{random.randint(10,99)}:16"

            # 4. 데이터 저장
            sql = """INSERT INTO traffic (ip, src_mac, dst_ip, dst_mac, protocol, port, size, msg, status)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cur.execute(sql, (v_ip, src_mac, "13.125.103.140", "00:0C:29:44:FF:01", "UDP", 9999, len(data), msg, status))

        conn.commit()
        conn.close()

        print(f"📡 [수신 완료] {v_ip} -> {status} (남은 로그: 최대 1000개)")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")