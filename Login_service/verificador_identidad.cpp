#include "verificador_identidad.h"
#include <random>

VerificadorIdentidad::VerificadorIdentidad(GestorDB& gestor) : db(gestor) {}

std::string VerificadorIdentidad::generar_aleatorio() {
    const std::string chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dist(0, (int)chars.size() - 1);
    std::string resultado;
    for (int i = 0; i < 10; ++i) resultado += chars[dist(gen)];
    return resultado;
}

RespuestaValidacionUsuario VerificadorIdentidad::validar_usuario(std::string usuario, std::string clave) {
    RespuestaValidacionUsuario resp;
    std::string id_encontrado = db.verificar_por_usuario_clave(usuario, clave);

    if (id_encontrado == "false") {
        resp.id = "0"; resp.token = "0"; resp.r_token = "0";
        resp.mensaje = "information does not match";
        return resp;
    }

    resp.id = id_encontrado;
    std::string nuevo_token   = generar_aleatorio();
    std::string nuevo_refresh = generar_aleatorio();

    db.actualizar_token(id_encontrado, nuevo_token);
    db.actualizar_refresh(id_encontrado, nuevo_refresh);

    resp.token   = db.obtener_token(id_encontrado);
    resp.r_token = db.obtener_refresh(id_encontrado);
    resp.mensaje = "user located; ID, token and refresh token has been provided";
    return resp;
}

std::string VerificadorIdentidad::cerrar_sesion(std::string id) {
    db.actualizar_refresh(id, generar_aleatorio());
    return "the refresh token was updated";
}

RespuestaRol VerificadorIdentidad::obtener_rol(std::string id) {
    RespuestaRol resp;
    std::string resultado = db.obtener_rol(id);
    if (resultado == "false") {
        resp.rol = "0"; resp.mensaje = "user not found";
    } else {
        resp.rol = resultado; resp.mensaje = "user found, role returned";
    }
    return resp;
}

RespuestaEstado VerificadorIdentidad::verificar_estado(std::string id) {
    RespuestaEstado resp;
    resp.id     = id;
    resp.estado = db.obtener_estado(id) ? "active" : "inactive";
    resp.mensaje = "estado del usuario obtenido";
    return resp;
}
