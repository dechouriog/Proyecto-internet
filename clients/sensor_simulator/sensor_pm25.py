#!/usr/bin/env python3
"""Sensor PM2.5 - Monitoreo Ambiental Urbano | Rango: 0-300 ug/m3"""
import random, sys
from sensor_base import SensorBase


class SensorPM25(SensorBase):
    def __init__(
        self,
        sensor_id="PM2-S01",
        zona="via_principal",
        unidad="ug/m3",
        token="token_pm2_001",
        host="localhost",
        puerto=5000,
    ):
        super().__init__(sensor_id, "pm25", zona, unidad, token, host, puerto)
        self.valor_actual = 18.0

    def generar_medicion(self):
        if random.random() < 0.82:
            self.valor_actual += random.gauss(0, 1.2)
        elif random.random() < 0.96:
            inc = random.uniform(5, 20)
            self.valor_actual += inc
            self.logger.warning(f"Aumento PM2.5: +{inc:.1f} ug/m3")
        else:
            self.valor_actual = random.uniform(60, 150)
            self.logger.critical(
                f"EPISODIO CONTAMINACION PM2.5: {self.valor_actual:.1f}"
            )
        if self.valor_actual > 40:
            self.valor_actual -= random.uniform(0.5, 2.5)
        self.valor_actual = max(0, min(300, self.valor_actual))
        return round(self.valor_actual, 1)


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    puerto = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    SensorPM25(host=host, puerto=puerto).iniciar()
