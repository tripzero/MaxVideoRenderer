project(maxiod)
cmake_minimum_required(VERSION 2.8.11)

configure_file (${CMAKE_CURRENT_SOURCE_DIR}/maxiod.py ${CMAKE_CURRENT_BINARY_DIR}/maxiod @ONLY)
configure_file (${CMAKE_CURRENT_SOURCE_DIR}/maxiod.py ${CMAKE_CURRENT_BINARY_DIR}/maxiod @ONLY)

install (PROGRAMS ${CMAKE_CURRENT_BINARY_DIR}/maxiod DESTINATION bin)
install (FILES ${CMAKE_CURRENT_BINARY_DIR}/maxiod.conf DESTINATION /etc/dbus-1/system.d)
