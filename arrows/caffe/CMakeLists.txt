# Build/install plugin for caffe CNN support
#

set( headers
        caffe_segnet_segmentor.h
)

set( sources
        caffe_segnet_segmentor.cxx
  )

set( caffe_linked_libs
  ${Caffe_LIBRARIES}
  kwiversys
  ${Boost_SYSTEM_LIBRARY}
  ${Boost_FILESYSTEM_LIBRARY}
  kwiver_algo_ocv )

kwiver_install_headers(
  SUBDIR     arrows/caffe
  ${headers}
  )
kwiver_install_headers(
  ${CMAKE_CURRENT_BINARY_DIR}/kwiver_algo_caffe_export.h
  NOPATH   SUBDIR     arrows/caffe
  )

kwiver_add_library( kwiver_algo_caffe
  ${headers}
  ${sources}
  )

target_link_libraries( kwiver_algo_caffe
  PUBLIC               vital_algo
  PRIVATE              ${caffe_linked_libs}
  )

algorithms_create_plugin( kwiver_algo_caffe
  register_algorithms.cxx
  )
