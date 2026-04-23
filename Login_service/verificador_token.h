#pragma once
#include "db_manager.h"
#include <string>

struct RespuestaValidacion {
    std::string token;
    std::string r_token;
    std::string mensaje;
};

class VerificadorToken {
private:
    GestorDB& db;

public:
    VerificadorToken(GestorDB& gestor);
    std::string generar_aleatorio();
    RespuestaValidacion validar_token(std::string id, std::string token, std::string r_token);
};
