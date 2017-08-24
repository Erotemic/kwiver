project(sprokit_test_python_test)

set(sprokit_test_pipelines_directory
  "${sprokit_test_data_directory}/pipelines")

# Write a file that locates the pipeline directory for tests
sprokit_add_python_resource(
  pipeline_dir.txt
  sprokit/test
  sprokit_test_pipelines_directory
)


sprokit_add_python_module( ${CMAKE_CURRENT_SOURCE_DIR}/test-test.py
  sprokit/tests
  test-test)
sprokit_discover_python_tests(test test-test.py)
