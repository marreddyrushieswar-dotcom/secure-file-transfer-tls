import socket
import ssl
import threading
import os
import hashlib

SERVER_IP = "0.0.0.0"
PORT = 5000
CHUNK_SIZE = 4096

os.makedirs("storage", exist_ok=True)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()

def handle_client(conn, addr):
    print(f"[+] Connected from {addr}")
    try:
        # 1️⃣ Receive filename
        filename = conn.recv(1024).decode().strip()
        filepath = os.path.join("storage", "received_" + filename)

        # 2️⃣ Resume support
        offset = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        conn.sendall(str(offset).encode())

        # 3️⃣ Receive file data
        with open(filepath, "ab") as f:
            while True:
                data = conn.recv(CHUNK_SIZE)
                if data == b"EOF":
                    break
                f.write(data)

        # 4️⃣ Send file hash
        conn.sendall(sha256_file(filepath).encode())
        print(f"[✓] Received {filename}")

    except Exception as e:
        print("Error:", e)

    conn.close()

def main():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain("server.crt", "server.key")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((SERVER_IP, PORT))
    sock.listen(5)

    print("Secure TCP/TLS server running...")

    with context.wrap_socket(sock, server_side=True) as ssock:
        while True:
            client, addr = ssock.accept()
            threading.Thread(
                target=handle_client,
                args=(client, addr),
                daemon=True
            ).start()

if __name__ == "__main__":
    main()