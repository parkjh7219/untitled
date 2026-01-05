import socket
import time
import random

SERVER_IP = "127.0.0.1" # 수신기의 엔드포인트 IP로 수정 필요
PORT = 9999
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

normal_ips = [f"192.168.1.{i}" for i in range(10, 20)]

def send_packet(ip, msg):
    data = f"{ip}|{msg}"
    sock.sendto(data.encode(), (SERVER_IP, PORT))

print("🚀 ATC 고도화 시뮬레이션 (client3)")
print("1: 정상, 2: DDoS, 3: 포트스캔(랜덤), 4: 미승인(고정: 221.180.1.5), 5: 침투")

try:
    while True:
        mode = input("\n관제 모드 선택 > ")
        if mode == '1':
            send_packet(random.choice(normal_ips), f"ID:KE{random.randint(100,999)}, ALT:{random.randint(30000,40000)}ft")
        elif mode == '2':
            for _ in range(20): send_packet("10.10.10.10", "[ATTACK] FLOODING")
        elif mode == '3':
            send_packet(f"172.16.{random.randint(0,255)}.{random.randint(0,255)}", "[WARN] PORT SCANNING")
        elif mode == '4':
            send_packet("221.180.1.5", "[CAUTION] UNAUTHORIZED ACCESS")
            print(f"[!] 고정 IP 송신: 221.180.1.5")
        elif mode == '5':
            send_packet("45.12.88.99", "[CRITICAL] EXPLOIT / SQLi")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\n종료")