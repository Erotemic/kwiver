/*ckwg +29
 * Copyright 2016-2017 by Kitware, Inc.
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
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
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


#include "oriented_bounding_box.h"

namespace kwiver {
namespace vital {

kwiver::vital::polygon_sptr oriented_bounding_box::to_polygon()
{
  using std::cos;
  using std::sin;

  const double cx = m_center[0];
  const double cy = m_center[1];

  const double sin_ = sin(m_angle);
  const double cos_ = cos(m_angle);

  // Assume the bbox is centered at the origin, then the upper right corner
  // is at pt=[w / 2, h / 2]. To transform this into the rotated coordinate
  // frame we perform a rotation by R(theta), and a translation by T(cx, cy)
  // The final point is T.dot(R.dot(pt)), which simplifies to the following:
  // [cx + pt.x * cos - pt_y * sin, cy + pt_x * sin + pt_y * cos]

  // Substituting the appropriately signed half width and height we get
  // [cx - h * sin_ / 2 + w * cos_ / 2,  cy + h * cos_ / 2 + w * sin_ / 2]
  // [cx - h * sin_ / 2 - w * cos_ / 2,  cy + h * cos_ / 2 - w * sin_ / 2]
  // [cx + h * sin_ / 2 - w * cos_ / 2,  cy - h * cos_ / 2 - w * sin_ / 2]
  // [cx + h * sin_ / 2 + w * cos_ / 2,  cy - h * cos_ / 2 + w * sin_ / 2]

  const double half_w = m_size[0] / 2;
  const double half_h = m_size[1] / 2;

  // 4 combinations of [w, h] x [sin, cos]
  const double wc = half_w * cos_;
  const double ws = half_w * sin_;
  const double hc = half_h * cos_;
  const double hs = half_h * sin_;

  std::vector< kwiver::vital::polygon::point_t > points = {
    kwiver::vital::polygon::point_t( cx + wc - hs,  cy + ws + hc ),
    kwiver::vital::polygon::point_t( cx - wc - hs,  cy - ws + hc ),
    kwiver::vital::polygon::point_t( cx - wc + hs,  cy - ws - hc ),
    kwiver::vital::polygon::point_t( cx + wc + hs,  cy + ws - hc ),
  };

  kwiver::vital::polygon_sptr polygon = std::make_shared< kwiver::vital::polygon >(points);
  //kwiver::vital::polygon_sptr polygon = std::make_shared< kwiver::vital::polygon >();
  return polygon;

}

} }
