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


#include <vital/types/image_container_set.h>
#include <arrows/ocv/image_container.h>

#include <gtest/gtest.h>

namespace kv = kwiver::vital;
namespace kao = kwiver::arrows::ocv;

// ----------------------------------------------------------------------------
int
main(int argc, char* argv[])
{
  ::testing::InitGoogleTest( &argc, argv );
  return RUN_ALL_TESTS();
}


// ----------------------------------------------------------------------------
TEST(image_container_set, empty)
{
  const auto empty_set
          = std::make_shared<kwiver::vital::simple_image_container_set>();

  // Check size is reported as zero
  EXPECT_EQ(0, empty_set->size()) << "Set empty";

  // Check underlying vector implementation exists and also reports zero size
  EXPECT_EQ(0, empty_set->images().size()) << "Vector empty";
}

TEST(image_container_set, iterators)
{
  const std::vector<int> sizes{{100, 200, 300}};
  std::vector< kv::image_container_sptr > vic;
  for (auto sz : sizes)
  {
    auto imgc = std::make_shared<kao::image_container>( kv::image(sz,sz,3) );
    vic.push_back(imgc);
  }
  const auto sics = std::make_shared<kv::simple_image_container_set>(vic);

  EXPECT_EQ(sizes.size(), sics->size()) << "Set contains three images";

  const size_t new_size{500};
  auto imgc = std::make_shared<kao::image_container>(
          kv::image(new_size,new_size,3) );

  const auto itce = sics->cend();
  int ct = 0;
  for (auto it = sics->cbegin(); it != itce; ++it)
  {
    EXPECT_EQ(sizes.at(ct++), (*it)->height()) << "Image height read correctly";
  }
  EXPECT_EQ(sizes.size(), ct)
                << "Const iterator iterates through three elements";

  const auto ite = sics->end();
  for (auto it = sics->begin(); it != ite; ++it)
  {
    *it = imgc;
  }
  EXPECT_EQ(sizes.size(), sics->end() - sics->begin())
                << "Non-const iterator iterates through three elements";

  EXPECT_EQ((*sics->cbegin())->height(), new_size)
                << "New size written to image";
}