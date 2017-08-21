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

#include "segnet_segmentation.h"

#include <string>
#include <sstream>
#include <exception>


namespace kwiver {
namespace arrows {
namespace segnet {

// ==================================================================
class segnet_segmentation::priv
{
public:
  priv()
    : m_config( "" )
  {}

  ~priv()
  {
  }

  // Items from the config
  std::string m_config;

  kwiver::vital::logger_handle_t m_logger;
};


// ==================================================================
segnet_segmentation::
segnet_segmentation()
  : d( new priv() )
{

}


segnet_segmentation::
~segnet_segmentation()
{}


// --------------------------------------------------------------------
vital::config_block_sptr
segnet_segmentation::
get_configuration() const
{
  // Get base config from base class
  vital::config_block_sptr config = vital::algorithm::get_configuration();

  config->set_value( "config", d->m_config,
    "Name of config file." );

  return config;
}


// --------------------------------------------------------------------
void
segnet_segmentation::
set_configuration( vital::config_block_sptr config_in )
{
  // TODO: What configs do we need?
  vital::config_block_sptr config = this->get_configuration();

  config->merge_config( config_in );

  this->d->m_config = config->get_value< std::string >( "config" );
}


// --------------------------------------------------------------------
bool
segnet_segmentation::
check_configuration( vital::config_block_sptr config ) const
{
  std::string config_fn = config->get_value< std::string >( "config" );

  if( config_fn.empty() )
  {
    return false;
  }

  return true;
}


// --------------------------------------------------------------------
kwiver::vital::image_container_sptr  // TODO Is this the right output type?
segnet_segmentation::
compute( kwiver::vital::image_container_sptr image_data)
{

  return kwiver::vital::image_container_sptr();
}


} } } // end namespace
