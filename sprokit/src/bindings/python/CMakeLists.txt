#
#
#

project(sprokit_python)

set(boost_python_library     python)

if (KWIVER_ENABLE_PYTHON3)
  set(boost_python_library    python3)
endif ()

string(TOUPPER ${boost_python_library} boost_python_library_upper)
set(boost_python_library_var
  Boost_${boost_python_library_upper}_LIBRARY)

find_package(Boost ${sprokit_boost_version} REQUIRED
  COMPONENTS
    iostreams
    ${boost_python_library})

find_package(PythonLibs ${PYTHON_VERSION} REQUIRED)
include_directories(SYSTEM ${PYTHON_INCLUDE_DIR})

sprokit_use_python_fixes()

###
#
function (_sprokit_add_python_library name modpath)
  _sprokit_create_safe_modpath(${modpath} safe_modpath)

  sprokit_add_python_library(${name} ${modpath}
    ${ARGN})

  sprokit_require_python_fixes(python-${safe_modpath}-${name})
endfunction ()

add_subdirectory(sprokit)
add_subdirectory(modules)
add_subdirectory(processes)
add_subdirectory(schedulers)
add_subdirectory(test)

set(python_noarch FALSE)
sprokit_add_python_module(${CMAKE_CURRENT_SOURCE_DIR}/__init__.py
                          sprokit __init__)
set(python_noarch TRUE)
sprokit_add_python_module(${CMAKE_CURRENT_SOURCE_DIR}/__init__.py
                          sprokit __init__)
set(python_noarch FALSE)
