/*ckwg +29
 * Copyright 2016 by Kitware, Inc.
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
 * \brief OCV HOG descriptor extractor wrapper implementation
 */

#include "extract_descriptors_HOG.h"

#ifdef KWIVER_HAS_OPENCV_VER_3

#include <opencv2/objdetect.hpp>

using namespace kwiver::vital;

namespace kwiver {
namespace arrows {
namespace ocv {


  HOGDescriptor::DEFAULT_WIN_SIGMA
  HOGDescriptor::DEFAULT_NLEVELS
  HOGDescriptor::DESCR_FORMAT_ROW_BY_ROW
  HOGDescriptor::DESCR_FORMAT_COL_BY_COL

    enum { DEFAULT_WIN_SIGMA = -1 };
    enum { DEFAULT_NLEVELS = 64 };
    enum { DESCR_FORMAT_ROW_BY_ROW, DESCR_FORMAT_COL_BY_COL };




namespace {

std::string list_norm_options()
{
  std::stringstream ss;
  ss << "\tNRM_NONE    = " << cv::xfeatures2d::HOG::NRM_NONE << "\n"
     << "\tNRM_PARTIAL = " << cv::xfeatures2d::HOG::NRM_PARTIAL << "\n"
     << "\tNRM_FULL    = " << cv::xfeatures2d::HOG::NRM_FULL << "\n"
     << "\tNRM_SIFT    = " << cv::xfeatures2d::HOG::NRM_SIFT;
  return ss.str();
}

bool check_norm_type( int norm )
{
  switch( norm )
  {
    case cv::xfeatures2d::HOG::NRM_NONE:
    case cv::xfeatures2d::HOG::NRM_PARTIAL:
    case cv::xfeatures2d::HOG::NRM_FULL:
    case cv::xfeatures2d::HOG::NRM_SIFT:
      return true;
    default:
      return false;
  }
}

} //end namespace anonymous


class extract_descriptors_HOG::priv
{
public:
  priv()
    : win_width( 64 )
    : win_height( 128 )
  {
  }

  cv::Ptr<cv::HOGDescriptor> create() const
  {
    return cv::HOGDescriptor::create( cv::Size(win_width, win_height) );
  }

  void update_config( config_block_sptr config ) const
  {

    // https://docs.opencv.org/3.1.0/d5/d33/structcv_1_1HOGDescriptor.html

    //HOGDescriptor(Size win_size=Size(64, 128), Size block_size=Size(16, 16),
    //              Size block_stride=Size(8, 8), Size cell_size=Size(8, 8),
    //              int nbins=9, double win_sigma=DEFAULT_WIN_SIGMA,
    //              double threshold_L2hys=0.2, bool gamma_correction=true,
    //              int nlevels=DEFAULT_NLEVELS);

    config->set_value( "win_width", win_width, "sliding window width" );
    config->set_value( "win_height", win_height, "sliding window height" );
  }

  void set_config( config_block_sptr config )
  {
    win_width = config->get_value<int>( "win_width" );
    win_height = config->get_value<int>( "win_height" );
  }

  bool check_config( config_block_sptr config, logger_handle_t const &log ) const
  {
    return true;
  }

  // Parameters
  int win_width;
  int win_height;
};


extract_descriptors_HOG
::extract_descriptors_HOG()
  : p_( new priv )
{
  attach_logger( "arrows.ocv.HOG" );
  extractor = p_->create();
}


extract_descriptors_HOG
::~extract_descriptors_HOG()
{
}

vital::config_block_sptr
extract_descriptors_HOG
::get_configuration() const
{
  config_block_sptr config = ocv::extract_descriptors::get_configuration();
  p_->update_config( config );
  return config;
}


void extract_descriptors_HOG
::set_configuration(vital::config_block_sptr config)
{
  config_block_sptr c = get_configuration();
  c->merge_config( config );
  p_->set_config( c );
  extractor = p_->create();
}


bool
extract_descriptors_HOG
::check_configuration(vital::config_block_sptr config) const
{
  config_block_sptr c = get_configuration();
  c->merge_config( config );
  return p_->check_config( c, logger() );
}


} // end namespace ocv
} // end namespace arrows
} // end namespace kwiver

#endif //KWIVER_HAS_OPENCV_VER_3
