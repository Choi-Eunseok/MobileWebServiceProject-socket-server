import os
import socket
from datetime import datetime

class SocketServer:
    def __init__(self):
        self.bufsize = 1024  # 버퍼 크기 설정
        with open('./response.bin', 'rb') as file:
            self.RESPONSE = file.read()  # 응답 파일 읽기

        self.DIR_PATH = './request'
        self.createDir(self.DIR_PATH)

    def createDir(self, path):
        """디렉토리 생성"""
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError:
            print("Error: Failed to create the directory.")

    def run(self, ip, port):
        """서버 실행"""
        # 소켓 생성
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen(10)
        print("Start the socket server...")
        print("\"Ctrl+C\" for stopping the server!\r\n")

        try:
            while True:
                # 클라이언트의 요청 대기
                clnt_sock, req_addr = self.sock.accept()
                clnt_sock.settimeout(5.0)  # 타임아웃 설정 (5초)
                print("Request message...\r\n")

                response = b""

                # Request 데이터 수신
                while True:
                    try:
                        data = clnt_sock.recv(self.bufsize)

                        if not data:
                            break

                        response += data

                        # HTTP Header와 Body 분리
                        if b"\r\n\r\n" in response:
                            header, body = response.split(b"\r\n\r\n", 1)

                            # Content-Length 확인
                            content_length = 0

                            for line in header.split(b"\r\n"):
                                if line.lower().startswith(b"content-length:"):
                                    content_length = int(
                                        line.split(b":", 1)[1].strip()
                                    )
                                    break

                            # Body를 모두 받았으면 종료
                            if len(body) >= content_length:
                                break

                    except socket.timeout:
                        break

                # -------------------------
                # 실습 1
                # Request 전체를 bin 파일로 저장
                # -------------------------

                now = datetime.now()
                filename = now.strftime("%Y-%m-%d-%H-%M-%S.bin")
                filepath = os.path.join(self.DIR_PATH, filename)

                with open(filepath, "wb") as file:
                    file.write(response)

                print(f"Request saved: {filepath}")

                # -------------------------
                # 실습 2
                # multipart 이미지 추출
                # -------------------------

                try:
                    header, body = response.split(b"\r\n\r\n", 1)

                    # boundary 찾기
                    boundary = None

                    for line in header.split(b"\r\n"):
                        if line.lower().startswith(b"content-type:") \
                                and b"boundary=" in line:
                            boundary = line.split(b"boundary=", 1)[1].strip()
                            break

                    if boundary:
                        # multipart의 각 파트 분리
                        parts = body.split(b"--" + boundary)

                        for part in parts:

                            if b'filename="' not in part:
                                continue

                            # 각 multipart의 header/body 분리
                            part_header, file_data = part.split(
                                b"\r\n\r\n", 1
                            )

                            # filename 추출
                            filename_part = part_header.split(
                                b'filename="', 1
                            )[1]

                            image_filename = filename_part.split(
                                b'"', 1
                            )[0].decode("utf-8")

                            # multipart 끝의 CRLF 제거
                            if file_data.endswith(b"\r\n"):
                                file_data = file_data[:-2]

                            image_path = os.path.join(
                                self.DIR_PATH,
                                image_filename
                            )

                            with open(image_path, "wb") as image_file:
                                image_file.write(file_data)

                            print(f"Image saved: {image_path}")

                except Exception as e:
                    print(f"Multipart parsing error: {e}")

                # 응답 전송
                clnt_sock.sendall(self.RESPONSE)

                # 클라이언트 소켓 닫기
                clnt_sock.close()
        except KeyboardInterrupt:
            print("\r\nStop the server...")

        # 서버 소켓 닫기
        self.sock.close()

if __name__ == "__main__":
    server = SocketServer()
    server.run("127.0.0.1", 8000)
