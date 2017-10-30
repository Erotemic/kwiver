/*ckwg +29
 * Copyright 2013-2015 by Kitware, Inc.
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
 * \brief extract_image_descriptor algorithm definition
 */

#ifndef VITAL_ALGO_EXTRACT_IMAGE_DESCRIPTORS_H_
#define VITAL_ALGO_EXTRACT_IMAGE_DESCRIPTORS_H_

#include <vital/vital_config.h>

#include <vital/algo/algorithm.h>
#include <vital/types/image_container.h>
#include <vital/types/descriptor_set.h>
#include <vital/types/image_set.h>
#include <vital/types/descriptor.h>

namespace kwiver {
namespace vital {
namespace algo {

/// An abstract base class for extracting image descriptors
class VITAL_ALGO_EXPORT extract_image_descriptor
  : public kwiver::vital::algorithm_def<extract_image_descriptor>
{
public:

  typedef kwiver::vital::descriptor out_type
  typedef kwiver::vital::descriptor_set_sptr batch_out_type

  /// Return the name of this algorithm
  static std::string static_type_name() { return "extract_image_descriptor"; }

  /// Extract a single descriptor to represent a single image
  /**
   * \param image_data contains the image data to process
   * \returns a single image-level descriptor (e.g. HoG / GIST / CNN features)
   */
  virtual kwiver::vital::descriptor
  compute(kwiver::vital::image_container_sptr image_data) const = 0;

  /// Extract descriptors from multiple images
  /**
   * \param image_data contains the image data to process
   * \returns a set of image-level descriptors
   */
  virtual kwiver::vital::descriptor_set_sptr
  compute_batch(kwiver::vital::image_set_sptr image_data) const = 0;

protected:
  extract_image_descriptor();

};


/// Shared pointer for base extract_image_descriptor algorithm definition class
typedef std::shared_ptr<extract_image_descriptor> extract_image_descriptor_sptr;


} } } // end namespace

#endif // VITAL_ALGO_EXTRACT_IMAGE_DESCRIPTORS_H_
