import socket
import pymysql
import random

DB = {
    "host": "atc-main.cpwsus2yubp1.ap-northeast-2.rds.amazonaws.com",
    "user": "ATCMAIN",
    "password": "atc12345!",
    "db": "ATCMAIN",
    "charset": "utf8mb4"
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9999))

print("🚀 ATC Receiver 가동 중")

while True:
    data, addr = sock.recvfrom(1024)
    raw = data.decode()
    ip, msg = raw.split("|", 1)

    msg_u = msg.upper()
    if "FLOOD" in msg_u:
        status = "DDoS"
    elif "SCAN" in msg_u:
        status = "Scanning"
    elif "UNAUTHORIZED" in msg_u:
        status = "Unauthorized"
    elif "EXPLOIT" in msg_u or "SQL" in msg_u:
        status = "Exploit"
    else:
        status = "Normal"

    conn = pymysql.connect(**DB)
    with conn.cursor() as cur:
        cur.execute("""
                    INSERT INTO traffic
                        (ip, src_mac, dst_ip, dst_mac, protocol, port, size, msg, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        ip,
                        f"00:{random.randint(10,99)}:95:9D:{random.randint(10,99)}:16",
                        "13.125.103.140",
                        "00:0C:29:44:FF:01",
                        "UDP",
                        9999,
                        len(data),
                        msg,
                        status
                    ))
    conn.commit()
    conn.close()

    print(f"[저장] {ip} | {status}")
