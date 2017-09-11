project(sprokit_test_python)


# Include the python helper functions previously defined here
include("${sprokit_source_dir}/conf/sprokit-macro-python-tests.cmake")


add_subdirectory(test)

add_subdirectory(sprokit)
add_subdirectory(modules)
