#!/usr/bin/env python3
"""Sensor Indice UV Solar - Monitoreo Ambiental Urbano | Rango: 0-15"""
import random, time, sys
from sensor_base import SensorBase


class SensorUV(SensorBase):
    def __init__(
        self,
        sensor_id="UVR-S01",
        zona="plaza_publica",
        unidad="idx",
        token="token_uvr_001",
        host="localhost",
        puerto=5000,
    ):
        super().__init__(sensor_id, "uv", zona, unidad, token, host, puerto)
        self.valor_actual = 3.0

    def generar_medicion(self):
        hora = time.localtime().tm_hour
        if 6 <= hora <= 8:
            base = random.uniform(1, 4)
        elif 9 <= hora <= 11:
            base = random.uniform(4, 8)
        elif 12 <= hora <= 14:
            base = random.uniform(7, 13)
        elif 15 <= hora <= 17:
            base = random.uniform(3, 7)
        elif 18 <= hora <= 19:
            base = random.uniform(1, 3)
        else:
            base = random.uniform(0, 1)

        self.valor_actual = max(0, min(15, base + random.gauss(0, 0.5)))

        if self.valor_actual > 10:
            self.logger.critical(f"INDICE UV EXTREMO: {self.valor_actual:.1f}")
        elif self.valor_actual > 7:
            self.logger.warning(f"UV muy alto: {self.valor_actual:.1f}")

        return round(self.valor_actual, 1)


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    puerto = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    SensorUV(host=host, puerto=puerto).iniciar()
