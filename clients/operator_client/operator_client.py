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
        # Usamos un candado para que si tenemos varios hilos queriendo hablar con el 
        # servidor principal al mismo tiempo, no se "pisen" los mensajes.
        self._lock = __import__("threading").Lock()

    def connect(self):
        """Establece la conexión de larga duración con el servidor de operaciones."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        return f"[INFO] Conectado al servidor {self.host}:{self.port}"

    def _login_sock(self):
        """Helper para abrir una conexión rápida con el servidor de autenticación."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.login_host, self.login_port))
        return s

    def login(self, username, password):
        """Intenta autenticar al usuario y guarda las credenciales de sesión."""
        s = self._login_sock()
        try:
            # Enviamos credenciales en formato plano 
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
        """Renueva el token actual usando el refresh_token."""
        if not self.user_id:
            raise RuntimeError("¡Ni siquiera has iniciado sesión!")
        s = self._login_sock()
        try:
            s.sendall(
                f"VALIDATE|{self.user_id}|{self.token}|{self.refresh_token}\n".encode()
            )
            resp = s.recv(4096).decode().strip()
            if resp.startswith("OK|VALIDATE"):
                p = resp.split("|")
                # Actualizamos los tokens con los nuevos que nos da el servidor
                self.token = p[2]
                self.refresh_token = p[3]
            return resp
        finally:
            s.close()

    def logout(self):
        """Informa al servidor de login que cerramos sesión y limpia el cliente."""
        if not self.user_id:
            return "[INFO] No hay sesión activa para cerrar."
        s = self._login_sock()
        try:
            s.sendall(
                f"LOGOUT|{self.user_id}|{self.token}|{self.refresh_token}\n".encode()
            )
            resp = s.recv(4096).decode().strip()
            # Limpiamos todo rastro de la sesión localmente
            self.user_id = self.token = self.refresh_token = None
            self.role = "Sin rol"
            return resp
        finally:
            s.close()

    def send_command(self, msg):
        """
        Envía un comando al servidor de operaciones y espera la respuesta.
        Implementa un pequeño buffer para no perder datos en respuestas largas.
        """
        with self._lock: 
            self.sock.sendall((msg.strip() + "\n").encode())
            
            # Ponemos un timeout corto para que el loop de lectura no se quede "colgado"
            # esperando datos que nunca llegarán si el servidor termina de enviar.
            self.sock.settimeout(1.5)
            chunks = []
            try:
                while True:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
            except socket.timeout:
                # El timeout es normal aquí, significa que ya no hay más datos por ahora
                pass
            finally:
                self.sock.settimeout(None) # Quitamos el timeout para la próxima
            
            return b"".join(chunks).decode().strip()

    # --- Comandos de Operación ---

    def get_sensors(self):
        return self.send_command("GET_SENSORS")

    def get_alerts(self):
        return self.send_command("GET_ALERTS")

    def get_readings(self, sid):
        return self.send_command(f"GET_READINGS {sid}")

    def ack_alert(self, aid):
        """Confirma una alerta específica."""
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
    # Configuración de argumentos desde la terminal
    parser = argparse.ArgumentParser(description="Cliente de Operador para el Sistema")
    parser.add_argument("mode", choices=["console"], help="Modo de ejecución")
    parser.add_argument("--host", default="localhost", help="IP del servidor de operaciones")
    parser.add_argument("--port", type=int, default=5000, help="Puerto de operaciones")
    parser.add_argument("--login-host", default="localhost", help="IP del servidor de login")
    parser.add_argument("--login-port", type=int, default=6000, help="Puerto de login")
    args = parser.parse_args()

    client = OperatorClient(args.host, args.port, args.login_host, args.login_port)
    
    # Intentamos la conexión inicial
    try:
        print(client.connect())
    except Exception as e:
        print(f"[ERROR] No se pudo conectar: {e}")
        sys.exit(1)

    if args.mode == "console":
        print("\n--- Interfaz de Control del Operador ---")
        print("Escribe 'ayuda' para ver qué puedes hacer.")
        
        while True:
            try:
                # Capturamos la entrada y evitamos rompernos con espacios vacíos
                line = input("> ").strip()
                if not line: continue
                
                parts = line.split()
                cmd = parts[0].lower()
                
                # --- Lógica de la CLI ---
                if cmd == "ayuda":
                    print("\nComandos disponibles:")
                    print("  login <user> <pass> | validate | logout")
                    print("  sensors             | readings <id>")
                    print("  alerts              | ack <id>       | clear")
                    print("  status              | pause          | resume")
                    print("  salir\n")
                
                elif cmd == "login":
                    if len(parts) < 3:
                        print("Uso: login <usuario> <password>")
                    else:
                        print(client.login(parts[1], parts[2]))
                
                elif cmd == "validate":
                    print(client.validate())
                
                elif cmd == "logout":
                    print(client.logout())
                
                elif cmd == "sensors":
                    print(client.get_sensors())
                
                elif cmd == "alerts":
                    print(client.get_alerts())
                
                elif cmd == "readings":
                    if len(parts) < 2:
                        print("Falta el ID del sensor.")
                    else:
                        print(client.get_readings(parts[1]))
                
                elif cmd == "ack":
                    if len(parts) < 2:
                        print("Falta el ID de la alerta.")
                    else:
                        print(client.ack_alert(parts[1]))
                
                elif cmd == "clear":
                    print(client.clear_alerts())
                
                elif cmd == "status":
                    print(client.get_system_status())
                
                elif cmd == "pause":
                    print(client.pause_simulation())
                
                elif cmd == "resume":
                    print(client.resume_simulation())
                
                elif cmd == "salir":
                    print("Cerrando cliente...")
                    break
                else:
                    print(f"'{cmd}' no es un comando válido. Prueba con 'ayuda'.")
            
            except EOFError: # Captura Ctrl+D
                break
            except Exception as e:
                print(f"[ERROR EN COMANDO] {e}")

if __name__ == "__main__":
    main()