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

#include "compute_image_descriptor_process.h"

#include <vital/vital_types.h>

#include <vital/types/timestamp.h>
#include <vital/types/timestamp_config.h>
#include <vital/types/image_container.h>
#include <vital/types/object_track_set.h>
#include <vital/types/track_descriptor_set.h>

#include <vital/algo/compute_image_descriptor.h>

#include <kwiver_type_traits.h>

#include <sprokit/pipeline/process_exception.h>

namespace kwiver
{

namespace algo = vital::algo;

create_config_trait( flush_on_last, bool, "true",
  "Flushes descriptors on the last frame of the pipeline, outputing "
  "any remaining descriptors currently in progress" );

//------------------------------------------------------------------------------
// Private implementation class
class compute_image_descriptor_process::priv
{
public:
  priv();
  ~priv();

  bool flush_on_last;
  unsigned detection_offset;

  algo::compute_image_descriptor_sptr m_algo;

  void add_custom_uids( vital::track_descriptor_set_sptr& output,
                        const std::string& frame_id_stamp );
};


// =============================================================================

compute_image_descriptor_process
::compute_image_descriptor_process( vital::config_block_sptr const& config )
  : process( config ),
    d( new compute_image_descriptor_process::priv )
{
  // Attach our logger name to process logger
  attach_logger( vital::get_logger( name() ) );

  // Required so that we can do 1 step past the end of video for flushing
  set_data_checking_level( check_none );

  make_ports();
  make_config();
}


compute_image_descriptor_process
::~compute_image_descriptor_process()
{
}


// -----------------------------------------------------------------------------
void compute_image_descriptor_process
::_configure()
{
  vital::config_block_sptr algo_config = get_config();

  algo::compute_image_descriptor::set_nested_algo_configuration(
    "computer", algo_config, d->m_algo );

  if( !d->m_algo )
  {
    throw sprokit::invalid_configuration_exception(
      name(), "Unable to create compute_image_descriptor" );
  }

  algo::compute_image_descriptor::get_nested_algo_configuration(
    "computer", algo_config, d->m_algo );

  // Check config so it will give run-time diagnostic of config problems
  if( !algo::compute_image_descriptor::check_nested_algo_configuration(
    "computer", algo_config ) )
  {
    throw sprokit::invalid_configuration_exception(
      name(), "Configuration check failed." );
  }
}


// -----------------------------------------------------------------------------
void
compute_image_descriptor_process
::_step()
{
  // Peek at next input to see if we're at end of video
  auto port_info = peek_at_port_using_trait( image );

  if( port_info.datum->type() == sprokit::datum::complete )
  {
    grab_edge_datum_using_trait( image );
    mark_process_as_complete();

    // Push last outputs
    if( d->flush_on_last )
    {
      vital::track_descriptor_set_sptr output;
      output = d->m_algo->flush();
      d->add_custom_uids( output, "final" );
      push_outputs( output );
    }

    const sprokit::datum_t dat = sprokit::datum::complete_datum();

    push_datum_to_port_using_trait( descriptor_set, dat );
    return;
  }

  // Retrieve inputs from ports
  vital::image_container_sptr image;
  image = grab_from_port_using_trait( image );

  if( detections )
  {
    std::vector< vital::track_sptr > det_tracks;

    for( unsigned i = 0; i < detections->size(); ++i )
    {
      vital::track_sptr new_track( vital::track::create() );
      new_track->set_id( i + d->detection_offset );

      vital::track_state_sptr first_track_state(
        new vital::object_track_state( ts.get_frame(), detections->begin()[i] ) );

      new_track->append( first_track_state );

      det_tracks.push_back( new_track );
    }

    vital::object_track_set_sptr det_track_set(
      new vital::object_track_set( det_tracks ) );

    output = d->m_algo->compute_single( image, det_track_set );
    d->detection_offset = d->detection_offset + detections->size();
  }

  // Add custom uids
  d->add_custom_uids( output, std::to_string( ts.get_frame() ) );

  // Return all outputs
  push_outputs( output );

  if( process::count_output_port_edges( "detected_object_set" ) > 0 )
  {
    push_to_port_using_trait( detected_object_set, detections );
  }

}


// -----------------------------------------------------------------------------
void compute_image_descriptor_process
::make_ports()
{
  // Set up for required ports
  sprokit::process::port_flags_t optional;
  sprokit::process::port_flags_t required;

  required.insert( flag_required );

  // -- input --
  declare_input_port_using_trait( timestamp, optional );
  declare_input_port_using_trait( image, required );
  declare_input_port_using_trait( object_track_set, optional );
  declare_input_port_using_trait( detected_object_set, optional );

  // -- output --
  declare_output_port_using_trait( track_descriptor_set, optional );
  declare_output_port_using_trait( descriptor_set, optional );
  declare_output_port_using_trait( string_vector, optional );
  declare_output_port_using_trait( detected_object_set, optional );
}


// -----------------------------------------------------------------------------
void compute_image_descriptor_process
::make_config()
{
  declare_config_using_trait( inject_to_detections );
  declare_config_using_trait( add_custom_uid );
  declare_config_using_trait( uid_basename );
  declare_config_using_trait( flush_on_last );
}


// -----------------------------------------------------------------------------
void compute_image_descriptor_process
::push_outputs( vital::track_descriptor_set_sptr& output )
{
  push_to_port_using_trait( track_descriptor_set, output );

  if( process::count_output_port_edges( "descriptor_set" ) > 0 )
  {
    std::vector< vital::descriptor_sptr > raw_descs;

    for( auto desc : *output )
    {
      raw_descs.push_back( desc->get_descriptor() );
    }

    vital::descriptor_set_sptr dset(
      new vital::simple_descriptor_set( raw_descs ) );

    push_to_port_using_trait( descriptor_set, dset );
  }
}


} // end namespace
