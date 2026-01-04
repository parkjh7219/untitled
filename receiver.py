import socket
import pymysql
import random

DB_CONFIG = {
    'host': 'atc-main.cpwsus2yubp1.ap-northeast-2.rds.amazonaws.com',
    'user': 'ATCMAIN', 'password': 'atc12345!', 'db': 'ATCMAIN', 'charset': 'utf8mb4'
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9999))
print("🚀 [ATC Receiver] 가동 중... (데이터 수집 시작)")

while True:
    try:
        data, addr = sock.recvfrom(1024)
        raw_msg = data.decode()
        v_ip, msg = raw_msg.split("|", 1) if "|" in raw_msg else (addr[0], raw_msg)

        status = "Attack" if "ATTACK" in msg.upper() else "Normal"
        src_mac = f"00:{random.randint(10,99)}:95:9D:{random.randint(10,99)}:16"

        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            # 11개 필드 순서 정확히 일치2
            sql = """INSERT INTO traffic (ip, src_mac, dst_ip, dst_mac, protocol, port, size, msg, status)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cur.execute(sql, (v_ip, src_mac, "13.125.103.140", "00:0C:29:44:FF:01", "UDP", 9999, len(data), msg, status))
        conn.commit()
        conn.close()
        print(f"📡 [저장 완료] {v_ip} -> {status}")
    except Exception as e:
        print(f"❌ 에러: {e}")