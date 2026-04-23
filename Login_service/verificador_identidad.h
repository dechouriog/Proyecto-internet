#pragma once
#include "db_manager.h"
#include <string>

struct RespuestaValidacionUsuario {
    std::string id;
    std::string token;
    std::string r_token;
    std::string mensaje;
};

struct RespuestaRol {
    std::string rol;
    std::string mensaje;
};

struct RespuestaEstado {
    std::string id;
    std::string estado;
    std::string mensaje;
};

class VerificadorIdentidad {
private:
    GestorDB& db;

public:
    VerificadorIdentidad(GestorDB& gestor);
    std::string generar_aleatorio();
    RespuestaValidacionUsuario validar_usuario(std::string usuario, std::string clave);
    std::string cerrar_sesion(std::string id);
    RespuestaRol obtener_rol(std::string id);
    RespuestaEstado verificar_estado(std::string id);
};
