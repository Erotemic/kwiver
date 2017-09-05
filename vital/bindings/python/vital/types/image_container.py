"""
ckwg +31
Copyright 2015-2016 by Kitware, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

 * Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

 * Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

 * Neither name of Kitware, Inc. nor the names of any contributors may be used
   to endorse or promote products derived from this software without specific
   prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

==============================================================================

Interface to VITAL image_container class.

"""
# -*- coding: utf-8 -*-

import ctypes

from vital.types import Image
from vital.util import VitalObject
from vital.util import VitalErrorHandle


class ImageContainer (VitalObject):
    """
    vital::image_container interface class

    Example:
        >>> from vital.types.image_container import *
        >>> import numpy as np
        >>> arr = (np.random.rand(7, 5) * 255).astype(np.uint8)
        >>> img_container = ImageContainer.cast(arr)
        >>> img = img_container.get_image()
        >>> arr2 = img.get_numpy_array()
        >>> assert np.all(arr2 == arr)
    """

    def __init__(self, image=None, from_cptr=None):
        """
        Create a simple image container from a Image instance

        :param image: Image to contain
        :type image: vital.types.Image

        """
        super(ImageContainer, self).__init__(from_cptr, image)

    @classmethod
    def cast(cls, data):
        if data is None or isinstance(data, cls):
            return super(ImageContainer, cls).cast(data)
        # See if the data was a raw image
        image = Image.cast(data)
        return ImageContainer(image=image)

    def _new(self, image):
        """
        :param image: Image to contain
        :type image: vital.types.Imagimge
        """
        if image is None:
            raise ValueError("No vital.types.Image given to contain.")

        imgc_new = self.VITAL_LIB.vital_image_container_new_simple
        imgc_new.argtypes = [Image.C_TYPE_PTR]
        imgc_new.restype = self.C_TYPE_PTR
        return imgc_new(image.c_pointer)

    def _destroy(self):
        imgc_del = self.VITAL_LIB.vital_image_container_destroy
        imgc_del.argtypes = [self.C_TYPE_PTR, VitalErrorHandle.C_TYPE_PTR]
        with VitalErrorHandle() as eh:
            imgc_del(self, eh)

    def size(self):
        """
        Get the size in bytes of this image container

        Size includes all allocated image memory, which could be larger than
        the product of width, height and depth.

        :return: Size in bytes
        :rtype: long

        """
        ic_size = self.VITAL_LIB.vital_image_container_size
        ic_size.argtypes = [self.C_TYPE_PTR]
        ic_size.restype = ctypes.c_size_t
        return ic_size(self)

    def width(self):
        """
        :return: The pixel width of the image
        :rtype: long
        """
        ic_width = self.VITAL_LIB.vital_image_container_width
        ic_width.argtypes = [self.C_TYPE_PTR]
        ic_width.restype = ctypes.c_size_t
        return ic_width(self)

    def height(self):
        """
        :return: The pixel height of the image
        :rtype: long
        """
        ic_height = self.VITAL_LIB.vital_image_container_height
        ic_height.argtypes = [self.C_TYPE_PTR]
        ic_height.restype = ctypes.c_size_t
        return ic_height(self)

    def depth(self):
        """
        :return: The depth (number of channels) of the image
        :rtype: long
        """
        ic_depth = self.VITAL_LIB.vital_image_container_depth
        ic_depth.argtypes = [self.C_TYPE_PTR]
        ic_depth.restype = ctypes.c_size_t
        return ic_depth(self)

    def get_image(self):
        """
        Return a new pointer the to contained image. This instance shares the
        same internal memory as the contained image.

        :return: New ImageContainer instance
        :rtype: ImageContainer

        """
        ic_getimg = self.VITAL_LIB['vital_image_container_get_image']
        ic_getimg.argtypes = [self.C_TYPE_PTR]
        ic_getimg.restype = Image.C_TYPE_PTR
        img_ptr = ic_getimg(self)
        if bool(img_ptr) is False:
            return None
        return Image(from_cptr=img_ptr)

    def asarray(self):
        """
        Return a new pointer the to contained image. This instance shares the
        same internal memory as the contained image.

        :return: New ImageContainer instance
        :rtype: ImageContainer

        """
        img = self.get_image()
        if img is None:
            return None
        else:
            return img.get_numpy_array()
