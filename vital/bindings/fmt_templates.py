import datetime
import ubelt as ub

COPYRIGHT = ub.codeblock(
    '''
    /*ckwg +29
     * Copyright 2013-{year} by Kitware, Inc.
     * All rights reserved.
     *
     * Redistribution and use in source and binary forms, with or without
     * modification, are permitted provided that the following conditions are met:
     *
     *  * Redistributions of source code must retain the above copyright notice,
     *    this list of conditions and the following disclaimer.
     *
     *  * Redistributions in binary form must reproduce the above copyright notice,
     *    this list of conditions and the following disclaimer in the documentation
     *    and/or other materials provided with the distribution.
     *
     *  * Neither name of Kitware, Inc. nor the names of any contributors may be used
     *    to endorse or promote products derived from this software without specific
     *    prior written permission.
     *
     * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
     * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
     * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
     * ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
     * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
     * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
     * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
     * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
     * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
     * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
     */
    '''
).format(year=datetime.datetime.now().year)


VITAL_C_BINDING_H_FILE = ub.codeblock(
    r'''
    {copyright}

    /**
     * \file
     * \brief core {classname} class interface
     *
     * \seealso ../../types/{classname}.h
     * \seealso ../../python/vital/types/{classname}.py
     */

    #ifndef VITAL_C_{CXX_CLASSNAME}_H_
    #define VITAL_C_{CXX_CLASSNAME}_H_

    #ifdef __cplusplus
    extern "C"
    {{
    #endif

    #include <stddef.h>
    #include <stdint.h>

    #include <vital/bindings/c/error_handle.h>
    #include <vital/bindings/c/vital_c_export.h>
    {vital_type_include_block}


    /// Opaque structure for vital::{classname}
    typedef struct vital_{classname}_s vital_{classname}_t;

    {method_block}

    #ifdef __cplusplus
    }}
    #endif

    #endif // VITAL_C_{CXX_CLASSNAME}_H_
    ''')


VITAL_C_BINDING_HXX_FILE = ub.codeblock(
    r'''
    {copyright}


    /**
     * \file
     * \brief C/C++ interface to kwiver::vital::{cxx_classname} class
     */

    #ifndef VITAL_C_{CXX_CLASSNAME}_HXX_
    #define VITAL_C_{CXX_CLASSNAME}_HXX_

    #include <vital/bindings/c/vital_c_export.h>
    #include <vital/bindings/c/types/{cxx_classname}.h>
    #include <vital/types/{cxx_classname}.h>


    // -----------------------------------------------------------------------------
    // These two functions are a bridge between C++ and the internal C smart pointer
    // management.
    // -----------------------------------------------------------------------------


    /// Create a {c_type} around an existing shared pointer.
    /**
     * If an error occurs, a NULL pointer is returned.
     *
     * \param sptr Shared pointer to a kwiver::vital::{cxx_classname} instance.
     * \param eh Vital error handle instance. May be null to ignore errors.
     */
    VITAL_C_EXPORT
    {c_type}
    vital_{cxx_classname}_from_sptr( {sptr_type} sptr, vital_error_handle_t* eh );


    /// Get the kwiver::vital::{cxx_classname} shared pointer for a handle.
    /**
     * If an error occurs, an empty shared pointer is returned.
     *
     * \param self Vital C handle to the {cxx_classname} instance to get the shared
     *   pointer reference of.
     * \param eh Vital error handle instance. May be null to ignore errors.
     */
    VITAL_C_EXPORT
    {sptr_type}
    vital_{cxx_classname}_to_sptr( {c_type} self, vital_error_handle_t* eh );


    #endif // VITAL_C_{CXX_CLASSNAME}_HXX_
    ''')


VITAL_BINDING_FROM_SPTR_CONVERSION = ub.codeblock(
    r'''
    /// Adopt existing sptr
    {c_type}
    vital_{cxx_classname}_from_sptr( {sptr_type} sptr, vital_error_handle_t* eh=NULL)
    {{
      STANDARD_CATCH(
        "vital_{cxx_classname}_from_sptr", eh,

        {SPTR_CACHE}.store( sptr );
        return reinterpret_cast<{c_type}>( sptr.get() );
      );
      return NULL;
    }}
    ''')

VITAL_BINDING_TO_SPTR_CONVERSION = ub.codeblock(
    r'''
    /// Get the kwiver::vital::{cxx_classname} shared pointer for a handle.
    {sptr_type}
    vital_{cxx_classname}_to_sptr( {c_type} self, vital_error_handle_t* eh )
    {{
      STANDARD_CATCH(
        "vital_{cxx_classname}_to_sptr", eh,
        // Return the cached shared pointer.
        return {SPTR_CACHE}.get( self );
      );
      return {sptr_type}();
    }}
    ''')
