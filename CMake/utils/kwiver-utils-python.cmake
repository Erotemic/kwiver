# Python functions for the kwiver project
# The following functions are defined:
#
#   kwiver_add_python_library
#   kwiver_add_python_module
#   kwiver_create_python_init
#   kwiver_create_python_plugin_init
#
# The following variables may be used to control the behavior of the functions:
#
#   kwiver_python_subdir
#     The subdirectory to use for Python modules (e.g., python2.7).
#
#   kwiver_python_output_path
#     The base output path for Python modules and libraries.
#
#   copyright_header
#     The copyright header to place at the top of generated __init__.py files.
#
#   python_both_arch
#     If set, __init__.py file is created for both the archful and pure-Python
#     module paths (if in doubt, you probably don't need this; it's necessary
#     to support CPython and pure Python kwiver plugins).
#
# Their syntax is:
#
#   kwiver_add_python_library(name modpath [source ...])
#     Builds and installs a library to be used as a Python module which may be
#     imported. It is built as a shared library, installed (use no_install to
#     not install the module), placed into the proper subdirectory but not
#     exported. Any other control variables for kwiver_add_library are
#     available.
#
#   kwiver_add_python_module(name modpath module)
#     Installs a pure-Python module into the 'modpath' and puts it into the
#     correct place in the build tree so that it may be used with any built
#     libraries in any build configuration.
#
#   kwiver_create_python_init(modpath [module ...])
#     Creates an __init__.py package file which imports the modules in the
#     arguments for the package.
#
#   kwiver_create_python_plugin_init(modpath)
#     Creates an __init__.py for use as a plugin package (packages for kwiver
#     plugins written in Python must use one of these files as the package
#     __init__.py file and added to the KWIVER_PYTHON_MODULES environment
#     variable).

if ( NOT TARGET python)
  add_custom_target(python)
endif()

source_group("Python Files"  REGULAR_EXPRESSION ".*\\.py\\.in$")
source_group("Python Files"  REGULAR_EXPRESSION ".*\\.py$")

# Global collection variables
define_property(GLOBAL PROPERTY kwiver_python_modules
  BRIEF_DOCS "Python modules generated by kwiver"
  FULL_DOCS "List of Python modiles build."
  )


###
#
macro (_kwiver_create_safe_modpath    modpath    result)
  string(REPLACE "/" "." "${result}" "${modpath}")
endmacro ()


###
#
# Get canonical directory for python site packages.
# It varys from system to system.
#
# Args:
#    var_name : out-var that will be populated with the site-packages path
#
function ( _kwiver_python_site_package_dir    var_name)
  # This is run many times and should produce the same result, so we cache it
  if (_prev_python_exe STREQUAL PYTHON_EXECUTABLE)
    set(python_site_packages ${_prev_python_exe})
  else()
    # Only run this if the python exe has changed
    execute_process(
      COMMAND "${PYTHON_EXECUTABLE}" -c "import distutils.sysconfig; print distutils.sysconfig.get_python_lib(prefix='')"
      RESULT_VARIABLE proc_success
      OUTPUT_VARIABLE python_site_packages
    )
    # Returns something like "lib/python2.7/dist-packages"

    if(NOT ${proc_success} EQUAL 0)
      message(FATAL_ERROR "Request for python site-packages location failed with error code: ${proc_success}")
    else()
      string(STRIP "${python_site_packages}" python_site_packages)
    endif()

    # Current usage determines most of the path in alternate ways.
    # All we need to supply is the '*-packages' directory name.
    # Customers could be converted to accept a larger part of the path from this function.
    string( REGEX MATCH "dist-packages" result ${python_site_packages} )
    if (result)
      set( python_site_packages dist-packages)
    else()
      set( python_site_packages site-packages)
    endif()

    # Cache computed value
    set(_prev_site_packages "${python_site_packages}" INTERNAL)
    set(_prev_python_exe "${PYTHON_EXECUTABLE}" INTERNAL)
  endif()

  set(${var_name} ${python_site_packages} PARENT_SCOPE )
endfunction()



###
#
function (kwiver_add_python_library    name    modpath)
  _kwiver_create_safe_modpath("${modpath}" safe_modpath)

  _kwiver_python_site_package_dir( python_site_packages )

  set(library_subdir "/${kwiver_python_subdir}")
  set(library_subdir_suffix "/${python_site_packages}/${modpath}")
  set(component runtime)

  set(no_export ON)
  set(no_export_header ON)

  kwiver_add_library("python-${safe_modpath}-${name}" MODULE
    ${ARGN})

  set(pysuffix "${CMAKE_SHARED_MODULE_SUFFIX}")
  if (WIN32 AND NOT CYTWIN)
    set(pysuffix .pyd)
  endif ()

  set_target_properties("python-${safe_modpath}-${name}"
    PROPERTIES
      OUTPUT_NAME "${name}"
      PREFIX      ""
      SUFFIX      "${pysuffix}"
    )

  add_dependencies(python      "python-${safe_modpath}-${name}")
  set_property(GLOBAL APPEND PROPERTY kwiver_python_modules ${name})

endfunction ()

###
# - internal implementation -
#
function (kwiver_add_python_module_int    path     modpath    module)
  _kwiver_create_safe_modpath("${modpath}" safe_modpath)

  _kwiver_python_site_package_dir( python_site_packages )
  set(python_sitepath /${python_site_packages})

  set(python_arch)
  set(python_noarchdir)

  if (WIN32)
    set(python_install_path lib)
  else ()
    if (python_noarch)
      set(python_noarchdir /noarch)
      set(python_install_path lib)
      set(python_arch u)
    else ()
      set(python_install_path "lib${LIB_SUFFIX}")
    endif ()
  endif ()

  set(pyfile_src "${path}")
  set(pyfile_dst "${kwiver_python_output_path}${python_noarchdir}${python_sitepath}/${modpath}/${module}.py")
  # installation path for this module
  set(pypkg_install_path "${python_install_path}/${kwiver_python_subdir}${python_sitepath}/${modpath}")

  # copy and configure the source file into the binary directory
  if (KWIVER_SYMLINK_PYTHON)
    kwiver_symlink_file("python${python_arch}-${safe_modpath}-${module}"
      "${pyfile_src}"
      "${pyfile_dst}"
      PYTHON_EXECUTABLE)
  else()
    kwiver_configure_file("python${python_arch}-${safe_modpath}-${module}"
      "${pyfile_src}"
      "${pyfile_dst}"
      PYTHON_EXECUTABLE)
  endif()

  # install the configured binary to the kwiver python install path
  kwiver_install(
    FILES       "${pyfile_dst}"
    DESTINATION "${pypkg_install_path}"
    COMPONENT   runtime)

  add_dependencies(python
    "configure-python${python_arch}-${safe_modpath}-${module}")

  if (python_both_arch)
    set(python_both_arch)
    set(python_noarch TRUE)

    if (NOT WIN32)
      # this looks recursive
      kwiver_add_python_module_int(
        "${path}"
        "${modpath}"
        "${module}")
    endif ()
  endif ()
endfunction ()

###
# kwiver_add_python_module
#
#     Installs a pure-Python module into the 'modpath' and puts it into the
#     correct place in the build tree so that it may be used with any built
#     libraries in any build configuration.
#
# \param path Path to the python source
#
# \param modpath Python module path (e.g. kwiver/processes)
#
# \param module Python module name. This is the name used to import the code.
#
function (kwiver_add_python_module   path   modpath   module)
  kwiver_add_python_module_int("${path}"
    "${modpath}"
    "${module}")
endfunction ()

###
#   kwiver_create_python_init(modpath [module ...])
#
#     Creates an __init__.py package file which imports the modules in the
#     arguments for the package.
#
function (kwiver_create_python_init    modpath)
  _kwiver_create_safe_modpath("${modpath}" safe_modpath)

  set(init_template "${CMAKE_CURRENT_BINARY_DIR}/${safe_modpath}.__init__.py")

  if (NOT copyright_header)
    set(copyright_header "# Generated by kwiver")
  endif ()

  file(WRITE "${init_template}"      "${copyright_header}\n\n")

  foreach (module IN LISTS ARGN)
    file(APPEND "${init_template}"      "from ${module} import *\n")
  endforeach ()

  kwiver_add_python_module_int("${init_template}"
    "${modpath}"
    __init__)
endfunction ()

###
#
function (kwiver_create_python_plugin_init modpath)
  _kwiver_create_safe_modpath("${modpath}" safe_modpath)

  set(init_template "${CMAKE_CURRENT_BINARY_DIR}/${safe_modpath}.__init__.py")

  if (NOT copyright_header)
    set(copyright_header "# Generated by kwiver")
  endif ()

  file(WRITE "${init_template}"     "${copyright_header}\n\n")
  file(APPEND "${init_template}"    "from pkgutil import extend_path\n")
  file(APPEND "${init_template}"    "__path__ = extend_path(__path__, __name__)\n")

  kwiver_add_python_module_int("${init_template}"
    "${modpath}"
    __init__)
endfunction ()
