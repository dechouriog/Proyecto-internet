#include "manejador_sesion.h"
#include <fstream>
#include <chrono>
#include <ctime>

ManejadorSesion::ManejadorSesion(VerificadorIdentidad& vi, VerificadorToken& vt, OperacionesUsuario& ou)
    : ver_identidad(vi), ver_token(vt), ops_usuario(ou) {}

void ManejadorSesion::crear_log() {
    std::ofstream f("log_sesiones");
    f << "--- ARCHIVO DE LOG CREADO ---" << std::endl;
    f.close();
}

void ManejadorSesion::registrar_log(std::string mensaje, std::string id) {
    std::ifstream check("log_sesiones");
    if (!check) crear_log();
    check.close();

    std::ofstream f("log_sesiones", std::ios::app);
    if (f.is_open()) {
        auto now = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
        std::string dt = std::ctime(&now);
        dt.pop_back();
        f << "[" << dt << "] | ID: " << id << " | MSG: " << mensaje << std::endl;
        f.close();
    }
}

RespuestaValidacionUsuario ManejadorSesion::iniciar_sesion(std::string usuario, std::string clave) {
    RespuestaValidacionUsuario resp = ver_identidad.validar_usuario(usuario, clave);
    if (resp.id == "0") { registrar_log(resp.mensaje, resp.id); return resp; }

    RespuestaEstado estado = ver_identidad.verificar_estado(resp.id);
    if (estado.estado != "active") {
        resp.id = "0"; resp.token = "0"; resp.r_token = "0";
        resp.mensaje = "information does not match";
    }

    registrar_log(resp.mensaje, resp.id);
    return resp;
}

ManejadorSesion::VerificacionAdmin ManejadorSesion::verificar_admin(std::string id) {
    RespuestaRol resp = ver_identidad.obtener_rol(id);
    bool es_admin = (resp.rol == "Admin" || resp.rol == "admin");
    registrar_log(resp.mensaje, id);
    return { es_admin, resp.mensaje };
}

RespuestaValidacion ManejadorSesion::validar_tokens(std::string id, std::string token, std::string r_token) {
    RespuestaValidacion resp = ver_token.validar_token(id, token, r_token);
    registrar_log(resp.mensaje, id);
    return resp;
}

void ManejadorSesion::cerrar_sesion(std::string id, std::string token, std::string r_token) {
    RespuestaValidacion val = validar_tokens(id, token, r_token);
    if (val.token != "0") {
        std::string msg = ver_identidad.cerrar_sesion(id);
        registrar_log(msg, id);
    }
}

RespuestaListaUsuarios ManejadorSesion::listar_usuarios(std::string id, std::string token, std::string r_token) {
    RespuestaValidacion vtok = validar_tokens(id, token, r_token);
    RespuestaListaUsuarios resp;

    if (vtok.token == "0") { resp.mensaje = vtok.mensaje; return resp; }

    VerificacionAdmin vadmin = verificar_admin(id);
    if (vadmin.es_admin) resp = ops_usuario.obtener_usuarios();
    else resp.mensaje = vadmin.mensaje;

    registrar_log(resp.mensaje, id);
    return resp;
}

RespuestaAccionAdmin ManejadorSesion::crear_usuario(std::string id_admin, std::string nombre,
                                                     std::string usuario, std::string rol,
                                                     std::string clave, std::string token,
                                                     std::string r_token) {
    RespuestaValidacion vtok = validar_tokens(id_admin, token, r_token);
    RespuestaAccionAdmin resp = {"0", "", false};

    if (vtok.token == "0") { resp.mensaje = vtok.mensaje; }
    else {
        VerificacionAdmin vadmin = verificar_admin(id_admin);
        if (vadmin.es_admin) {
            RespuestaCreacion cr = ops_usuario.crear_usuario(nombre, usuario, rol, clave);
            resp.id = cr.id; resp.mensaje = cr.mensaje; resp.exito = true;
        } else {
            resp.mensaje = "operation not valid";
        }
    }

    registrar_log(resp.mensaje, id_admin);
    return resp;
}

RespuestaAccionAdmin ManejadorSesion::eliminar_usuario(std::string id_eliminar, std::string id_admin,
                                                        std::string token, std::string r_token) {
    RespuestaValidacion vtok = validar_tokens(id_admin, token, r_token);
    RespuestaAccionAdmin resp = {"0", "", false};

    if (vtok.token == "0") { resp.mensaje = vtok.mensaje; }
    else {
        VerificacionAdmin vadmin = verificar_admin(id_admin);
        if (vadmin.es_admin) {
            RespuestaEliminacion del = ops_usuario.eliminar_usuario(id_eliminar);
            resp.id = del.id; resp.mensaje = del.mensaje; resp.exito = true;
        } else {
            resp.mensaje = "operation not valid";
        }
    }

    registrar_log(resp.mensaje, id_admin);
    return resp;
}
