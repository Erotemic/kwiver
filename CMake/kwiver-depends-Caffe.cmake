# Optionally find and configure Caffe dependency

message(STATUS "Hi I am Caffe!")
option( KWIVER_ENABLE_CAFFE
  "Enable Caffe dependent code and plugins (Arrows)"
  OFF
  )
mark_as_advanced( KWIVER_ENABLE_CAFFE )

if( KWIVER_ENABLE_CAFFE )
  find_package( Caffe REQUIRED )
endif( KWIVER_ENABLE_CAFFE )
