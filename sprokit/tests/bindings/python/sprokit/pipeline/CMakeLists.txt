project(sprokit_test_python_sprokit_pipeline)

set(__testable_modnames
  config
  datum
  edge
  modules
  pipeline
  process
  process_cluster
  process_registry
  scheduler
  scheduler_registry
  stamp
  utils
  version
  )

# Add files to the vital.tests python module
foreach (modname IN LISTS __all_modnames)
  message(STATUS "modname = ${modname}")
  kwiver_add_python_module( ${CMAKE_CURRENT_SOURCE_DIR}/${modname}.py
    vital/tests
    ${modname})
endforeach()


if (KWIVER_ENABLE_TESTS)
  # SeeAlso:
  #     # defines sprokit_discover_python_tests
  #     sprokit/cmake/conf/sprokit-macro-python-tests.cmake
  sprokit_discover_python_tests(config test-config.py)
endif()

##############################
# Config tests
##############################
sprokit_discover_python_tests(config test-config.py)


##############################
# Run tests
##############################
sprokit_build_python_test(run test-run.py)

set(schedulers
  pythread_per_process
  sync
  thread_per_process)

function (sprokit_add_python_run_test group instance)
  foreach (scheduler IN LISTS schedulers)
    sprokit_add_python_test(${group} ${instance}-${scheduler})

    set_tests_properties(test-python-${group}-${instance}-${scheduler}
      PROPERTIES
        TIMEOUT 5)
  endforeach ()
endfunction ()

sprokit_add_python_run_test(run python_to_python)
sprokit_add_python_run_test(run cpp_to_python)
sprokit_add_python_run_test(run python_to_cpp)
sprokit_add_python_run_test(run python_via_cpp)
