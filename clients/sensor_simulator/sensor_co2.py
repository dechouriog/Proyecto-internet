#!/usr/bin/env python3
"""Sensor CO2 - Monitoreo Ambiental Urbano | Rango: 300-2000 ppm"""
import random, sys
from sensor_base import SensorBase


class SensorCO2(SensorBase):
    def __init__(
        self,
        sensor_id="CO2-S01",
        zona="zona_centro",
        unidad="ppm",
        token="token_co2_001",
        host="localhost",
        puerto=5000,
    ):
        super().__init__(sensor_id, "co2", zona, unidad, token, host, puerto)
        self.valor_actual = 420.0

    def generar_medicion(self):
        if random.random() < 0.88:
            self.valor_actual += random.gauss(0, 4.0)
        elif random.random() < 0.97:
            pico = random.uniform(50, 150)
            self.valor_actual += pico
            self.logger.warning(f"Pico CO2: +{pico:.0f} ppm")
        else:
            self.valor_actual += random.uniform(200, 400)
            self.logger.critical("ALERTA CO2 CRITICO")
        if self.valor_actual > 600:
            self.valor_actual -= random.uniform(2, 8)
        self.valor_actual = max(300, min(2000, self.valor_actual))
        return round(self.valor_actual, 1)


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    puerto = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    SensorCO2(host=host, puerto=puerto).iniciar()
