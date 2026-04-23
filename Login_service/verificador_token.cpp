#include "verificador_token.h"
#include <random>

VerificadorToken::VerificadorToken(GestorDB& gestor) : db(gestor) {}

std::string VerificadorToken::generar_aleatorio() {
    const std::string chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dist(0, (int)chars.size() - 1);
    std::string resultado;
    for (int i = 0; i < 10; ++i) resultado += chars[dist(gen)];
    return resultado;
}

RespuestaValidacion VerificadorToken::validar_token(std::string id, std::string token, std::string r_token) {
    RespuestaValidacion resp;

    if (!db.verificar_por_id(id)) {
        resp.token = "0"; resp.r_token = "0";
        resp.mensaje = "user does not exist";
        return resp;
    }

    bool token_ok   = db.verificar_token(id, token);
    bool refresh_ok = db.verificar_refresh(id, r_token);

    if (token_ok && refresh_ok) {
        std::string nuevo_token   = generar_aleatorio();
        std::string nuevo_refresh = generar_aleatorio();
        db.actualizar_token(id, nuevo_token);
        db.actualizar_refresh(id, nuevo_refresh);
        resp.token   = nuevo_token;
        resp.r_token = nuevo_refresh;
        resp.mensaje = "token validated and information was updated";
    } else {
        resp.token = "0"; resp.r_token = "0";
        resp.mensaje = "token could not be validated";
    }

    return resp;
}
