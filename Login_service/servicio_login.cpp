#include "db_manager.h"
#include "verificador_token.h"
#include "verificador_identidad.h"
#include "operaciones_usuario.h"
#include "manejador_sesion.h"

#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <thread>
#include <cstring>
#include <unistd.h>
#include <arpa/inet.h>

using namespace std;

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
    while (getline(ss, item, delimitador)) partes.push_back(item);
    return partes;
}

string usuarios_a_string(const RespuestaListaUsuarios& resp) {
    string result = "OK|USERS|" + resp.mensaje + "\n";
    for (const auto& u : resp.usuarios)
        result += u.id + "|" + u.usuario + "|" + u.nombre + "|" + u.rol + "\n";
    return result;
}

string procesar_mensaje(const string& mensaje_raw, ManejadorSesion& manejador) {
    string mensaje = recortar(mensaje_raw);
    if (mensaje.empty()) return "ERROR|empty_message\n";

    vector<string> partes = dividir(mensaje, '|');
    if (partes.empty()) return "ERROR|invalid_format\n";

    string comando = partes[0];

    if (comando == "LOGIN") {
        if (partes.size() != 3) return "ERROR|LOGIN_format\n";
        auto res = manejador.iniciar_sesion(partes[1], partes[2]);
        if (res.id == "0") return "ERROR|LOGIN|" + res.mensaje + "\n";
        return "OK|LOGIN|" + res.id + "|" + res.token + "|" + res.r_token + "|" + res.mensaje + "\n";
    }

    if (comando == "VALIDATE") {
        if (partes.size() != 4) return "ERROR|VALIDATE_format\n";
        auto res = manejador.validar_tokens(partes[1], partes[2], partes[3]);
        if (res.token == "0") return "ERROR|VALIDATE|" + res.mensaje + "\n";
        return "OK|VALIDATE|" + res.token + "|" + res.r_token + "|" + res.mensaje + "\n";
    }

    if (comando == "LOGOUT") {
        if (partes.size() != 4) return "ERROR|LOGOUT_format\n";
        manejador.cerrar_sesion(partes[1], partes[2], partes[3]);
        return "OK|LOGOUT|session_closed\n";
    }

    if (comando == "LIST_USERS") {
        if (partes.size() != 4) return "ERROR|LIST_USERS_format\n";
        auto res = manejador.listar_usuarios(partes[1], partes[2], partes[3]);
        return usuarios_a_string(res);
    }

    if (comando == "CREATE_USER") {
        if (partes.size() != 8) return "ERROR|CREATE_USER_format\n";
        auto res = manejador.crear_usuario(partes[1], partes[2], partes[3], partes[4], partes[5], partes[6], partes[7]);
        if (!res.exito || res.id == "0") return "ERROR|CREATE_USER|" + res.mensaje + "\n";
        return "OK|CREATE_USER|" + res.id + "|" + res.mensaje + "\n";
    }

    if (comando == "REMOVE_USER") {
        if (partes.size() != 5) return "ERROR|REMOVE_USER_format\n";
        auto res = manejador.eliminar_usuario(partes[1], partes[2], partes[3], partes[4]);
        if (!res.exito) return "ERROR|REMOVE_USER|" + res.mensaje + "\n";
        return "OK|REMOVE_USER|" + res.id + "|" + res.mensaje + "\n";
    }

    if (comando == "ROLE") {
        if (partes.size() != 2) return "ERROR|ROLE_format\n";
        auto res = manejador.verificar_admin(partes[1]);
        return string("OK|ROLE|") + (res.es_admin ? "admin" : "not_admin") + "|" + res.mensaje + "\n";
    }

    return "ERROR|unknown_command\n";
}

void atender_cliente(int socket_cliente, ManejadorSesion& manejador) {
    char buffer[4096];
    while (true) {
        memset(buffer, 0, sizeof(buffer));
        int bytes = read(socket_cliente, buffer, sizeof(buffer) - 1);
        if (bytes <= 0) break;
        string mensaje(buffer, bytes);
        string respuesta = procesar_mensaje(mensaje, manejador);
        send(socket_cliente, respuesta.c_str(), respuesta.size(), 0);
    }
    close(socket_cliente);
}

int main() {
    GestorDB gestorDB("users.db");
    gestorDB.crear_db();

    VerificadorIdentidad ver_identidad(gestorDB);
    VerificadorToken     ver_token(gestorDB);
    OperacionesUsuario   ops_usuario(gestorDB);
    ManejadorSesion      manejador(ver_identidad, ver_token, ops_usuario);

    int puerto = 6000;

    int servidor_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (servidor_fd == 0) { cerr << "Error creando socket del servicio de login" << endl; return 1; }

    int opt = 1;
    setsockopt(servidor_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr;
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port        = htons(puerto);

    if (bind(servidor_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        cerr << "Error en bind del servicio de login" << endl;
        close(servidor_fd); return 1;
    }
    if (listen(servidor_fd, 10) < 0) {
        cerr << "Error en listen del servicio de login" << endl;
        close(servidor_fd); return 1;
    }

    cout << "=== Servicio de Autenticacion Ambiental ===" << endl;
    cout << "Escuchando en puerto " << puerto << endl;

    while (true) {
        sockaddr_in addr_cliente;
        socklen_t len = sizeof(addr_cliente);
        int socket_cliente = accept(servidor_fd, (struct sockaddr*)&addr_cliente, &len);
        if (socket_cliente < 0) { cerr << "Error aceptando cliente en login" << endl; continue; }
        thread hilo(atender_cliente, socket_cliente, ref(manejador));
        hilo.detach();
    }

    close(servidor_fd);
    return 0;
}
