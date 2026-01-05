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
    cursor.execute("SELECT ip FROM firewall_rules")
    return [row['ip'] for row in cursor.fetchall()]

# UDP 소켓 설정
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9999))
print("🚀 [ATC Receiver v4] 가동 중... (차단 알림 연동 및 용량 관리 활성화)")

while True:
    try:
        data, addr = sock.recvfrom(1024)
        raw_msg = data.decode()
        v_ip, msg = raw_msg.split("|", 1) if "|" in raw_msg else (addr[0], raw_msg)

        conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

        with conn.cursor() as cur:
            # 1. 용량 관리 (최신 1000개 유지)
            cleanup_sql = """
                          DELETE FROM traffic
                          WHERE id NOT IN (
                              SELECT id FROM (
                                                 SELECT id FROM traffic ORDER BY id DESC LIMIT 1000
                                             ) AS tmp
                          ) \
                          """
            cur.execute(cleanup_sql)

            # 2. 실시간 차단 목록 확인
            blocked_ips = get_blocked_ips(cur)

            # [방화벽 작동 로직 수정]
            if v_ip in blocked_ips:
                print(f"🚫 [방화벽 작동] {v_ip} 차단 및 알림 전송 준비")
                status = "Blocked"
                msg = "[FIREWALL] ACCESS DENIED"
                src_mac = "00:00:00:00:00:00"

                # 차단된 이력을 DB에 저장 (대시보드 알람용)
                sql = """INSERT INTO traffic (ip, src_mac, dst_ip, dst_mac, protocol, port, size, msg, status)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                cur.execute(sql, (v_ip, src_mac, "13.125.103.140", "00:0C:29:44:FF:01", "UDP", 9999, len(data), msg, status))
                conn.commit()
                conn.close()
                continue

            # 3. 정상/위협 분류 및 저장 (기존 로직)
            msg_upper = msg.upper()
            if "ATTACK" in msg_upper: status = "Attack"
            elif "WARN" in msg_upper: status = "Warning"
            elif "CAUTION" in msg_upper: status = "Caution"
            elif "CRITICAL" in msg_upper: status = "Exploit"
            else: status = "Normal"

            src_mac = f"00:{random.randint(10,99)}:95:9D:{random.randint(10,99)}:16"
            sql = """INSERT INTO traffic (ip, src_mac, dst_ip, dst_mac, protocol, port, size, msg, status)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cur.execute(sql, (v_ip, src_mac, "13.125.103.140", "00:0C:29:44:FF:01", "UDP", 9999, len(data), msg, status))

        conn.commit()
        conn.close()
        print(f"📡 [수신] {v_ip} -> {status}")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")