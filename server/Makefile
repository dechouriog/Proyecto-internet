CXX      = g++
CXXFLAGS = -std=c++17 -pthread -Wall
LIBS     = -lsqlite3

servidor: server.cpp
	$(CXX) $(CXXFLAGS) -o servidor server.cpp $(LIBS)

clean:
	rm -f servidor
