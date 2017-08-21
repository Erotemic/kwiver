/*ckwg +29
 * Copyright 2017 by Kitware, Inc.
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
 * \brief Implementation of C interface to vital::feature_set
 *
 * \seealso ../../types/feature_set.h
 */

#include "feature.h"
#include "feature_set.h"

#include <vital/vital_foreach.h>
#include <vital/types/feature.h>
#include <vital/types/feature_set.h>

#include <vital/bindings/c/helpers/c_utils.h>
#include <vital/bindings/c/helpers/feature.h>
#include <vital/bindings/c/helpers/feature_set.h>


namespace kwiver {
namespace vital_c {

SharedPointerCache< vital::feature_set, vital_feature_set_t >
  FEATURE_SET_SPTR_CACHE( "feature_set" );

}
}


using namespace kwiver;


/// Create a new simple feature_set from an array of features
vital_feature_set_t*
vital_feature_set_new_from_list( vital_feature_t const **features,
                                 size_t length,
                                 vital_error_handle_t *eh )
{
  STANDARD_CATCH(
    "vital_feature_set_new", eh,
    vital::feature::vector_t fset_vec;
    vital::feature_sptr f_sptr;
    for( size_t i =0; i < length; ++i )
    {
      f_sptr = vital_c::FEATURE_SPTR_CACHE.get( features[i] );
      fset_vec.push_back(f_sptr);
    }
    auto fset_sptr = std::make_shared< vital::simple_feature_set >( fset_vec );
    vital_c::FEATURE_SET_SPTR_CACHE.store( fset_sptr );
    return reinterpret_cast< vital_feature_set_t* >( fset_sptr.get() );
  );
  return NULL;
}


/// Create a new, empty feature_set
vital_feature_set_t*
vital_feature_set_new_empty( vital_error_handle_t *eh )
{
  STANDARD_CATCH(
    "vital_feature_set_new_empty", eh,
    auto fset_sptr = std::make_shared< vital::simple_feature_set >();
    vital_c::FEATURE_SET_SPTR_CACHE.store( fset_sptr );
    return reinterpret_cast< vital_feature_set_t* >( fset_sptr.get() );
  );
  return NULL;
}


/// Destroy a feature_set instance
void
vital_feature_set_destroy( vital_feature_set_t *fset,
                           vital_error_handle_t *eh)
{
  STANDARD_CATCH(
    "vital_feature_set_destroy", eh,
    vital_c::FEATURE_SET_SPTR_CACHE.erase( fset );
  );
}


/// Get the size of the landmark map
size_t
vital_feature_set_size( vital_feature_set_t const *fset,
                        vital_error_handle_t *eh )
{
  STANDARD_CATCH(
    "vital_feature_set_size", eh,
    size_t s = vital_c::FEATURE_SET_SPTR_CACHE.get( fset )->size();
    return s;
  );
  return -1;
}


/// Get all the features contained in this map
void
vital_feature_set_features( vital_feature_set_t const *fset,
                            vital_feature_t ***features,  //oparam
                            vital_error_handle_t *eh )
{
  STANDARD_CATCH(
    "vital_feature_set_features", eh,
    auto fset_sptr = vital_c::FEATURE_SET_SPTR_CACHE.get( fset );
    auto fset_vec = fset_sptr->features();
    // Initialize array memory for the oparam
    *features = (vital_feature_t**)malloc( sizeof(vital_feature_t*) * fset_vec.size() );

    size_t i = 0;
    VITAL_FOREACH( auto const &item, fset_vec )
    {
      vital_c::FEATURE_SPTR_CACHE.store( item );

      // FIXME
      //(*features)[i] = reinterpret_cast< vital_feature_t* >( item );

      ++i;
    }
  );
}


/// Get some of the features contained in this map
void
vital_feature_set_getitems( vital_feature_set_t const *fset,
                            size_t num,
                            size_t *indices,
                            vital_feature_t ***features,  //oparam
                            vital_error_handle_t *eh )
{
  STANDARD_CATCH(
    "vital_feature_set_getitems", eh,
    auto const fset_sptr = vital_c::FEATURE_SET_SPTR_CACHE.get( fset );
    auto const fset_vec = fset_sptr->features();
    // Initialize array memory for the oparam
    *features = (vital_feature_t**)malloc( sizeof(vital_feature_t*) * num );

    size_t i = 0;
    VITAL_FOREACH( auto const &item, fset_vec )
    {
      vital_c::FEATURE_SPTR_CACHE.store( item );

      // FIXME
      (*features)[i] = reinterpret_cast< vital_feature_t* >( item.get() );

      ++i;
    }
  );
}

/// Get one of the features contained in this map
void
vital_feature_set_getitem( vital_feature_set_t *fset, size_t index,
                           vital_feature_t **feature,  //oparam
                           vital_error_handle_t *eh)
{
  STANDARD_CATCH(
    "vital_feature_set_getitem", eh,
    auto const fset_sptr = vital_c::FEATURE_SET_SPTR_CACHE.get( fset );
    std::vector< vital::feature_sptr > const fset_fvec = fset_sptr->features();
    vital::feature_sptr const item = fset_fvec[index];
    vital_c::FEATURE_SPTR_CACHE.store( item );
    // type(item) = feature_sptr const&
    *feature = reinterpret_cast< vital_feature_t* >( item.get() );
  );
}


// Remove an item from the vector
void
vital_feature_set_delitem( vital_feature_set_t *fset, size_t index,
                           vital_error_handle_t *eh)
{
  STANDARD_CATCH(
    "vital_feature_set_delindex", eh,
    auto fset_sptr = vital_c::FEATURE_SET_SPTR_CACHE.get( fset );
    auto fset_fvec = fset_sptr->features();
    fset_fvec.erase(fset_fvec.begin() + index);
  );
}


void vital_feature_set_add( vital_feature_set_t *fset, vital_feature_t *item,
                            vital_error_handle_t *eh)
{
  STANDARD_CATCH(
    "vital_feature_set_add", eh,
    auto fset_sptr = vital_c::FEATURE_SET_SPTR_CACHE.get( fset );
    auto fset_fvec = fset_sptr->features();
    auto item_sptr = kwiver::vital_c::FEATURE_SPTR_CACHE.get( item );
    size_t tmp = 0;
    tmp ++;
    fset_fvec.push_back( item_sptr );
    );
}
