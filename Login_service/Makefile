CXX      = g++
CXXFLAGS = -std=c++17 -pthread -Wall
LIBS     = -lsqlite3

login_service: servicio_login.cpp db_manager.cpp verificador_identidad.cpp verificador_token.cpp operaciones_usuario.cpp manejador_sesion.cpp
	$(CXX) $(CXXFLAGS) -o login_service $^ $(LIBS)

clean:
	rm -f login_service users.db log_sesiones
