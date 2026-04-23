#include "db_manager.h"
#include <iostream>

GestorDB::GestorDB(const std::string& nombre_db) : db(nullptr) {
    if (sqlite3_open(nombre_db.c_str(), &db) != SQLITE_OK) {
        std::cerr << "Error abriendo users.db: " << sqlite3_errmsg(db) << std::endl;
        db = nullptr;
    }
}

GestorDB::~GestorDB() {
    if (db) { sqlite3_close(db); db = nullptr; }
}

void GestorDB::crear_db() {
    if (!db) return;

    const char* sql = R"(
        CREATE TABLE IF NOT EXISTS usuarios (
            ID TEXT PRIMARY KEY,
            USUARIO TEXT NOT NULL UNIQUE,
            CLAVE TEXT NOT NULL,
            NOMBRE TEXT NOT NULL,
            ROL TEXT NOT NULL,
            TOKEN TEXT NOT NULL,
            REFRESH_TOKEN TEXT NOT NULL,
            ESTADO TEXT NOT NULL
        );
    )";

    char* errMsg = nullptr;
    int rc = sqlite3_exec(db, sql, nullptr, nullptr, &errMsg);
    if (rc != SQLITE_OK) {
        std::cerr << "Error creando tabla usuarios: " << errMsg << std::endl;
        sqlite3_free(errMsg);
        return;
    }

    const char* seed_sql = R"(
        INSERT OR IGNORE INTO usuarios (ID, USUARIO, CLAVE, NOMBRE, ROL, TOKEN, REFRESH_TOKEN, ESTADO)
        VALUES ('0000000001', 'admin', 'admin123', 'Administrador', 'admin', 'token_admin_001', 'refresh_admin_001', 'active');

        INSERT OR IGNORE INTO usuarios (ID, USUARIO, CLAVE, NOMBRE, ROL, TOKEN, REFRESH_TOKEN, ESTADO)
        VALUES ('0000000002', 'operador1', 'op1234', 'Operador Uno', 'operator', 'token_op_001', 'refresh_op_001', 'active');
    )";

    rc = sqlite3_exec(db, seed_sql, nullptr, nullptr, &errMsg);
    if (rc != SQLITE_OK) {
        std::cerr << "Error insertando usuarios por defecto: " << errMsg << std::endl;
        sqlite3_free(errMsg);
    }
}

bool GestorDB::crear_usuario(std::string id, std::string usuario, std::string clave,
                              std::string nombre, std::string rol, std::string token,
                              std::string r_token, std::string estado) {
    if (!db) return false;

    const char* sql = R"(
        INSERT INTO usuarios (ID, USUARIO, CLAVE, NOMBRE, ROL, TOKEN, REFRESH_TOKEN, ESTADO)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    )";

    sqlite3_stmt* stmt = nullptr;
    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr);
    if (rc != SQLITE_OK) return false;

    sqlite3_bind_text(stmt, 1, id.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, usuario.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 3, clave.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 4, nombre.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 5, rol.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 6, token.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 7, r_token.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 8, estado.c_str(), -1, SQLITE_TRANSIENT);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return rc == SQLITE_DONE;
}

bool GestorDB::verificar_por_id(std::string id) {
    if (!db) return false;
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "SELECT COUNT(*) FROM usuarios WHERE ID = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, id.c_str(), -1, SQLITE_TRANSIENT);
    bool existe = false;
    if (sqlite3_step(stmt) == SQLITE_ROW) existe = sqlite3_column_int(stmt, 0) > 0;
    sqlite3_finalize(stmt);
    return existe;
}

std::string GestorDB::verificar_por_usuario(std::string usuario) {
    if (!db) return "false";
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "SELECT ID FROM usuarios WHERE USUARIO = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, usuario.c_str(), -1, SQLITE_TRANSIENT);
    std::string id = "false";
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const unsigned char* t = sqlite3_column_text(stmt, 0);
        if (t) id = reinterpret_cast<const char*>(t);
    }
    sqlite3_finalize(stmt);
    return id;
}

std::string GestorDB::verificar_por_usuario_clave(std::string usuario, std::string clave) {
    if (!db) return "false";
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "SELECT ID FROM usuarios WHERE USUARIO = ? AND CLAVE = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, usuario.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, clave.c_str(), -1, SQLITE_TRANSIENT);
    std::string id = "false";
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const unsigned char* t = sqlite3_column_text(stmt, 0);
        if (t) id = reinterpret_cast<const char*>(t);
    }
    sqlite3_finalize(stmt);
    return id;
}

std::string GestorDB::obtener_rol(std::string id) {
    if (!db) return "false";
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "SELECT ROL FROM usuarios WHERE ID = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, id.c_str(), -1, SQLITE_TRANSIENT);
    std::string rol = "false";
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const unsigned char* t = sqlite3_column_text(stmt, 0);
        if (t) rol = reinterpret_cast<const char*>(t);
    }
    sqlite3_finalize(stmt);
    return rol;
}

bool GestorDB::obtener_estado(std::string id) {
    if (!db) return false;
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "SELECT ESTADO FROM usuarios WHERE ID = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, id.c_str(), -1, SQLITE_TRANSIENT);
    bool activo = false;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const unsigned char* t = sqlite3_column_text(stmt, 0);
        if (t) activo = (std::string(reinterpret_cast<const char*>(t)) == "active");
    }
    sqlite3_finalize(stmt);
    return activo;
}

bool GestorDB::verificar_token(std::string id, std::string token) {
    if (!db) return false;
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "SELECT COUNT(*) FROM usuarios WHERE ID = ? AND TOKEN = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, id.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, token.c_str(), -1, SQLITE_TRANSIENT);
    bool valido = false;
    if (sqlite3_step(stmt) == SQLITE_ROW) valido = sqlite3_column_int(stmt, 0) > 0;
    sqlite3_finalize(stmt);
    return valido;
}

bool GestorDB::verificar_refresh(std::string id, std::string r_token) {
    if (!db) return false;
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "SELECT COUNT(*) FROM usuarios WHERE ID = ? AND REFRESH_TOKEN = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, id.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, r_token.c_str(), -1, SQLITE_TRANSIENT);
    bool valido = false;
    if (sqlite3_step(stmt) == SQLITE_ROW) valido = sqlite3_column_int(stmt, 0) > 0;
    sqlite3_finalize(stmt);
    return valido;
}

std::string GestorDB::obtener_token(std::string id) {
    if (!db) return "";
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "SELECT TOKEN FROM usuarios WHERE ID = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, id.c_str(), -1, SQLITE_TRANSIENT);
    std::string token;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const unsigned char* t = sqlite3_column_text(stmt, 0);
        if (t) token = reinterpret_cast<const char*>(t);
    }
    sqlite3_finalize(stmt);
    return token;
}

std::string GestorDB::obtener_refresh(std::string id) {
    if (!db) return "";
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "SELECT REFRESH_TOKEN FROM usuarios WHERE ID = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, id.c_str(), -1, SQLITE_TRANSIENT);
    std::string r_token;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const unsigned char* t = sqlite3_column_text(stmt, 0);
        if (t) r_token = reinterpret_cast<const char*>(t);
    }
    sqlite3_finalize(stmt);
    return r_token;
}

bool GestorDB::actualizar_token(std::string id, std::string token) {
    if (!db) return false;
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "UPDATE usuarios SET TOKEN = ? WHERE ID = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, token.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, id.c_str(), -1, SQLITE_TRANSIENT);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return rc == SQLITE_DONE;
}

bool GestorDB::actualizar_refresh(std::string id, std::string r_token) {
    if (!db) return false;
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "UPDATE usuarios SET REFRESH_TOKEN = ? WHERE ID = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, r_token.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, id.c_str(), -1, SQLITE_TRANSIENT);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return rc == SQLITE_DONE;
}

bool GestorDB::actualizar_usuario(std::string id, std::string usuario, std::string clave,
                                   std::string nombre, std::string rol,
                                   std::string token, std::string r_token) {
    if (!db) return false;
    sqlite3_stmt* stmt = nullptr;
    const char* sql = "UPDATE usuarios SET USUARIO=?,CLAVE=?,NOMBRE=?,ROL=?,TOKEN=?,REFRESH_TOKEN=? WHERE ID=?;";
    sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, usuario.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, clave.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 3, nombre.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 4, rol.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 5, token.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 6, r_token.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 7, id.c_str(), -1, SQLITE_TRANSIENT);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return rc == SQLITE_DONE;
}

bool GestorDB::eliminar_usuario(std::string id) {
    if (!db) return false;
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "DELETE FROM usuarios WHERE ID = ?;", -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, id.c_str(), -1, SQLITE_TRANSIENT);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return rc == SQLITE_DONE;
}

std::vector<InfoUsuario> GestorDB::obtener_todos() {
    std::vector<InfoUsuario> lista;
    if (!db) return lista;
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db, "SELECT ID, USUARIO, NOMBRE, ROL FROM usuarios;", -1, &stmt, nullptr);
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        InfoUsuario u;
        auto c = [](const unsigned char* t) -> std::string {
            return t ? reinterpret_cast<const char*>(t) : "";
        };
        u.id      = c(sqlite3_column_text(stmt, 0));
        u.usuario = c(sqlite3_column_text(stmt, 1));
        u.nombre  = c(sqlite3_column_text(stmt, 2));
        u.rol     = c(sqlite3_column_text(stmt, 3));
        lista.push_back(u);
    }
    sqlite3_finalize(stmt);
    return lista;
}
