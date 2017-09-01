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

#include <string>
#include <sstream>
#include <exception>

#include <kwiversys/SystemTools.hxx>
#include <opencv2/imgproc/types_c.h>
#include "caffe_segnet_segmentor.h"

#include "opencv2/core/core.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include "arrows/ocv/image_container.h"

#include "caffe/blob.hpp"
#include "caffe/net.hpp"
#include "caffe/common.hpp"
using namespace caffe;


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

  void configure(const std::string& layer_file, const std::string& weight_file);

  cv::Mat segment(const cv::Mat& img);

  std::unique_ptr<Net<float>> m_cnn;
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
{

}


// --------------------------------------------------------------------
vital::config_block_sptr
caffe_segnet_segmentor::
get_configuration() const
{
  // Get base config from base class
  vital::config_block_sptr config = vital::algorithm::get_configuration();

  std::string weight_file;
  std::string layer_file;
  config->set_value( "weight_file", weight_file, "Name of weight file." );
  config->set_value( "layer_file", layer_file, "Name of layer file." );

  return config;
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

  std::string layer_file = config->get_value< std::string >( "layer_file" );
  if( layer_file.empty() )
  {
    std::stringstream str;
    config->print( str );
    LOG_ERROR( logger(), "Required model file not specified. "
        "Configuration is as follows:\n" << str.str() );
    success = false;
  }
  else if( ! kwiversys::SystemTools::FileExists( layer_file ) )
  {
    LOG_ERROR( logger(), "model file \"" << layer_file << "\" not found." );
    success = false;
  }

  return success;
}

// --------------------------------------------------------------------
void
caffe_segnet_segmentor::
set_configuration( vital::config_block_sptr config_in )
{
  vital::config_block_sptr config = this->get_configuration();

  config->merge_config( config_in );
  d->configure(config->get_value<std::string>("layer_file"), config->get_value<std::string>("weight_file"));
}

// --------------------------------------------------------------------
vital::image_container_sptr
caffe_segnet_segmentor::
segment( vital::image_container_sptr image_data) const
{
  cv::Mat input_image = kwiver::arrows::ocv::image_container::vital_to_ocv(image_data->get_image());
  cv::Mat output_image = d->segment( input_image );
  return vital::image_container_sptr(new kwiver::arrows::ocv::image_container(output_image));
}

// --------------------------------------------------------------------
void caffe_segnet_segmentor::priv::configure(const std::string &layer_file, const std::string &weight_file)
{
  Caffe::set_mode(Caffe::GPU);
  m_cnn.reset(new Net<float>(layer_file, TEST));
  m_cnn->CopyTrainedLayersFrom(weight_file);
}

// --------------------------------------------------------------------
cv::Mat caffe_segnet_segmentor::priv::segment(const cv::Mat &img)
{
  std::vector<cv::Mat>       channels;
  Blob<float>* input_layer = m_cnn->input_blobs()[0];
  cv::Size input_geometry  = cv::Size(input_layer->width(), input_layer->height());

  std::cout << "Network inputs " << m_cnn->num_inputs() << std::endl;
  std::cout << "Network outputs " << m_cnn->num_outputs() << std::endl;

  input_layer->Reshape(1, input_layer->channels(), input_geometry.height, input_geometry.width);
  m_cnn->Reshape();// Let the network know about dimensions

  // Wrap the input layer of the network in seperate cv::Mat objects (one per channel)
  // This way we save one memcpy operation and we dont need to rely on cudaMemcpy2D
  // The last preprocessing operation will write the seperate channels directly to the input layer
  float* input_data = input_layer->mutable_cpu_data();
  for(int i=0; i<input_layer->channels();++i)
  {
    cv::Mat channel(input_geometry.height,input_geometry.width, CV_32FC1,input_data);
    channels.push_back(channel);
    input_data += input_geometry.width*input_geometry.height;
  }

  // Convert the input image to the input image format of the network
  cv::Mat sample;
  if(img.channels()==3 && channels.size()==1)
    cv::cvtColor(img,sample,cv::COLOR_BGR2GRAY);
  else if(img.channels()==4 && channels.size()==1)
    cv::cvtColor(img,sample,cv::COLOR_BGRA2GRAY);
  else if(img.channels()==4 && channels.size()==3)
    cv::cvtColor(img,sample,cv::COLOR_BGRA2BGR);
  else if(img.channels()==1 && channels.size()==3)
    cv::cvtColor(img,sample,cv::COLOR_GRAY2BGR);
  else
    sample = img;

  // Resize the image if necessary
  cv::Mat sample_resized;
  if(sample.size() != input_geometry)
    cv::resize(sample, sample_resized, input_geometry);
  else
    sample_resized = sample;

  cv::Mat sample_float;
  if(channels.size() == 3)
    sample_resized.convertTo(sample_float,CV_32FC3);
  else
    sample_resized.convertTo(sample_float,CV_32FC1);

  // spBlit the separate BGR planes into to the channels
  // Those channels use the memory blocks from the input_layer
  cv::split(sample_float, channels);

  std::cout << "Input image address " << reinterpret_cast<float*>(channels[0].data) << std::endl;
  std::cout << "Input layer address " << m_cnn->input_blobs()[0]->cpu_data() << std::endl;

  std::cout << "Input num " << input_layer->num() << std::endl;
  std::cout << "Input channels " << input_layer->channels() << std::endl;
  std::cout << "Input height " << input_layer->height() << std::endl;
  std::cout << "Input width " << input_layer->width() << std::endl;

  m_cnn->Forward();

  // Pull the image out and back into ocv
  Blob<float>* output_layer = m_cnn->output_blobs()[0];
  std::cout << "Output num " << output_layer->num() << std::endl;
  std::cout << "Output channels " << output_layer->channels() << std::endl;
  std::cout << "Output height " << output_layer->height() << std::endl;
  std::cout << "Output width " << output_layer->width() << std::endl;
  cv::Mat merged_output_image = cv::Mat(output_layer->height(),
                                        output_layer->width(),
                                        CV_32F,
                                        const_cast<float*>(output_layer->cpu_data()));
  merged_output_image.convertTo(merged_output_image,CV_8U);
  cv::cvtColor(merged_output_image.clone(), merged_output_image, CV_GRAY2BGR);
  // cv::Mat label_colors = cv::imread(LUT_file,1);
  // cv::Mat output_image;
  // LUT(merged_output_image, label_colors, output_image);

  return merged_output_image;
}



} } } // end namespace
