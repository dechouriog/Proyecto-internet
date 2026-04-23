#!/usr/bin/env python3
"""Sensor Ruido - Monitoreo Ambiental Urbano | Rango: 30-120 dB"""
import random, sys
from sensor_base import SensorBase


class SensorRuido(SensorBase):
    def __init__(
        self,
        sensor_id="RUI-S01",
        zona="zona_comercial",
        unidad="dB",
        token="token_rui_001",
        host="localhost",
        puerto=5000,
    ):
        super().__init__(sensor_id, "ruido", zona, unidad, token, host, puerto)
        self.valor_actual = 52.0

    def generar_medicion(self):
        if random.random() < 0.75:
            self.valor_actual += random.gauss(0, 2.5)
        elif random.random() < 0.93:
            pico = random.uniform(10, 20)
            self.valor_actual += pico
            self.logger.warning(f"Pico de ruido: +{pico:.1f} dB")
        else:
            self.valor_actual = random.uniform(80, 115)
            self.logger.critical(f"EVENTO ACUSTICO SEVERO: {self.valor_actual:.1f} dB")
        if self.valor_actual > 70:
            self.valor_actual -= random.uniform(3, 10)
        self.valor_actual = max(30, min(120, self.valor_actual))
        return round(self.valor_actual, 1)


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    puerto = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    SensorRuido(host=host, puerto=puerto).iniciar()
