#!/usr/bin/env python3
"""
run_sensors.py - Inicia todos los sensores ambientales en paralelo

USO:
    python run_sensors.py
    python run_sensors.py --host <IP_EC2> --port 5000
"""
import subprocess, sys, time, argparse

def run_all(host='localhost', port=5000):
    sensores = [
        ('sensor_co2',         'CO2-S01'),
        ('sensor_ruido',       'RUI-S01'),
        ('sensor_temperatura', 'TMP-S01'),
        ('sensor_pm25',        'PM2-S01'),
        ('sensor_humedad',     'HUM-S01'),
        ('sensor_uv',          'UVR-S01'),
    ]

    procesos = []
    print("=" * 55)
    print("  SISTEMA DE MONITOREO AMBIENTAL URBANO")
    print("  Iniciando sensores...")
    print("=" * 55)
    print(f"  Servidor: {host}:{port}\n")

    for modulo, sid in sensores:
        print(f"  > {sid} iniciando...")
        try:
            p = subprocess.Popen(
                [sys.executable, f'{modulo}.py', host, str(port)],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                bufsize=1, universal_newlines=True
            )
            procesos.append((sid, p))
        except Exception as e:
            print(f"  ERROR: {modulo} - {e}")

    print(f"\n  {len(procesos)} sensores activos.")
    print("  Ctrl+C para detener todos.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nDeteniendo sensores...")
        for sid, p in procesos:
            try: p.terminate(); print(f"  - {sid} detenido")
            except: pass
        for _, p in procesos:
            try: p.wait(timeout=2)
            except: p.kill()
    print("\nTodos los sensores cerrados.")

def main():
    parser = argparse.ArgumentParser(description='Simulador de sensores ambientales urbanos')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("  MONITOREO AMBIENTAL URBANO - SIMULADOR")
    print("=" * 55)
    print(f"  Destino: {args.host}:{args.port}")
    print("=" * 55 + "\n")
    run_all(args.host, args.port)

if __name__ == '__main__':
    main()
