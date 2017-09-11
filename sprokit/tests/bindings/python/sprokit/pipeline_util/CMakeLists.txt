project(sprokit_test_python_sprokit_pipeline_util)

set(__modnames
  bake
  export_
  load
  )



if (KWIVER_ENABLE_TESTS)
  foreach (group IN LISTS __modnames)
    sprokit_discover_python_tests(${group} test-${group}.py)
  endforeach()
endif()
