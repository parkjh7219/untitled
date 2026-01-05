import socket
import random
import time

SERVER_IP = "13.125.103.140"
PORT = 9999

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def random_ip():
    return f"{random.randint(11,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def send(ip, msg):
    sock.sendto(f"{ip}|{msg}".encode(), (SERVER_IP, PORT))

print("🚀 ATC 공격 시뮬레이터 시작")

while True:
    print("\n1 정상 | 2 DDoS | 3 스캔 | 4 미승인 | 5 침투")
    mode = input("> ")

    if mode == "1":
        send(random_ip(), "NORMAL TRAFFIC")
    elif mode == "2":
        ip = random_ip()
        for _ in range(20):
            send(ip, "[ATTACK] FLOODING")
    elif mode == "3":
        send(random_ip(), "[WARN] PORT SCANNING")
    elif mode == "4":
        send(random_ip(), "[CAUTION] UNAUTHORIZED ACCESS")
    elif mode == "5":
        send(random_ip(), "[CRITICAL] EXPLOIT SQL INJECTION")

    time.sleep(0.5)
