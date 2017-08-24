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
#     kwiver-utils-tests.cmake
#     sprokit/cmake/conf/sprokit-macro-python-tests.cmake
#
function (kwiver_build_python_test group input)
  # seems unused
  #if (CMAKE_CONFIGURATION_TYPES)
  #    set(kwiver_configure_cmake_args
  #        "\"-Dconfig=${CMAKE_CFG_INTDIR}/\"")
  #endif ()

  set(name test-python-${group})
  set(source "${CMAKE_CURRENT_SOURCE_DIR}/${input}")
  set(dest "${kwiver_test_output_path}/\${config}test-python-${group}")

  if (KWIVER_SYMLINK_PYTHON)
      kwiver_symlink_file(${name} ${source} ${dest} PYTHON_EXECUTABLE)
  else()
      kwiver_configure_file(${name} ${source} ${dest} PYTHON_EXECUTABLE)
  endif()
  kwiver_declare_test(python-${group})

endfunction ()


###
#
# Calls add_test similar to kwiver_add_test, but formats arguments such that
# py.test can be used
function (kwiver_add_python_test group instance)

  _kwiver_python_site_package_dir( site_dir )

  set(oneValueArgs TEST_OUTPUT_PATH PYTHON_MODULE_PATH)
  cmake_parse_arguments(my "" "${oneValueArgs}" "" ${ARGN} )
  # keyword argument defaults
  if (NOT my_TEST_OUTPUT_PATH)
    set(my_TEST_OUTPUT_PATH "${kwiver_test_output_path}")
  endif()
  if (NOT my_PYTHON_MODULE_PATH)
    set(my_PYTHON_MODULE_PATH "${kwiver_python_output_path}")
  endif()


  # Dont call kwiver_add_test because we need to set `kwiver_test_runner`
  # globally, which may still be expected to be empty. It would be nice if this
  # var could be passed down explicitly. However, just doing it here lets us
  # hook into py.test in a bit easier. We need to revisit `kwiver_add_test`
  # only if those extra options are actually necessary for python.

  #kwiver_add_test(python-${group} ${instance}
  #  "${python_chdir}" "${my_PYTHON_MODULE_PATH}/${site_dir}" ${ARGN})

  set(name python-${group})
  set(test_name test-${name}-${instance})
  set(test_path "${my_TEST_OUTPUT_PATH}/test-${name}")

  # do we need to worry about "noarch" stuff here?
  set(python_test_env "PYTHONPATH=${my_PYTHON_MODULE_PATH}/${site_dir}")

  set(_node_suffix "${instance}")
  # HACK: to put brakets back in
  # FIXME: ctest still breaks even if this is specified. I guess
  # we just have to run all paramatraziations as a single test.
  string(REPLACE "-LBRAK-" "[" _node_suffix "${_node_suffix}")
  string(REPLACE "-RBRAK-" "]" _node_suffix "${_node_suffix}")

  set(pytest_node "${test_path}::${_node_suffix}")
  #message(STATUS "_node_suffix = ${_node_suffix}")

  # Run the python test through py.test
  add_test(
    NAME    ${test_name}
    COMMAND "${PYTHON_EXECUTABLE}" -m pytest "${pytest_node}" ${my_ARGN}
    )
  set_tests_properties(${test_name}
    PROPERTIES
    ENVIRONMENT "${python_test_env}")

endfunction ()



###
#
# Wrapper around python helper function that parses testable functions in a file
#
# Args:
#     py_fpath: filepath to the python file
#     outvar: output variable which will contain a list of testable functions
#     in the py.test node name suffix format
#     (e.g. test_func, TestClass::test_func)
#
function (parse_python_testables py_fpath outvar)
  # Run a python script that does AST parsing to find all testable
  # functions/methods prefixed with `_test`.
  set(discover_tests_py "${CMAKE_SOURCE_DIR}/CMake/tools/discover_python_tests.py")
  # Each testable item is printed in its own line
  # functions are printed in the format `<funcname>`
  # methods are printed in the format `<classname>::<funcname>`
  execute_process(COMMAND "${PYTHON_EXECUTABLE}" ${discover_tests_py}
    ${py_fpath}
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

  set(output_list)

  # Fixup formatting and skip if the line is empty
  foreach (test_name IN LISTS __testname_list)
    string(STRIP "${test_name}" test_name)
    string(LENGTH "${test_name}" test_name_len)
    if (NOT ${test_name_len} EQUAL 0)
      list(APPEND output_list "${test_name}")
    endif()
  endforeach()

  set(${outvar} ${output_list} PARENT_SCOPE)
endfunction()


###
#
# Searches test .py files for functions that begin with "test" and creates a
# separate `ctest` for each. Ideally we would just map the output from
# something like `py.test` to `ctest` instead.
#
# Args:
#     group: the test is registered with this ctests group
#     file: filename of the test .py file (includes the extension)
#
# SeeAlso:
#     sprokit/cmake/conf/sprokit-macro-python-tests.cmake
#
function (kwiver_discover_python_tests group file)

  set(properties)

  set(group "${group}.py")

  # Register the python file as a test script
  kwiver_build_python_test("${group}" "${file}")

  # Define a python test for each testable function / method
  set(py_fpath "${CMAKE_CURRENT_SOURCE_DIR}/${file}")
  parse_python_testables("${py_fpath}" _testables)
  foreach (test_name IN LISTS _testables)
    kwiver_add_python_test("${group}" "${test_name}" ${ARGN})
  endforeach()

endfunction ()
