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
 * \brief Header for OCV crop_chips algorithm
 */

#ifndef KWIVER_ARROWS_OCV_CROP_CHIPS_H_
#define KWIVER_ARROWS_OCV_CROP_CHIPS_H_


#include <vital/vital_config.h>
#include <arrows/ocv/kwiver_algo_ocv_export.h>

#include <vital/algo/crop_chips.h>

#include <memory>

namespace kwiver {
namespace arrows {
namespace ocv {

/// A class for writing out image chips around detections, useful as a debugging process
/// for ensuring that the refine detections process is running on desired ROIs.
class KWIVER_ALGO_OCV_EXPORT crop_chips
: public vital::algorithm_impl<crop_chips, vital::algo::crop_chips>
{
public:

  /// Constructor
  crop_chips();

  /// Destructor
  virtual ~crop_chips();

  /// Split image
  virtual kwiver::vital::image_container_set_sptr
      crop(kwiver::vital::image_container_sptr const img,
           std::vector<kwiver::vital::bounding_box_d> const& bboxes) const;
};

} // end namespace ocv
} // end namespace arrows
} // end namespace kwiver

#endif // KWIVER_ARROWS_OCV_CROP_CHIPS_H_