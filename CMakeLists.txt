project(maxrenderer)
cmake_minimum_required(VERSION 2.8.11)

find_package(PythonInterp 2.7 REQUIRED)

set(PROJECT_NAME "iod")

set(DBUS_SERVICE "io.tripzero.${PROJECT_NAME}")
set(INTERFACE_PREFIX ${DBUS_SERVICE})

configure_file (${CMAKE_CURRENT_SOURCE_DIR}/maxrenderer.py ${CMAKE_CURRENT_BINARY_DIR}/maxrenderer.py @ONLY)
configure_file (${CMAKE_CURRENT_SOURCE_DIR}/videoplayer.py ${CMAKE_CURRENT_BINARY_DIR}/videoplayer.py @ONLY)
configure_file (${CMAKE_CURRENT_SOURCE_DIR}/lights.py ${CMAKE_CURRENT_BINARY_DIR}/lights.py @ONLY)
configure_file (${CMAKE_CURRENT_SOURCE_DIR}/opencvfilter/opencvfilter.py ${CMAKE_CURRENT_BINARY_DIR}/opencvfilter/opencvfilter.py @ONLY)
configure_file (${CMAKE_CURRENT_SOURCE_DIR}/gst_hacks.py ${CMAKE_CURRENT_BINARY_DIR}/gst_hacks.py @ONLY)
configure_file (${CMAKE_CURRENT_SOURCE_DIR}/config.json ${CMAKE_CURRENT_BINARY_DIR}/config.json @ONLY)

execute_process (
   COMMAND ${PYTHON_EXECUTABLE} -c
	   "import site, sys; sys.stdout.write(site.PREFIXES[-1])"
   OUTPUT_VARIABLE PYTHON_PREFIX
)
file ( TO_CMAKE_PATH "${PYTHON_PREFIX}" PYTHON_PREFIX )
execute_process (
   COMMAND ${PYTHON_EXECUTABLE} -c
	   "import site, sys; sys.stdout.write(site.getsitepackages()[-1])"
   OUTPUT_VARIABLE PYTHON_SITE_DIR
)
file ( TO_CMAKE_PATH "${PYTHON_SITE_DIR}" PYTHON_SITE_DIR )
string ( REGEX REPLACE "^${PYTHON_PREFIX}/" ""
   PYTHON_SITE_DIR "${PYTHON_SITE_DIR}"
)

install (PROGRAMS ${CMAKE_CURRENT_BINARY_DIR}/iod DESTINATION bin)
install (FILES ${CMAKE_CURRENT_BINARY_DIR}/iod.conf DESTINATION /etc/dbus-1/system.d)

install (FILES ${CMAKE_CURRENT_BINARY_DIR}/iodclient.py
		 DESTINATION ${PYTHON_SITE_DIR})
