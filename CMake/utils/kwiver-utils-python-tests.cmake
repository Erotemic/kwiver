###
#
# """
# Configures the python test file to the ctest bin directory
#
# Args:
#     group: the suffix of the python file. Weird. We probably should just
#     use the filename.
#     input: filename of the test .py file (includes the extension)
#
# SeeAlso:
#     kwiver-utils-tests.cmake
#     sprokit/tests/bindings/python/CMakeLists.txt - sprokit version of this func
# """
function (kwiver_build_python_test group input)
  # seems unused
  #if (CMAKE_CONFIGURATION_TYPES)
  #    set(kwiver_configure_cmake_args
  #        "\"-Dconfig=${CMAKE_CFG_INTDIR}/\"")
  #endif ()

  set(name test-python-${group})
  set(source "${CMAKE_CURRENT_SOURCE_DIR}/${input}")
  set(dest "${kwiver_test_output_path}/\${config}test-python-${group}")

  message(STATUS "dest = ${dest}")

  if (KWIVER_SYMLINK_PYTHON)
      kwiver_symlink_file(${name} ${source} ${dest} PYTHON_EXECUTABLE)
  else()
      kwiver_configure_file(${name} ${source} ${dest} PYTHON_EXECUTABLE)
  endif()
  kwiver_declare_test(python-${group})

endfunction ()


###
#
# """
# Seems to call the CMAKE `add_test` function under the hood
# """
function (kwiver_add_python_test group instance)
  set(python_module_path    "${kwiver_python_output_path}")

  _kwiver_python_site_package_dir( site_dir )

  # Dont call kwiver_add_test because we need to set `kwiver_test_runner`
  # globally, which may still be expected to be empty. It would be nice if this
  # var could be passed down explicitly. However, just doing it here lets us
  # hook into py.test in a bit easier. We need to revisit `kwiver_add_test`
  # only if those extra options are actually necessary for python.

  #kwiver_add_test(python-${group} ${instance}
  #  "${python_chdir}" "${python_module_path}/${site_dir}" ${ARGN})

  set(name python-${group})
  set(test_name test-${name}-${instance})
  set(test_path "${kwiver_test_output_path}/test-${name}")

  # do we need to worry about "noarch" stuff here?
  set(python_test_env "PYTHONPATH=${python_module_path}/${site_dir}")
  # Run the python test through py.test
  add_test(
    NAME    ${test_name}
    COMMAND "${PYTHON_EXECUTABLE}" -m pytest "${test_path}::${instance}" ${ARGN}
    )
  set_tests_properties(${test_name}
    PROPERTIES
    ENVIRONMENT "${python_test_env}")

endfunction ()


###
#
# """
# Searches test .py files for functions that begin with "test" and creates a
# separate `ctest` for each. Ideally we would just map the output from
# something like `py.test` to `ctest` instead.
#
# Args:
#     group: the test is registered with this ctests group
#     file: filename of the test .py file (includes the extension)
#
# SeeAlso:
#     sprokit/tests/bindings/python/CMakeLists.txt - defines sprokit_discover_python_tests
# """
function (kwiver_discover_python_tests group file)

  set(properties)

  set(group "${group}.py")

  kwiver_build_python_test("${group}" "${file}")

  # Run a python script that does AST parsing to find all testable
  # functions/methods prefixed with `_test`.
  set(discover_tests_py "${CMAKE_SOURCE_DIR}/CMake/tools/discover_python_tests.py")
  # Each testable item is printed in its own line
  # functions are printed in the format `<funcname>`
  # methods are printed in the format `<classname>::<funcname>`
  execute_process(COMMAND "${PYTHON_EXECUTABLE}" ${discover_tests_py}
    ${CMAKE_CURRENT_SOURCE_DIR}/${file}
    RESULT_VARIABLE _parse_result
    OUTPUT_VARIABLE _parse_output)
  if (NOT ${_parse_result} EQUAL 0)
    message(FATAL_ERROR "
      Failed to discover python tests due to an error in the parsing script.
      Parsing script return code: ${_parse_result}
      Parsing script output:\n\n${_parse_output}")
  endif()
  # Convert newline separated output into a list
  string(REPLACE "\n" ";" __testname_list ${_parse_output})

  # Define a python test for each testable function / method
  foreach (test_name IN LISTS __testname_list)
    # Fixup formatting and skip if the line is empty
    string(STRIP "${test_name}" test_name)
    string(LENGTH "${test_name}" test_name_len)
    if (NOT ${test_name_len} EQUAL 0)
      kwiver_add_python_test("${group}" "${test_name}" ${ARGN})
    endif()
  endforeach()
endfunction ()
