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

#ifndef KWIVER_VITAL_TYPES_BOUNDING_BOX_H
#define KWIVER_VITAL_TYPES_BOUNDING_BOX_H

#define _USE_MATH_DEFINES
#include <math.h>

#if defined M_PIl
#define LOCAL_PI M_PIl
#else
#define LOCAL_PI M_PI
#endif

#include <cmath>
#include <limits>

#include <vital/types/vector.h>
#include <Eigen/Geometry>
//#include "bounding_box.h"
#include "polygon.h"

namespace kwiver {
namespace vital {

/// forward declaration of landmark class
class oriented_bounding_box;
/// typedef for a landmark shared pointer
typedef std::shared_ptr< oriented_bounding_box > oriented_bounding_box_sptr;

// ----------------------------------------------------------------
/**
 * @brief Oriented bounding box
 *
 * This class represents a rotated bounding box.
 *
 * A bounding box must be constructed with the correct geometry. Once
 * created, the geometry can not be altered.
 */
class oriented_bounding_box
{
public:
  //typedef Eigen::Matrix< double, 2, 1 > vector_type;
  typedef kwiver::vital::vector_2d vector_t;

  /**
   * @brief Equality operator for oriented bounding box
   *
   * @param other The box to check against
   *
   * @return \b true if boxes are identical
   */
  bool operator== ( oriented_bounding_box const& rhs )
  {
    if ( ( this == &rhs ) ||
        ( this->center() == rhs.center()  &&
          this->size() == rhs.size()
        )
       )
    {
      const double angle1 = fmod(this->angle(), (2.0 * LOCAL_PI));
      const double angle2 = fmod(rhs.angle(), (2.0 * LOCAL_PI));
      return fabs(angle1 - angle2) < std::numeric_limits<double>::epsilon();
    }

    return false;
  }

  /**
   * @brief Create oriented bounding box from a center, extent, and angle.
   *
   * @param center Upper left corner of box.
   * @param size Lower right corner of box.
   * @param angle Lower right corner of box.
   */
  oriented_bounding_box( vector_t const& center,
                         vector_t const& size,
                         double const& angle=0 )
    : m_center(center), m_size(size), m_angle(angle)
  { }

  /**
   * @brief Get center coordinate of box.
   *
   * @return Center coordinate of box.
   */
  vector_t center() const { return m_center; }

  /**
   * @brief Get width and height of the box
   *
   * @return angle (in radians), zero degrees points to the right
   */
  vector_t size() const { return m_size; }

  /**
   * @brief Get angle of the box.
   *
   * @return vector containing width and height
   */
  double angle() const { return m_angle; }

  /**
   * @brief Get width of box.
   *
   * @return Width of box.
   */
  double width() const { return m_size[0]; }

  /**
   * @brief Get height of box.
   *
   * @return Height of box.
   */
  double height() const { return m_size[1]; }

  /**
   * @brief Get area of box.
   *
   * @return Area of box.
   */
  double area() const { return m_size[0] * m_size[1]; }

  /**
   * @brief Converts the points on the oriented bounding box into a generic
   * polygon
   *
   * @return the polygon
   */
  kwiver::vital::polygon_sptr to_polygon();


private:

  vector_t m_center;  // rectangle center
  vector_t m_size;  // rectangle width and height
  double m_angle;  // rectangle angle (in radians), zero degrees points to the right
};


// Define for common types.
//typedef oriented_bounding_box< double > oriented_bounding_box_d;
typedef oriented_bounding_box oriented_bounding_box_d;


}
}

#endif /* KWIVER_VITAL_TYPES_BOUNDING_BOX_H */
