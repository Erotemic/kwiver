# Build/install plugin for segnet CNN support
#

set( headers
  segnet_segmentation.h
)

set( sources
  segnet_segmentation.cxx
  )

set( segnet_linked_libs
  ${VIDTK_LIBRARIES}
  kwiversys
  ${Boost_SYSTEM_LIBRARY}
  ${Boost_FILESYSTEM_LIBRARY}
  kwiver_algo_ocv )

kwiver_install_headers(
  SUBDIR     arrows/segnet
  ${headers}
  )
kwiver_install_headers(
  ${CMAKE_CURRENT_BINARY_DIR}/kwiver_algo_segnet_export.h
  NOPATH   SUBDIR     arrows/segnet
  )

kwiver_add_library( kwiver_algo_segnet
  ${headers}
  ${sources}
  )

target_link_libraries( kwiver_algo_segnet
  PUBLIC               vital_algo
  PRIVATE              ${segnet_linked_libs}
  )

algorithms_create_plugin( kwiver_algo_segnet
  register_algorithms.cxx
  )
