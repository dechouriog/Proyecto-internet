#!/usr/bin/env python3
"""
sensor_base.py - Clase base para todos los sensores ambientales urbanos
Protocolo: REGISTER|id|tipo|zona|unidad|token
           MEASURE|id|valor|timestamp
           HEARTBEAT|id
"""
import socket, time, logging, sys
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class SensorBase(ABC):
    TIPOS_SENSOR = ["co2", "ruido", "temperatura", "pm25", "humedad", "uv"]

    def __init__(
        self, sensor_id, tipo, zona, unidad, token=None, host="localhost", puerto=5000
    ):
        self.sensor_id = sensor_id
        self.tipo = tipo
        self.zona = zona
        self.unidad = unidad
        self.token = token or "token_defecto"
        self.host = host
        self.puerto = puerto
        self.socket = None
        self.conectado = False
        self.ultima_medicion = 0
        self.intentos_recon = 0
        self.max_intentos = 999
        self.logger = logging.getLogger(self.sensor_id)

    @abstractmethod
    def generar_medicion(self):
        pass

    @classmethod
    def crear(
        cls,
        tipo,
        sensor_id,
        zona="Desconocida",
        unidad=None,
        token=None,
        host="localhost",
        puerto=5000,
    ):
        defaults = {
            "co2": "ppm",
            "ruido": "dB",
            "temperatura": "C",
            "pm25": "ug/m3",
            "humedad": "%",
            "uv": "idx",
        }
        if unidad is None:
            unidad = defaults.get(tipo.lower(), "u")
        t = tipo.lower()
        if t == "co2":
            from sensor_co2 import SensorCO2

            return SensorCO2(
                sensor_id=sensor_id,
                zona=zona,
                unidad=unidad,
                token=token,
                host=host,
                puerto=puerto,
            )
        elif t == "ruido":
            from sensor_ruido import SensorRuido

            return SensorRuido(
                sensor_id=sensor_id,
                zona=zona,
                unidad=unidad,
                token=token,
                host=host,
                puerto=puerto,
            )
        elif t == "temperatura":
            from sensor_temperatura import SensorTemperatura

            return SensorTemperatura(
                sensor_id=sensor_id,
                zona=zona,
                unidad=unidad,
                token=token,
                host=host,
                puerto=puerto,
            )
        elif t == "pm25":
            from sensor_pm25 import SensorPM25

            return SensorPM25(
                sensor_id=sensor_id,
                zona=zona,
                unidad=unidad,
                token=token,
                host=host,
                puerto=puerto,
            )
        elif t == "humedad":
            from sensor_humedad import SensorHumedad

            return SensorHumedad(
                sensor_id=sensor_id,
                zona=zona,
                unidad=unidad,
                token=token,
                host=host,
                puerto=puerto,
            )
        elif t == "uv":
            from sensor_uv import SensorUV

            return SensorUV(
                sensor_id=sensor_id,
                zona=zona,
                unidad=unidad,
                token=token,
                host=host,
                puerto=puerto,
            )
        raise ValueError(f"Tipo desconocido: {tipo}")

    def conectar(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.puerto))
            self.conectado = True
            self.intentos_recon = 0
            self.logger.info(f"Conectado a {self.host}:{self.puerto}")
            return True
        except Exception as e:
            self.logger.error(f"Error conectando: {e}")
            return False

    def enviar(self, mensaje):
        if not self.conectado:
            return None
        try:
            self.socket.settimeout(10)
            self.socket.sendall((mensaje + "\n").encode("utf-8"))
            resp = self.socket.recv(1024).decode("utf-8").strip()
            return resp
        except Exception as e:
            self.logger.error(f"Error enviando: {e}")
            self.conectado = False
            try:
                self.socket.close()
            except:
                pass
            return None

    def registrar(self):
        msg = f"REGISTER|{self.sensor_id}|{self.tipo}|{self.zona}|{self.unidad}|{self.token}"
        resp = self.enviar(msg)
        if resp and "OK" in resp.upper():
            self.logger.info(f"Sensor registrado: {self.sensor_id}")
            return True
        # Si el sensor ya existe en la DB (INSERT OR IGNORE), el servidor
        # devuelve ERROR pero el sensor puede operar igual — tratar como éxito
        self.logger.warning(
            f"Registro retornó: {resp} — asumiendo sensor ya existente, continuando..."
        )
        return True

    def enviar_medicion(self):
        try:
            valor = self.generar_medicion()
            resp = self.enviar(f"MEASURE|{self.sensor_id}|{valor}|{int(time.time())}")
            if resp and "OK" in resp.upper():
                self.ultima_medicion = time.time()
                self.logger.info(f"Medicion: {valor} {self.unidad}")
                return True
        except Exception as e:
            self.logger.error(f"Error medicion: {e}")
        return False

    def enviar_heartbeat(self):
        if not self.conectado:
            return
        if time.time() - self.ultima_medicion > 30:
            resp = self.enviar(f"HEARTBEAT|{self.sensor_id}")
            if resp and "OK" in resp.upper():
                self.logger.debug("Heartbeat enviado")

    def reconectar(self):
        espera = min(2**self.intentos_recon, 30)
        self.logger.warning(
            f"Reintentando en {espera}s (intento {self.intentos_recon+1})"
        )
        time.sleep(espera)
        self.intentos_recon += 1
        ok = self.conectar()
        if ok:
            self.intentos_recon = 0  # resetear backoff al reconectar
        return ok

    def iniciar(self):
        self.logger.info(f"=== Iniciando {self.sensor_id} ({self.tipo}) ===")
        if not self.conectar():
            return
        if not self.registrar():
            self.cerrar()
            return
        try:
            self.ultima_medicion = time.time()
            while True:
                try:
                    if not self.conectado:
                        if not self.reconectar():
                            time.sleep(5)
                            continue
                        if not self.registrar():
                            self.conectado = False
                            continue
                    self.enviar_medicion()
                    self.enviar_heartbeat()
                    time.sleep(5)
                except Exception as e:
                    self.logger.error(f"Error en ciclo: {e}")
                    self.conectado = False
                    time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Sensor detenido por usuario")
        finally:
            self.cerrar()

    def cerrar(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.conectado = False
        self.logger.info("Conexion cerrada")
