#!/usr/bin/env python3
import socket, argparse, sys


class OperatorClient:
    def __init__(self, host, port, login_host, login_port):
        self.host = host
        self.port = port
        self.login_host = login_host
        self.login_port = login_port
        self.sock = None
        self.user_id = None
        self.token = None
        self.refresh_token = None
        self.role = "Sin rol"
        self._lock = __import__("threading").Lock()  # Mutex para el socket compartido

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        return f"[INFO] Conectado al servidor {self.host}:{self.port}"

    def _login_sock(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.login_host, self.login_port))
        return s

    def login(self, username, password):
        s = self._login_sock()
        try:
            s.sendall(f"LOGIN|{username}|{password}\n".encode())
            resp = s.recv(4096).decode().strip()
            if resp.startswith("OK|LOGIN"):
                p = resp.split("|")
                self.user_id = p[2]
                self.token = p[3]
                self.refresh_token = p[4]
                self.role = "admin"
            return resp
        finally:
            s.close()

    def validate(self):
        if not self.user_id:
            raise RuntimeError("Debe hacer login primero")
        s = self._login_sock()
        try:
            s.sendall(
                f"VALIDATE|{self.user_id}|{self.token}|{self.refresh_token}\n".encode()
            )
            resp = s.recv(4096).decode().strip()
            if resp.startswith("OK|VALIDATE"):
                p = resp.split("|")
                self.token = p[2]
                self.refresh_token = p[3]
            return resp
        finally:
            s.close()

    def logout(self):
        if not self.user_id:
            return "[INFO] No hay sesion activa"
        s = self._login_sock()
        try:
            s.sendall(
                f"LOGOUT|{self.user_id}|{self.token}|{self.refresh_token}\n".encode()
            )
            resp = s.recv(4096).decode().strip()
            self.user_id = self.token = self.refresh_token = None
            self.role = "Sin rol"
            return resp
        finally:
            s.close()

    def send_command(self, msg):
        with self._lock:  # Serializa acceso al socket — evita race condition entre hilos
            self.sock.sendall((msg.strip() + "\n").encode())
            # Leer en loop con timeout para capturar toda la respuesta TCP
            self.sock.settimeout(1.5)
            chunks = []
            try:
                while True:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
            except Exception:
                pass
            finally:
                self.sock.settimeout(None)
            return b"".join(chunks).decode().strip()

    def get_sensors(self):
        return self.send_command("GET_SENSORS")

    def get_alerts(self):
        return self.send_command("GET_ALERTS")

    def get_readings(self, sid):
        return self.send_command(f"GET_READINGS {sid}")

    def ack_alert(self, aid):
        return self.send_command(f"ACK_ALERT {aid}")

    def clear_alerts(self):
        return self.send_command("CLEAR_ALERTS")

    def get_system_status(self):
        return self.send_command("SYSTEM_STATUS")

    def pause_simulation(self):
        return self.send_command("PAUSE_SIMULATION")

    def resume_simulation(self):
        return self.send_command("RESUME_SIMULATION")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["console"])
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--login-host", default="localhost")
    parser.add_argument("--login-port", type=int, default=6000)
    args = parser.parse_args()

    client = OperatorClient(args.host, args.port, args.login_host, args.login_port)
    try:
        print(client.connect())
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if args.mode == "console":
        print("Modo consola - 'ayuda' para ver comandos")
        while True:
            try:
                cmd = input("> ").strip()
            except:
                break
            if not cmd:
                continue
            p = cmd.split()
            c = p[0].lower()
            try:
                if c == "ayuda":
                    print(
                        "\nlogin <u> <p> | validate | logout | sensors | alerts | readings <id> | ack <id> | clear | status | pause | resume | salir\n"
                    )
                elif c == "login":
                    print(client.login(p[1], p[2]))
                elif c == "validate":
                    print(client.validate())
                elif c == "logout":
                    print(client.logout())
                elif c == "sensors":
                    print(client.get_sensors())
                elif c == "alerts":
                    print(client.get_alerts())
                elif c == "readings":
                    print(client.get_readings(p[1]))
                elif c == "ack":
                    print(client.ack_alert(p[1]))
                elif c == "clear":
                    print(client.clear_alerts())
                elif c == "status":
                    print(client.get_system_status())
                elif c == "pause":
                    print(client.pause_simulation())
                elif c == "resume":
                    print(client.resume_simulation())
                elif c == "salir":
                    break
                else:
                    print("Comando no reconocido. Escribe 'ayuda'.")
            except Exception as e:
                print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
