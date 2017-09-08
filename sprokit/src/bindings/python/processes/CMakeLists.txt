project(sprokit_python_processes)

set(python_both_arch TRUE)

sprokit_add_python_module(${CMAKE_CURRENT_SOURCE_DIR}/__init__.py
                          sprokit/processes __init__)

if (KWIVER_ENABLE_TESTS)
  add_subdirectory(test)
endif ()
