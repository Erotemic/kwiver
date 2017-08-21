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
 * \brief Header for \link kwiver::vital::segmentation_image segmentation_image
 *        \endlink class
 */

#ifndef VITAL_SEGMENTATION_IMAGE_H_
#define VITAL_SEGMENTATION_IMAGE_H_

#include <vital/vital_export.h>
#include <vital/vital_config.h>

#include <vector>
#include <memory>

#include <vital/types/image_container.h>
//#include <vital/types/detected_object_type.h>


namespace kwiver {
namespace vital {

/// forward declaration of camera intrinsics class
class segmentation_image;
/// typedef for a camera intrinsics shared pointer
typedef std::shared_ptr< segmentation_image > segmentation_image_sptr;


// ------------------------------------------------------------------
/**
 * @brief Segmentation image class.
 *
 * This class represents a per-pixel segmentation using an image, where each
 * integer represents a different object type.
 */
class VITAL_EXPORT segmentation_image
{
public:

  /// Destructor
  virtual ~segmentation_image() VITAL_DEFAULT_DTOR

  /// Create a clone of this object
  segmentation_image_sptr clone() const;

  /// Access the pixel-wise segmentation labels
  image_container_sptr image() const { return m_label_image_sptr; }

  // Setters
  void set_image(image_container_sptr img) { m_label_image_sptr = img; }


protected:
  /// Image containing pixel segmentations
  image_container_sptr m_label_image_sptr;

  image_container_sptr image() const { return m_label_image_sptr; }

  // TODO: Do we need a mapping from integer labels to string
  // DetectedObjectTypes?
  /*
     typedef byte label_id_t;
     typedef int64_t label_id_t;
     std::map< label_id_t, detected_object_type_sptr >
     std::map< detected_object_type_sptr, label_id_t >
     */
};


} } // end namespace

#endif // VITAL_SEGMENTATION_IMAGE_H_
