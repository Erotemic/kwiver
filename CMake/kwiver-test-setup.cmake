#
# Script to set up testing environment for kwiver components
#

set(no_install TRUE)

if (WIN32)

  # TODO: Output to a different directory and then use $<CONFIGURATION> in the
  # working path when generator expressions are supported in test properties.
  set(kwiver_test_output_path    "${KWIVER_BINARY_DIR}/bin")

else ()

  set(kwiver_test_output_path    "${KWIVER_BINARY_DIR}/tests/bin")
  set(kwiver_test_working_path    "${KWIVER_BINARY_DIR}/tests")

endif ()

set(kwiver_test_data_directory  "${CMAKE_CURRENT_SOURCE_DIR}/data")

include_directories("${CMAKE_CURRENT_SOURCE_DIR}")
include_directories("${KWIVER_SOURCE_DIR}")
#include_directories("${KWIVER_SOURCE_DIR}/kwiver")
include_directories("${KWIVER_BINARY_DIR}")
#include_directories("${KWIVER_BINARY_DIR}/kwiver")

# this sets the data directory relative to the current "tests" directory
include_directories("${KWIVER_SOURCE_DIR}/tests") # to pick up test_common.h -> there may be a better place for this
