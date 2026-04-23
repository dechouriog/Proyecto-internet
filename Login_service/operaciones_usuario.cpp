#include "operaciones_usuario.h"
#include <random>
#include <iomanip>
#include <sstream>

OperacionesUsuario::OperacionesUsuario(GestorDB& gestor) : db(gestor) {}

std::string OperacionesUsuario::generar_id_aleatorio() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<long long> dis(0, 9999999999LL);
    std::stringstream ss;
    ss << std::setw(10) << std::setfill('0') << dis(gen);
    return ss.str();
}

RespuestaListaUsuarios OperacionesUsuario::obtener_usuarios() {
    RespuestaListaUsuarios resp;
    resp.usuarios = db.obtener_todos();
    resp.mensaje  = "all users were returned";
    return resp;
}

RespuestaCreacion OperacionesUsuario::crear_usuario(std::string nombre, std::string usuario,
                                                     std::string rol, std::string clave) {
    RespuestaCreacion resp;
    std::string id = generar_id_aleatorio();

    while (db.verificar_por_id(id)) {
        unsigned long long num = std::stoull(id) + 1;
        std::stringstream ss;
        ss << std::setw(10) << std::setfill('0') << num;
        id = ss.str();
    }

    std::string token   = generar_id_aleatorio();
    std::string r_token = generar_id_aleatorio();

    db.crear_usuario(id, usuario, clave, nombre, rol, token, r_token, "active");

    resp.id      = id;
    resp.usuario = usuario;
    resp.nombre  = nombre;
    resp.clave   = clave;
    resp.mensaje = "user has been created";
    return resp;
}

RespuestaEliminacion OperacionesUsuario::eliminar_usuario(std::string id) {
    RespuestaEliminacion resp;
    bool ok = db.eliminar_usuario(id);
    resp.id      = ok ? id : "0";
    resp.mensaje = ok ? "user has been removed" : "operation completed";
    return resp;
}
