#pragma once
#include "verificador_identidad.h"
#include "verificador_token.h"
#include "operaciones_usuario.h"
#include <string>

struct RespuestaAccionAdmin {
    std::string id;
    std::string mensaje;
    bool exito;
};

class ManejadorSesion {
private:
    VerificadorIdentidad& ver_identidad;
    VerificadorToken&     ver_token;
    OperacionesUsuario&   ops_usuario;

    void crear_log();

public:
    ManejadorSesion(VerificadorIdentidad& vi, VerificadorToken& vt, OperacionesUsuario& ou);

    void registrar_log(std::string mensaje, std::string id);
    RespuestaValidacionUsuario iniciar_sesion(std::string usuario, std::string clave);
    RespuestaValidacion validar_tokens(std::string id, std::string token, std::string r_token);
    void cerrar_sesion(std::string id, std::string token, std::string r_token);

    struct VerificacionAdmin { bool es_admin; std::string mensaje; };
    VerificacionAdmin verificar_admin(std::string id);

    RespuestaListaUsuarios listar_usuarios(std::string id, std::string token, std::string r_token);
    RespuestaAccionAdmin crear_usuario(std::string id_admin, std::string nombre, std::string usuario,
                                       std::string rol, std::string clave,
                                       std::string token, std::string r_token);
    RespuestaAccionAdmin eliminar_usuario(std::string id_eliminar, std::string id_admin,
                                          std::string token, std::string r_token);
};
