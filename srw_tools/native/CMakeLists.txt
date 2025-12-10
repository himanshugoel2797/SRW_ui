cmake_minimum_required(VERSION 3.14)
project(srw_native LANGUAGES C CXX)

# Build a shared library providing a minimal C API consumed by Python.
# The library name will be "srwfast" (libsrwfast.so / srwfast.dll / libsrwfast.dylib)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

message(STATUS "Building shared native library 'srwfast'.")
add_library(srwfast SHARED
    src/fastlib.cpp
)
target_include_directories(srwfast PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Provide header visibility
target_include_directories(srwfast PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Default: install to SRW_NATIVE_LIB_DIR if provided, otherwise to build directory
install(TARGETS srwfast
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib)

message(STATUS "srwfast library configured")

# Build an importable Python extension module named `nativelib` which wraps the
# srwfast C functions for direct Python imports (no ctypes required).
find_package(Python3 COMPONENTS Development REQUIRED)

# Determine numpy include dir by asking Python. This should be available if
# NumPy is installed in the build environment.
execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import numpy; print(numpy.get_include())"
    OUTPUT_VARIABLE NUMPY_INCLUDE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

add_library(nativelib MODULE
    src/py_nativelib.cpp
)
target_include_directories(nativelib PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include ${Python3_INCLUDE_DIRS} ${NUMPY_INCLUDE_DIR})
target_link_libraries(nativelib PRIVATE srwfast ${Python3_LIBRARIES})

# On most platforms Python extension modules should not have the lib prefix
set_target_properties(nativelib PROPERTIES PREFIX "" )

install(TARGETS nativelib
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib)

message(STATUS "nativelib Python extension configured")
