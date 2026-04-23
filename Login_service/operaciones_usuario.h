#pragma once
#include "db_manager.h"
#include <string>
#include <vector>

struct RespuestaCreacion {
    std::string id;
    std::string usuario;
    std::string nombre;
    std::string clave;
    std::string mensaje;
};

struct RespuestaListaUsuarios {
    std::vector<InfoUsuario> usuarios;
    std::string mensaje;
};

struct RespuestaEliminacion {
    std::string id;
    std::string mensaje;
};

class OperacionesUsuario {
private:
    GestorDB& db;

public:
    OperacionesUsuario(GestorDB& gestor);
    std::string generar_id_aleatorio();
    RespuestaListaUsuarios obtener_usuarios();
    RespuestaCreacion crear_usuario(std::string nombre, std::string usuario,
                                    std::string rol, std::string clave);
    RespuestaEliminacion eliminar_usuario(std::string id);
};
