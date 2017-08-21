/*ckwg +29
 * Copyright 2013-2017 by Kitware, Inc.
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

/**
 * \file
 * \brief core feature_set class interface
 *
 * \seealso ../../types/feature_set.h
 * \seealso ../../python/vital/types/feature_set.py
 */

#ifndef VITAL_C_FEATURE_SET_H_
#define VITAL_C_FEATURE_SET_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stddef.h>
#include <stdint.h>

#include <vital/bindings/c/error_handle.h>
#include <vital/bindings/c/vital_c_export.h>
#include <vital/bindings/c/types/feature.h>
#include <vital/bindings/c/types/feature_set.h>


/// Opaque structure for vital::feature_set
typedef struct vital_feature_set_s vital_feature_set_t;

VITAL_C_EXPORT
vital_feature_set_t* vital_feature_set_new_from_list(vital_feature_t const **features, size_t length, vital_error_handle_t *eh);

VITAL_C_EXPORT
vital_feature_set_t* vital_feature_set_new_empty(vital_error_handle_t *eh);

VITAL_C_EXPORT
void vital_feature_set_destroy(vital_feature_set_t *fset, vital_error_handle_t *eh);

VITAL_C_EXPORT
size_t vital_feature_set_size(vital_feature_set_t const *fset, vital_error_handle_t *eh);

VITAL_C_EXPORT
void vital_feature_set_features(vital_feature_set_t const *fset, vital_feature_t ***features, vital_error_handle_t *eh);

VITAL_C_EXPORT
void vital_feature_set_getitems(vital_feature_set_t const *fset, size_t num, size_t *indices, vital_feature_t ***features, vital_error_handle_t *eh);

VITAL_C_EXPORT
void vital_feature_set_getitem(vital_feature_set_t *fset, size_t index, vital_feature_t **feature, vital_error_handle_t *eh);

VITAL_C_EXPORT
void vital_feature_set_delitem(vital_feature_set_t *fset, size_t index, vital_error_handle_t *eh);

VITAL_C_EXPORT
void vital_feature_set_add(vital_feature_set_t *fset, vital_feature_t *item, vital_error_handle_t *eh);

#ifdef __cplusplus
}
#endif

#endif // VITAL_C_FEATURE_SET_H_