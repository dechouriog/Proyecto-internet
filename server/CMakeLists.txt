cmake_minimum_required(VERSION 3.10)
project(ServidorAmbientalUrbano)

set(CMAKE_CXX_STANDARD 17)

find_package(Threads REQUIRED)
find_path(SQLITE3_INCLUDE_DIR sqlite3.h)
find_library(SQLITE3_LIBRARY sqlite3)

if(NOT SQLITE3_LIBRARY)
    message(FATAL_ERROR "SQLite3 no encontrado. Instalar con: sudo apt install libsqlite3-dev")
endif()

add_executable(servidor server.cpp)
target_include_directories(servidor PRIVATE ${SQLITE3_INCLUDE_DIR})
target_link_libraries(servidor Threads::Threads ${SQLITE3_LIBRARY})

message(STATUS "SQLite3: ${SQLITE3_LIBRARY}")
