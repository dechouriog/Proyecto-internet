#include <iostream>
#include <fstream>
#include <cstring>
#include <string>
#include <sstream>
#include <thread>
#include <vector>
#include <mutex>
#include <algorithm>
#include <ctime>
#include <unistd.h>
#include <arpa/inet.h>
#include <sqlite3.h>

using namespace std;

string DB_PATH = "../database.db";
mutex log_mutex;
mutex monitoreo_mutex;
bool monitoreo_pausado = false;

// =========================
// UTILIDADES
// =========================
string recortar(const string& s) {
    size_t inicio = s.find_first_not_of(" \t\r\n");
    if (inicio == string::npos) return "";
    size_t fin = s.find_last_not_of(" \t\r\n");
    return s.substr(inicio, fin - inicio + 1);
}

vector<string> dividir(const string& s, char delimitador) {
    vector<string> partes;
    string item;
    stringstream ss(s);
    while (getline(ss, item, delimitador)) {
        partes.push_back(item);
    }
    return partes;
}

string marca_tiempo() {
    time_t ahora = time(nullptr);
    tm* local = localtime(&ahora);
    char buffer[32];
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", local);
    return string(buffer);
}

bool esta_pausado() {
    lock_guard<mutex> lock(monitoreo_mutex);
    return monitoreo_pausado;
}

void establecer_pausa(bool valor) {
    lock_guard<mutex> lock(monitoreo_mutex);
    monitoreo_pausado = valor;
}

// =========================
// LOGGING
// =========================
void registrar_log(
    const string& archivo_log,
    const string& ip_cliente,
    int puerto_cliente,
    const string& accion,
    const string& recibido,
    const string& respuesta
) {
    lock_guard<mutex> lock(log_mutex);
    string ts = marca_tiempo();

    cout << "[" << ts << "] "
         << "[" << ip_cliente << ":" << puerto_cliente << "] "
         << accion
         << " | RECIBIDO: " << recibido
         << " | RESPUESTA: " << respuesta
         << endl;

    ofstream log(archivo_log, ios::app);
    if (log.is_open()) {
        log << "[" << ts << "] "
            << "[" << ip_cliente << ":" << puerto_cliente << "] "
            << accion
            << " | RECIBIDO: " << recibido
            << " | RESPUESTA: " << respuesta
            << endl;
        log.close();
    }
}

// =========================
// BASE DE DATOS
// =========================
bool sensor_existe(const string& sensor_id) {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;
    bool existe = false;

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) { if (db) sqlite3_close(db); return false; }

    string sql = "SELECT COUNT(*) FROM sensores WHERE id = ?;";
    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);

    if (rc == SQLITE_OK) {
        sqlite3_bind_text(stmt, 1, sensor_id.c_str(), -1, SQLITE_TRANSIENT);
        if (sqlite3_step(stmt) == SQLITE_ROW)
            existe = sqlite3_column_int(stmt, 0) > 0;
    }

    if (stmt) sqlite3_finalize(stmt);
    sqlite3_close(db);
    return existe;
}

bool obtener_tipo_sensor(const string& sensor_id, string& tipo_sensor) {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) { if (db) sqlite3_close(db); return false; }

    string sql = "SELECT tipo FROM sensores WHERE id = ?;";
    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);

    if (rc != SQLITE_OK) { sqlite3_close(db); return false; }

    sqlite3_bind_text(stmt, 1, sensor_id.c_str(), -1, SQLITE_TRANSIENT);

    bool encontrado = false;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const unsigned char* texto = sqlite3_column_text(stmt, 0);
        if (texto) { tipo_sensor = reinterpret_cast<const char*>(texto); encontrado = true; }
    }

    sqlite3_finalize(stmt);
    sqlite3_close(db);
    return encontrado;
}

bool registrar_sensor(const string& sensor_id, const string& tipo, const string& zona,
                      const string& token, string& msg_error) {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) {
        msg_error = "No se pudo abrir la base de datos";
        if (db) sqlite3_close(db); return false;
    }

    string sql = R"(
        INSERT OR IGNORE INTO sensores (id, tipo, zona, token, estado)
        VALUES (?, ?, ?, ?, 'activo');
    )";

    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);
    if (rc != SQLITE_OK) {
        msg_error = "Error preparando INSERT de sensor";
        sqlite3_close(db); return false;
    }

    sqlite3_bind_text(stmt, 1, sensor_id.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, tipo.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 3, zona.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 4, token.c_str(), -1, SQLITE_TRANSIENT);

    rc = sqlite3_step(stmt);
    if (rc != SQLITE_DONE) {
        msg_error = "Error registrando sensor";
        sqlite3_finalize(stmt); sqlite3_close(db); return false;
    }

    sqlite3_finalize(stmt);
    sqlite3_close(db);
    return true;
}

bool validar_token_sensor(const string& sensor_id, const string& token) {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;
    bool valido = false;

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) { if (db) sqlite3_close(db); return false; }

    string sql = "SELECT COUNT(*) FROM sensores WHERE id = ? AND token = ? AND estado = 'activo';";
    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);
    if (rc == SQLITE_OK) {
        sqlite3_bind_text(stmt, 1, sensor_id.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_text(stmt, 2, token.c_str(), -1, SQLITE_TRANSIENT);
        if (sqlite3_step(stmt) == SQLITE_ROW)
            valido = (sqlite3_column_int(stmt, 0) > 0);
    }

    if (stmt) sqlite3_finalize(stmt);
    sqlite3_close(db);
    return valido;
}

bool insertar_dato(const string& sensor_id, double valor, string& msg_error) {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) {
        msg_error = "No se pudo abrir la base de datos";
        if (db) sqlite3_close(db); return false;
    }

    string sql = "INSERT INTO datos (sensor_id, valor) VALUES (?, ?);";
    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);
    if (rc != SQLITE_OK) {
        msg_error = "Error preparando INSERT de dato";
        sqlite3_close(db); return false;
    }

    sqlite3_bind_text(stmt, 1, sensor_id.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_double(stmt, 2, valor);

    rc = sqlite3_step(stmt);
    if (rc != SQLITE_DONE) {
        msg_error = "Error insertando dato";
        sqlite3_finalize(stmt); sqlite3_close(db); return false;
    }

    sqlite3_finalize(stmt);
    sqlite3_close(db);
    return true;
}

bool insertar_alerta(const string& sensor_id, const string& nivel, const string& mensaje, string& msg_error) {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) {
        msg_error = "No se pudo abrir la base de datos";
        if (db) sqlite3_close(db); return false;
    }

    string sql = "INSERT INTO alertas (sensor_id, nivel, mensaje) VALUES (?, ?, ?);";
    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);
    if (rc != SQLITE_OK) {
        msg_error = "Error preparando INSERT de alerta";
        sqlite3_close(db); return false;
    }

    sqlite3_bind_text(stmt, 1, sensor_id.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, nivel.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 3, mensaje.c_str(), -1, SQLITE_TRANSIENT);

    rc = sqlite3_step(stmt);
    if (rc != SQLITE_DONE) {
        msg_error = "Error insertando alerta";
        sqlite3_finalize(stmt); sqlite3_close(db); return false;
    }

    sqlite3_finalize(stmt);
    sqlite3_close(db);
    return true;
}

bool confirmar_alerta_db(int alerta_id, string& msg_error) {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) {
        msg_error = "No se pudo abrir la base de datos";
        if (db) sqlite3_close(db); return false;
    }

    string sql = "DELETE FROM alertas WHERE id = ?;";
    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);
    if (rc != SQLITE_OK) {
        msg_error = "Error preparando DELETE de alerta";
        sqlite3_close(db); return false;
    }

    sqlite3_bind_int(stmt, 1, alerta_id);
    rc = sqlite3_step(stmt);
    if (rc != SQLITE_DONE) {
        msg_error = "Error eliminando alerta";
        sqlite3_finalize(stmt); sqlite3_close(db); return false;
    }

    int cambios = sqlite3_changes(db);
    sqlite3_finalize(stmt);
    sqlite3_close(db);

    if (cambios == 0) { msg_error = "Alerta no encontrada"; return false; }
    return true;
}

bool limpiar_alertas_db(string& msg_error, int& total_eliminados) {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;
    total_eliminados = 0;

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) {
        msg_error = "No se pudo abrir la base de datos";
        if (db) sqlite3_close(db); return false;
    }

    string sql = "DELETE FROM alertas;";
    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);
    if (rc != SQLITE_OK) {
        msg_error = "Error preparando limpieza de alertas";
        sqlite3_close(db); return false;
    }

    rc = sqlite3_step(stmt);
    if (rc != SQLITE_DONE) {
        msg_error = "Error ejecutando limpieza";
        sqlite3_finalize(stmt); sqlite3_close(db); return false;
    }

    total_eliminados = sqlite3_changes(db);
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    return true;
}

int contar_filas(const string& tabla) {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;
    int conteo = 0;

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) { if (db) sqlite3_close(db); return 0; }

    string sql = "SELECT COUNT(*) FROM " + tabla + ";";
    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);

    if (rc == SQLITE_OK)
        if (sqlite3_step(stmt) == SQLITE_ROW)
            conteo = sqlite3_column_int(stmt, 0);

    if (stmt) sqlite3_finalize(stmt);
    sqlite3_close(db);
    return conteo;
}

// =========================
// EVALUACION DE ALERTAS
// =========================
void evaluar_alertas(const string& sensor_id, double valor) {
    string tipo_sensor;
    if (!obtener_tipo_sensor(sensor_id, tipo_sensor)) return;

    string msg_error;
    string nivel;
    string mensaje;

    if (tipo_sensor == "co2") {
        if (valor > 1000.0)      { nivel = "high";   mensaje = "Nivel de CO2 peligroso detectado"; }
        else if (valor > 700.0)  { nivel = "medium"; mensaje = "Nivel de CO2 elevado"; }
    } else if (tipo_sensor == "ruido") {
        if (valor > 85.0)        { nivel = "high";   mensaje = "Contaminacion acustica grave detectada"; }
        else if (valor > 65.0)   { nivel = "medium"; mensaje = "Nivel de ruido elevado"; }
    } else if (tipo_sensor == "temperatura") {
        if (valor > 38.0)        { nivel = "high";   mensaje = "Temperatura ambiental critica"; }
        else if (valor > 32.0)   { nivel = "medium"; mensaje = "Temperatura ambiental alta"; }
    } else if (tipo_sensor == "pm25") {
        if (valor > 55.0)        { nivel = "high";   mensaje = "Particulas PM2.5 en nivel peligroso"; }
        else if (valor > 35.0)   { nivel = "medium"; mensaje = "Particulas PM2.5 sobre limite recomendado"; }
    } else if (tipo_sensor == "humedad") {
        if (valor > 90.0)        { nivel = "medium"; mensaje = "Humedad relativa muy alta"; }
        else if (valor < 15.0)   { nivel = "medium"; mensaje = "Humedad relativa muy baja"; }
    } else if (tipo_sensor == "uv") {
        if (valor > 10.0)        { nivel = "high";   mensaje = "Indice UV extremo detectado"; }
        else if (valor > 7.0)    { nivel = "medium"; mensaje = "Indice UV muy alto"; }
    }

    if (!nivel.empty())
        insertar_alerta(sensor_id, nivel, mensaje, msg_error);
}

// =========================
// RESPUESTAS
// =========================
string respuesta_sensores() {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;
    string respuesta = "SENSORS\n";

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) { if (db) sqlite3_close(db); return "ERROR no_se_pudo_abrir_db\n"; }

    string sql = "SELECT id, tipo, zona, estado FROM sensores ORDER BY id;";
    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);
    if (rc != SQLITE_OK) { sqlite3_close(db); return "ERROR consulta_sensores_fallida\n"; }

    bool hay_filas = false;
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        hay_filas = true;
        const unsigned char* c0 = sqlite3_column_text(stmt, 0);
        const unsigned char* c1 = sqlite3_column_text(stmt, 1);
        const unsigned char* c2 = sqlite3_column_text(stmt, 2);
        const unsigned char* c3 = sqlite3_column_text(stmt, 3);

        string id     = c0 ? reinterpret_cast<const char*>(c0) : "";
        string tipo   = c1 ? reinterpret_cast<const char*>(c1) : "";
        string zona   = c2 ? reinterpret_cast<const char*>(c2) : "";
        string estado = c3 ? reinterpret_cast<const char*>(c3) : "";

        respuesta += id + " | " + tipo + " | " + zona + " | " + estado + "\n";
    }

    sqlite3_finalize(stmt);
    sqlite3_close(db);
    if (!hay_filas) return "SENSORS\nsin_resultados\n";
    return respuesta;
}

string respuesta_alertas() {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;
    string respuesta = "ALERTS\n";

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) { if (db) sqlite3_close(db); return "ERROR no_se_pudo_abrir_db\n"; }

    string sql = R"(
        SELECT alertas.id, alertas.sensor_id, sensores.tipo, alertas.nivel, alertas.mensaje, alertas.timestamp
        FROM alertas
        JOIN sensores ON alertas.sensor_id = sensores.id
        ORDER BY alertas.id DESC;
    )";

    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);
    if (rc != SQLITE_OK) { sqlite3_close(db); return "ERROR consulta_alertas_fallida\n"; }

    bool hay_filas = false;
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        hay_filas = true;
        int al_id = sqlite3_column_int(stmt, 0);
        const unsigned char* c1 = sqlite3_column_text(stmt, 1);
        const unsigned char* c2 = sqlite3_column_text(stmt, 2);
        const unsigned char* c3 = sqlite3_column_text(stmt, 3);
        const unsigned char* c4 = sqlite3_column_text(stmt, 4);
        const unsigned char* c5 = sqlite3_column_text(stmt, 5);

        string sensor_id  = c1 ? reinterpret_cast<const char*>(c1) : "";
        string tipo       = c2 ? reinterpret_cast<const char*>(c2) : "";
        string nivel      = c3 ? reinterpret_cast<const char*>(c3) : "";
        string msg        = c4 ? reinterpret_cast<const char*>(c4) : "";
        string ts         = c5 ? reinterpret_cast<const char*>(c5) : "";

        respuesta += to_string(al_id) + " | " + sensor_id + " | " + tipo + " | " +
                     nivel + " | " + msg + " | " + ts + "\n";
    }

    sqlite3_finalize(stmt);
    sqlite3_close(db);
    if (!hay_filas) return "ALERTS\nsin_resultados\n";
    return respuesta;
}

string respuesta_datos(const string& sensor_id) {
    sqlite3* db = nullptr;
    sqlite3_stmt* stmt = nullptr;
    string respuesta = "READINGS\n";

    int rc = sqlite3_open(DB_PATH.c_str(), &db);
    if (rc != SQLITE_OK) { if (db) sqlite3_close(db); return "ERROR no_se_pudo_abrir_db\n"; }

    string sql = R"(
        SELECT datos.id, datos.sensor_id, sensores.tipo, datos.valor, datos.timestamp
        FROM datos
        JOIN sensores ON datos.sensor_id = sensores.id
        WHERE datos.sensor_id = ?
        ORDER BY datos.id DESC
        LIMIT 10;
    )";

    rc = sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr);
    if (rc != SQLITE_OK) { sqlite3_close(db); return "ERROR consulta_datos_fallida\n"; }

    sqlite3_bind_text(stmt, 1, sensor_id.c_str(), -1, SQLITE_TRANSIENT);

    bool hay_filas = false;
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        hay_filas = true;
        int dato_id    = sqlite3_column_int(stmt, 0);
        const unsigned char* c1 = sqlite3_column_text(stmt, 1);
        const unsigned char* c2 = sqlite3_column_text(stmt, 2);
        double valor   = sqlite3_column_double(stmt, 3);
        const unsigned char* c4 = sqlite3_column_text(stmt, 4);

        string sid  = c1 ? reinterpret_cast<const char*>(c1) : "";
        string tipo = c2 ? reinterpret_cast<const char*>(c2) : "";
        string ts   = c4 ? reinterpret_cast<const char*>(c4) : "";

        respuesta += to_string(dato_id) + " | " + sid + " | " + tipo + " | " +
                     to_string(valor) + " | " + ts + "\n";
    }

    sqlite3_finalize(stmt);
    sqlite3_close(db);
    if (!hay_filas) return "READINGS\nsin_resultados\n";
    return respuesta;
}

string respuesta_estado_sistema() {
    int total_sensores = contar_filas("sensores");
    int total_alertas  = contar_filas("alertas");
    string estado_mon  = esta_pausado() ? "PAUSED" : "RUNNING";
    string estado_gral = total_alertas > 0 ? "ALERT" : "NORMAL";

    string respuesta = "SYSTEM_STATUS\n";
    respuesta += "overall | " + estado_gral + "\n";
    respuesta += "simulation | " + estado_mon + "\n";
    respuesta += "active_sensors | " + to_string(total_sensores) + "\n";
    respuesta += "active_alerts | " + to_string(total_alertas) + "\n";
    return respuesta;
}

// =========================
// PROTOCOLO
// =========================
string procesar_mensaje_pipe(const string& mensaje) {
    vector<string> partes = dividir(mensaje, '|');
    if (partes.empty()) return "ERROR formato_invalido\n";

    string comando = recortar(partes[0]);

    if (comando == "REGISTER") {
        if (partes.size() < 6) return "ERROR register_formato_invalido\n";

        string sensor_id = recortar(partes[1]);
        string tipo      = recortar(partes[2]);
        string zona      = recortar(partes[3]);
        string unidad    = recortar(partes[4]);
        string token     = recortar(partes[5]);
        (void)unidad;

        if (sensor_id.empty() || tipo.empty() || zona.empty() || token.empty())
            return "ERROR register_campos_invalidos\n";

        string msg_error;
        if (!registrar_sensor(sensor_id, tipo, zona, token, msg_error))
            return "ERROR no_se_pudo_registrar_sensor\n";

        return "OK REGISTERED\n";
    }

    if (comando == "MEASURE") {
        if (partes.size() < 4) return "ERROR measure_formato_invalido\n";
        if (esta_pausado()) return "OK SIMULATION_PAUSED\n";

        string sensor_id = recortar(partes[1]);
        string valor_str = recortar(partes[2]);
        string ts        = recortar(partes[3]);
        (void)ts;

        if (sensor_id.empty() || valor_str.empty())
            return "ERROR measure_campos_invalidos\n";

        if (!sensor_existe(sensor_id))
            return "ERROR sensor_no_registrado\n";

        double valor;
        try { valor = stod(valor_str); }
        catch (...) { return "ERROR valor_invalido\n"; }

        string msg_error;
        if (!insertar_dato(sensor_id, valor, msg_error))
            return "ERROR no_se_pudo_guardar_dato\n";

        evaluar_alertas(sensor_id, valor);
        return "OK MEASURE_RECEIVED\n";
    }

    if (comando == "HEARTBEAT") {
        if (partes.size() < 2) return "ERROR heartbeat_formato_invalido\n";
        string sensor_id = recortar(partes[1]);
        if (sensor_id.empty()) return "ERROR sensor_id_requerido\n";
        return "OK HEARTBEAT\n";
    }

    return "ERROR comando_no_reconocido\n";
}

string procesar_mensaje_espacio(const string& mensaje) {
    stringstream ss(mensaje);
    string comando;
    ss >> comando;

    if (comando == "SEND_READING") {
        if (esta_pausado()) return "OK SIMULATION_PAUSED\n";

        string sensor_id, token;
        double valor;
        ss >> sensor_id >> token >> valor;

        if (sensor_id.empty() || token.empty() || ss.fail())
            return "ERROR formato_invalido\n";

        if (!validar_token_sensor(sensor_id, token))
            return "ERROR token_invalido\n";

        string msg_error;
        if (!insertar_dato(sensor_id, valor, msg_error))
            return "ERROR no_se_pudo_guardar_dato\n";

        evaluar_alertas(sensor_id, valor);
        return "OK dato_guardado\n";
    }

    if (comando == "GET_SENSORS")   return respuesta_sensores();
    if (comando == "GET_ALERTS")    return respuesta_alertas();

    if (comando == "GET_READINGS") {
        string sensor_id;
        ss >> sensor_id;
        if (sensor_id.empty()) return "ERROR sensor_id_requerido\n";
        return respuesta_datos(sensor_id);
    }

    if (comando == "ACK_ALERT") {
        int alerta_id;
        ss >> alerta_id;
        if (ss.fail()) return "ERROR alerta_id_requerido\n";
        string msg_error;
        if (!confirmar_alerta_db(alerta_id, msg_error))
            return "ERROR " + msg_error + "\n";
        return "OK alert_acknowledged\n";
    }

    if (comando == "CLEAR_ALERTS") {
        string msg_error;
        int total_eliminados = 0;
        if (!limpiar_alertas_db(msg_error, total_eliminados))
            return "ERROR " + msg_error + "\n";
        return "OK cleared_alerts " + to_string(total_eliminados) + "\n";
    }

    if (comando == "SYSTEM_STATUS")        return respuesta_estado_sistema();
    if (comando == "PAUSE_SIMULATION")     { establecer_pausa(true);  return "OK simulation_paused\n"; }
    if (comando == "RESUME_SIMULATION")    { establecer_pausa(false); return "OK simulation_resumed\n"; }

    return "ERROR comando_no_reconocido\n";
}

string procesar_mensaje(const string& mensaje_raw) {
    string mensaje = recortar(mensaje_raw);
    if (mensaje.empty()) return "ERROR mensaje_vacio\n";
    if (mensaje.find('|') != string::npos) return procesar_mensaje_pipe(mensaje);
    return procesar_mensaje_espacio(mensaje);
}

// =========================
// CLIENTE
// =========================
void atender_cliente(int socket_cliente, string ip_cliente, int puerto_cliente, const string& archivo_log) {
    char buffer[4096];

    while (true) {
        memset(buffer, 0, sizeof(buffer));
        int bytes = recv(socket_cliente, buffer, sizeof(buffer) - 1, 0);

        if (bytes <= 0) {
            registrar_log(archivo_log, ip_cliente, puerto_cliente,
                          "DESCONEXION", "cliente_desconectado", "conexion_cerrada");
            break;
        }

        string mensaje(buffer, bytes);
        mensaje = recortar(mensaje);
        if (mensaje.empty()) continue;

        string respuesta = procesar_mensaje(mensaje);
        send(socket_cliente, respuesta.c_str(), respuesta.size(), 0);

        registrar_log(archivo_log, ip_cliente, puerto_cliente,
                      "SOLICITUD", mensaje, recortar(respuesta));
    }

    close(socket_cliente);
}

// =========================
// MAIN
// =========================
int main(int argc, char* argv[]) {
    if (argc < 3) {
        cerr << "Uso: ./servidor <puerto> <archivo_logs>" << endl;
        return 1;
    }

    int puerto = stoi(argv[1]);
    string archivo_log = argv[2];

    int servidor_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (servidor_fd == 0) { cerr << "Error creando socket" << endl; return 1; }

    int opt = 1;
    setsockopt(servidor_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in direccion;
    direccion.sin_family      = AF_INET;
    direccion.sin_addr.s_addr = INADDR_ANY;
    direccion.sin_port        = htons(puerto);

    if (bind(servidor_fd, (struct sockaddr*)&direccion, sizeof(direccion)) < 0) {
        cerr << "Error en bind" << endl; close(servidor_fd); return 1;
    }
    if (listen(servidor_fd, 20) < 0) {
        cerr << "Error en listen" << endl; close(servidor_fd); return 1;
    }

    cout << "=== Servidor de Monitoreo Ambiental Urbano ===" << endl;
    cout << "Escuchando en puerto " << puerto << endl;
    cout << "Archivo de logs: " << archivo_log << endl;

    while (true) {
        sockaddr_in addr_cliente;
        socklen_t len_cliente = sizeof(addr_cliente);

        int socket_cliente = accept(servidor_fd, (struct sockaddr*)&addr_cliente, &len_cliente);
        if (socket_cliente < 0) { cerr << "Error aceptando cliente" << endl; continue; }

        string ip_cliente    = inet_ntoa(addr_cliente.sin_addr);
        int puerto_cliente   = ntohs(addr_cliente.sin_port);

        registrar_log(archivo_log, ip_cliente, puerto_cliente,
                      "CONEXION", "nueva_conexion", "cliente_conectado");

        thread hilo(atender_cliente, socket_cliente, ip_cliente, puerto_cliente, archivo_log);
        hilo.detach();
    }

    close(servidor_fd);
    return 0;
}
