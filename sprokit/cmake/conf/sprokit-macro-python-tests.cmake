# Should these functions be rectified with the kwiver versions
# in kwiver/CMake/utils/kwiver-utils-python-tests.cmake ?


find_package(PythonInterp ${PYTHON_VERSION} REQUIRED)

# TODO: Use "$<CONFIGURATION>" and remove chdir below when generator
# expressions are supported in test properties.
if (WIN32)
  set(sprokit_test_working_path
    "${sprokit_output_dir}/bin")
endif ()

cmake_dependent_option(SPROKIT_ENABLE_COVERAGE_PYTHON "" ON
  SPROKIT_ENABLE_COVERAGE OFF)

if (SPROKIT_ENABLE_COVERAGE_PYTHON)
  set(sprokit_test_runner
    "${PYTHON_EXECUTABLE}"
    -m trace
    --count
    --coverdir "${sprokit_test_working_path}"
    --ignore-dir="\$prefix"
    --ignore-dir="\$exec_prefix")
else ()
  set(sprokit_test_runner
    "${PYTHON_EXECUTABLE}")
endif ()

###
#
# Configures the python test file to the ctest bin directory
#
# Args:
#     group: the suffix of the python file. Weird. We probably should just
#     use the filename.
#     input: filename of the test .py file (includes the extension)
#
# SeeAlso:
#     ../../../cmake/conf/sprokit-macro-tests.cmake
#     ../../../cmake/conf/sprokit-macro-python.cmake
#     ../../../cmake/conf/sprokit-macro-configure.cmake
#     ../../../cmake/support/tests.cmake
#
function (sprokit_build_python_test group input)

  if (CMAKE_CONFIGURATION_TYPES)
    set(sprokit_configure_cmake_args
      "\"-Dconfig=${CMAKE_CFG_INTDIR}/\"")
  endif ()

  set(name test-python-${group})
  set(source "${CMAKE_CURRENT_SOURCE_DIR}/${input}")
  set(dest "${sprokit_test_output_path}/\${config}test-python-${group}")

  if (KWIVER_SYMLINK_PYTHON)
      sprokit_symlink_file(${name} ${source} ${dest} PYTHON_EXECUTABLE)
  else()
      sprokit_configure_file(${name} ${source} ${dest} PYTHON_EXECUTABLE)
  endif()
  sprokit_declare_tooled_test(python-${group})

endfunction ()


###
# Calls CMake `add_test` function under the hood
function (sprokit_add_python_test group instance)
  message(STATUS "ADD SPROKIT PY-TEST")
  message(STATUS " group = ${group}")
  message(STATUS " instance = ${instance}")

  set(python_module_path    "${sprokit_python_output_path}/${sprokit_python_subdir}")
  set(python_chdir          ".")

  if (CMAKE_CONFIGURATION_TYPES)
    set(python_module_path      "${sprokit_python_output_path}/$<CONFIGURATION>/${sprokit_python_subdir}")
    set(python_chdir           "$<CONFIGURATION>")
  endif ()

  # Note: `sprokit_test_runner` is set to the python executable which is
  # implicitly passed down to sprokit_add_tooled_test.

  _kwiver_python_site_package_dir( site_dir )
  sprokit_add_tooled_test(python-${group} ${instance}
    "${python_chdir}" "${python_module_path}/${site_dir}" ${ARGN})
endfunction ()


###
#
# Searches test .py files for functions that begin with "test" and creates a
# separate `ctest` for each. Ideally we would just map the output from
# something like `py.test` to `ctest` instead.
#
# Arg:
#     group: the test is registered with this ctests group
#     file: filename of the test .py file (includes the extension)
#
# SeeAlso:
#     kwiver/CMake/utils/kwiver-utils-python-tests.cmake - defines kwiver_discover_python_tests
#     kwiver/sprokit/tests/bindings/python/sprokit/pipeline/CMakeLists.txt - uses this function
#
function (sprokit_discover_python_tests group file)
  message(STATUS "DISCOVER SPROKIT PY-TESTS")
  message(STATUS " group = ${group}")
  message(STATUS " file = ${file}")

  set(properties)

  set(group "${group}.py")

  # Register the python file as a test script
  sprokit_build_python_test("${group}" "${file}")

  # Define a python test for each testable function / method
  set(py_fpath "${CMAKE_CURRENT_SOURCE_DIR}/${file}")
  parse_python_testables("${py_fpath}" _testables)
  foreach (test_name IN LISTS _testables)
    sprokit_add_python_test("${group}" "${test_name}" ${ARGN})
  endforeach()

  #file(STRINGS "${file}" test_lines)
  #foreach (test_line IN LISTS test_lines)
  #  set(test_name)
  #  set(property)
  #  # Find python functions that start with test.
  #  # perhaps use AST parsing in the future?
  #  string(REGEX MATCH "^def test_([A-Za-z_]+)\\(.*\\):$"
  #    match "${test_line}")
  #  if (match)
  #    set(test_name "${CMAKE_MATCH_1}")
  #    sprokit_add_python_test("${group}" "${test_name}"
  #      ${ARGN})
  #    if (properties)
  #      set_tests_properties("test-python-${group}-${test_name}"
  #        PROPERTIES
  #          ${properties})
  #    endif ()
  #    set(properties)
  #  endif ()
  #  string(REGEX MATCHALL "^# TEST_PROPERTY\\(([A-Za-z_]+), (.*)\\)$"
  #    match "${test_line}")
  #  if (match)
  #    set(prop "${CMAKE_MATCH_1}")
  #    string(CONFIGURE "${CMAKE_MATCH_2}" prop_value
  #      @ONLY)
  #    if (prop STREQUAL "ENVIRONMENT")
  #      set(sprokit_test_environment
  #        "${prop_value}")
  #    else ()
  #      set(property "${prop}" "${prop_value}")
  #      list(APPEND properties
  #        "${property}")
  #    endif ()
  #  endif ()
  #endforeach ()
endfunction ()
