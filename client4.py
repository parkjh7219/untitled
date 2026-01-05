import socket
import time
import random

# [환경 설정] 수신기가 실행 중인 서버의 IP로 수정하세요.
SERVER_IP = "127.0.0.1"
PORT = 9999
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 정상 통신용 IP 대역
normal_ips = [f"192.168.1.{i}" for i in range(10, 20)]

def send_packet(ip, msg):
    """IP와 메시지를 결합하여 UDP 패킷 전송"""
    data = f"{ip}|{msg}"
    sock.sendto(data.encode(), (SERVER_IP, PORT))

print("🚀 [ATC Client v4] 시뮬레이션 시작")
print("-" * 40)
print("1: 정상 통신 (Random IP)")
print("2: DDoS 공격 (Fixed: 10.10.10.10)")
print("3: 포트 스캔 (Random IP - 대역 탐지)")
print("4: 미승인 접근 (Fixed: 221.180.1.5)")
print("5: 시스템 침투 (Fixed: 45.12.88.99)")
print("Ctrl+C를 누르면 종료됩니다.")
print("-" * 40)

try:
    while True:
        mode = input("\n관제 모드 선택 > ")

        if mode == '1':
            v_ip = random.choice(normal_ips)
            send_packet(v_ip, f"ID:ATC-{random.randint(100,999)}, Status:Active")
            print(f"[-] 정상 데이터 전송: {v_ip}")

        elif mode == '2':
            atk_ip = "10.10.10.10"
            print(f"[!] DDoS 공격 패킷 송신 중: {atk_ip}")
            for _ in range(15):
                send_packet(atk_ip, "[ATTACK] UDP FLOODING")
                time.sleep(0.05)

        elif mode == '3':
            # 포트 스캔은 특성상 여러 IP가 섞여 들어오도록 랜덤 유지
            scan_ip = f"172.16.{random.randint(0,255)}.{random.randint(0,255)}"
            send_packet(scan_ip, "[WARN] PORT SCANNING")
            print(f"[?] 정찰 활동 감지: {scan_ip}")

        elif mode == '4':
            # 방화벽 테스트용 고정 IP
            target_ip = "221.180.1.5"
            send_packet(target_ip, "[CAUTION] UNAUTHORIZED ACCESS ATTEMPT")
            print(f"[!] 미승인 접근 시도: {target_ip}")

        elif mode == '5':
            # 침투 공격 고정 IP
            exploit_ip = "45.12.88.99"
            send_packet(exploit_ip, "[CRITICAL] SQL INJECTION / EXPLOIT")
            print(f"[☠️] 치명적 침투 공격: {exploit_ip}")

        else:
            print("❌ 잘못된 입력입니다. 1~5 사이의 숫자를 입력하세요.")

        time.sleep(0.3)

except KeyboardInterrupt:
    print("\n시뮬레이션을 안전하게 종료합니다.")