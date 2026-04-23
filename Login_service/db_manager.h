#pragma once

#include <sqlite3.h>
#include <string>
#include <vector>

struct InfoUsuario {
    std::string id;
    std::string usuario;
    std::string nombre;
    std::string rol;
};

class GestorDB {
private:
    sqlite3* db;

public:
    GestorDB(const std::string& nombre_db);
    ~GestorDB();

    void crear_db();

    bool crear_usuario(std::string id, std::string usuario, std::string clave,
                       std::string nombre, std::string rol, std::string token,
                       std::string r_token, std::string estado);

    bool verificar_por_id(std::string id);
    std::string verificar_por_usuario(std::string usuario);
    std::string verificar_por_usuario_clave(std::string usuario, std::string clave);
    std::string obtener_rol(std::string id);
    bool obtener_estado(std::string id);

    bool verificar_token(std::string id, std::string token);
    bool verificar_refresh(std::string id, std::string r_token);
    std::string obtener_token(std::string id);
    std::string obtener_refresh(std::string id);

    bool actualizar_token(std::string id, std::string token);
    bool actualizar_refresh(std::string id, std::string r_token);
    bool actualizar_usuario(std::string id, std::string usuario, std::string clave,
                            std::string nombre, std::string rol,
                            std::string token, std::string r_token);

    bool eliminar_usuario(std::string id);
    std::vector<InfoUsuario> obtener_todos();
};
