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

#include "caffe_segnet_segmentor.h"

#include <string>
#include <sstream>
#include <exception>

#include <kwiversys/SystemTools.hxx>


namespace kwiver {
namespace arrows {
namespace caffe  {

// ==================================================================
class caffe_segnet_segmentor::priv
{
public:
  priv()
  {}

  ~priv()
  {
  }

  // Items from the config
  std::string m_weight_file;

  kwiver::vital::logger_handle_t m_logger;
};


// ==================================================================
caffe_segnet_segmentor::
caffe_segnet_segmentor()
  : d( new priv() )
{

}


caffe_segnet_segmentor::
~caffe_segnet_segmentor()
{}


// --------------------------------------------------------------------
vital::config_block_sptr
caffe_segnet_segmentor::
get_configuration() const
{
  // Get base config from base class
  vital::config_block_sptr config = vital::algorithm::get_configuration();

  config->set_value( "weight_file", d->m_weight_file, "Name of optional weight file." );

  return config;
}


// --------------------------------------------------------------------
void
caffe_segnet_segmentor::
set_configuration( vital::config_block_sptr config_in )
{
  vital::config_block_sptr config = this->get_configuration();

  config->merge_config( config_in );

  this->d->m_weight_file = config->get_value< std::string >( "weight_file" );
  if(!d->m_weight_file.empty() )
  {
    //load_weights( &d->m_net, const_cast< char* >( d->m_weight_file.c_str() ) );
  }
}


// --------------------------------------------------------------------
bool
caffe_segnet_segmentor::
check_configuration( vital::config_block_sptr config ) const
{
  bool success( true );

  std::string weight_file = config->get_value< std::string >( "weight_file" );
  if( weight_file.empty() )
  {
    std::stringstream str;
    config->print( str );
    LOG_ERROR( logger(), "Required weight file not specified. "
      "Configuration is as follows:\n" << str.str() );
    success = false;
  }
  else if( ! kwiversys::SystemTools::FileExists( weight_file ) )
  {
    LOG_ERROR( logger(), "weight file \"" << weight_file << "\" not found." );
    success = false;
  }

  return success;
}


// --------------------------------------------------------------------
vital::image_container_sptr
caffe_segnet_segmentor::
segment( vital::image_container_sptr image_data) const
{

  // vital::image_container_sptr output = image_data->();

  return image_data;
}


} } } // end namespace
