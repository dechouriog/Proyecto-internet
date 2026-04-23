# ============================================================
# Dockerfile — Servidor principal C++ (puerto 5000)
# Sistema de Monitoreo Ambiental Urbano
# ============================================================
FROM ubuntu:22.04

# Evitar prompts interactivos durante apt
ENV DEBIAN_FRONTEND=noninteractive

# Dependencias de compilación
RUN apt-get update && apt-get install -y \
    g++ \
    make \
    libsqlite3-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar fuentes del servidor
COPY server/server.cpp   ./server/
COPY server/Makefile     ./server/
COPY Login_service/      ./Login_service/
COPY docs/               ./docs/

# Compilar servidor principal
RUN cd server && make && echo "servidor compilado OK"

# Compilar login_service
RUN cd Login_service && make && echo "login_service compilado OK"

# Crear directorios necesarios
RUN mkdir -p logs

# limpiar DB antes de crearla
RUN rm -f database.db && \
    sqlite3 database.db < docs/database/schema.sql && \
    sqlite3 database.db < docs/database/seed.sql && \
    echo "Base de datos inicializada"

# Exponer puertos
EXPOSE 5000
EXPOSE 6000

# Script de arranque que lanza ambos servicios
COPY deployment/scripts/docker_entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]