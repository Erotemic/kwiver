"""
ckwg +31
Copyright 2017 by Kitware, Inc.
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

Interface to VITAL detected_object class.

"""
import ctypes

from vital.util import VitalObject
from vital.util import VITAL_LIB
from vital.util import VitalErrorHandle

from vital.types import BoundingBox
from vital.types import DetectedObjectType
from vital.types import ImageContainer
from vital.types.mixins import NiceRepr


def define_detected_object_c_api():
    """

    CommandLine:
        python -m c_introspect VitalTypeIntrospectCBind.dump_python_ctypes:0 --class=detected_object
    """
    class detected_object_c_api(object):
        pass
    C = detected_object_c_api()
    C.new_with_bbox = VITAL_LIB.vital_detected_object_new_with_bbox
    C.new_with_bbox.argtypes = [BoundingBox.C_TYPE_PTR, ctypes.c_double, DetectedObjectType.C_TYPE_PTR]
    C.new_with_bbox.restype = DetectedObject.C_TYPE_PTR

    C.copy = VITAL_LIB.vital_detected_object_copy
    C.copy.argtypes = [DetectedObject.C_TYPE_PTR]
    C.copy.restype = DetectedObject.C_TYPE_PTR

    C.destroy = VITAL_LIB.vital_detected_object_destroy
    C.destroy.argtypes = [DetectedObject.C_TYPE_PTR]
    C.destroy.restype = None

    C.bounding_box = VITAL_LIB.vital_detected_object_bounding_box
    C.bounding_box.argtypes = [DetectedObject.C_TYPE_PTR]
    C.bounding_box.restype = BoundingBox.C_TYPE_PTR

    C.set_bounding_box = VITAL_LIB.vital_detected_object_set_bounding_box
    C.set_bounding_box.argtypes = [DetectedObject.C_TYPE_PTR, BoundingBox.C_TYPE_PTR]
    C.set_bounding_box.restype = None

    C.confidence = VITAL_LIB.vital_detected_object_confidence
    C.confidence.argtypes = [DetectedObject.C_TYPE_PTR]
    C.confidence.restype = ctypes.c_double

    C.set_confidence = VITAL_LIB.vital_detected_object_set_confidence
    C.set_confidence.argtypes = [DetectedObject.C_TYPE_PTR, ctypes.c_double]
    C.set_confidence.restype = None

    C.get_type = VITAL_LIB.vital_detected_object_get_type
    C.get_type.argtypes = [DetectedObject.C_TYPE_PTR]
    C.get_type.restype = DetectedObjectType.C_TYPE_PTR

    C.set_type = VITAL_LIB.vital_detected_object_set_type
    C.set_type.argtypes = [DetectedObject.C_TYPE_PTR, DetectedObjectType.C_TYPE_PTR]
    C.set_type.restype = None

    C.index = VITAL_LIB.vital_detected_object_index
    C.index.argtypes = [DetectedObject.C_TYPE_PTR]
    C.index.restype = ctypes.c_int64

    C.set_index = VITAL_LIB.vital_detected_object_set_index
    C.set_index.argtypes = [DetectedObject.C_TYPE_PTR, ctypes.c_int64]
    C.set_index.restype = None

    C.detector_name = VITAL_LIB.vital_detected_object_detector_name
    C.detector_name.argtypes = [DetectedObject.C_TYPE_PTR]
    C.detector_name.restype = ctypes.POINTER(ctypes.c_char)

    C.detector_set_name = VITAL_LIB.vital_detected_object_detector_set_name
    C.detector_set_name.argtypes = [DetectedObject.C_TYPE_PTR, ctypes.POINTER(ctypes.c_char)]
    C.detector_set_name.restype = None

    C.mask = VITAL_LIB.vital_detected_object_mask
    C.mask.argtypes = [DetectedObject.C_TYPE_PTR, VitalErrorHandle.C_TYPE_PTR]
    C.mask.restype = ImageContainer.C_TYPE_PTR

    C.set_mask = VITAL_LIB.vital_detected_object_set_mask
    C.set_mask.argtypes = [DetectedObject.C_TYPE_PTR, ImageContainer.C_TYPE_PTR, VitalErrorHandle.C_TYPE_PTR]
    C.set_mask.restype = None
    return C


class DetectedObject (VitalObject, NiceRepr):
    """
    vital::detected_object interface class

    SeeAlso:
        ../../../c/types/detected_object.h
        ../../types/detected_object.h

    TODO:
        add mask getter / setter
    """
    C = define_detected_object_c_api()

    def __init__(self, bbox=None, confid=0.0, tot=None, from_cptr=None):
        """
        Create a simple detected object type

        Args:
            bbox (BoundingBox or list): if given as a list, args are used
                to create a new BoundingBox instance.
            confid (float): numeric confidence
            tot (DetectedObjectType): detected object type
        """
        bbox = BoundingBox.cast(bbox)
        super(DetectedObject, self).__init__(from_cptr, bbox, confid, tot)

    def _new(self, bbox, confid, tot):
        do_new = self.VITAL_LIB.vital_detected_object_new_with_bbox
        do_new.argtypes = [BoundingBox.C_TYPE_PTR, ctypes.c_double, DetectedObjectType.C_TYPE_PTR]
        do_new.restype = self.C_TYPE_PTR
        if bbox is None:
            raise ValueError('c-bindings will segfault if passed a bbox of None')
        return do_new(bbox, ctypes.c_double( confid ), tot)

    def _destroy(self):
        do_del = self.VITAL_LIB.vital_detected_object_destroy
        do_del.argtypes = [self.C_TYPE_PTR]
        do_del(self)

    def bounding_box(self):
        # Get C pointer to internal bounding box
        do_get_bb = self.VITAL_LIB.vital_detected_object_bounding_box
        do_get_bb.argtypes = [self.C_TYPE_PTR]
        do_get_bb.restype = BoundingBox.C_TYPE_PTR
        bb_c_ptr = do_get_bb(self)
        # Make copy of bounding box to return
        do_bb_cpy = self.VITAL_LIB.vital_bounding_box_copy
        do_bb_cpy.argtypes = [BoundingBox.C_TYPE_PTR]
        do_bb_cpy.restype = BoundingBox.C_TYPE_PTR
        return BoundingBox( from_cptr=do_bb_cpy( bb_c_ptr ) )

    def set_bounding_box(self, bbox):
        """
        Args:
            bbox (BoundingBox or list): if given as a list, args are used
                to create a new BoundingBox instance.
        """
        do_sbb = self.VITAL_LIB.vital_detected_object_set_bounding_box
        do_sbb.argtypes = [self.C_TYPE_PTR, BoundingBox.C_TYPE_PTR]
        return do_sbb(self, bbox)

    def confidence(self):
        """
        Example:
            >>> from vital.types import DetectedObject
            >>> from vital.types import DetectedObjectType
            >>> self = DetectedObject([0, 0, 1, 1])
            >>> conf1 = self.confidence()
            >>> self.set_confidence(2.0)
            >>> conf2 = self.confidence()
            >>> assert conf1 == 0
            >>> assert conf2 == 2
        """
        do_conf = self.VITAL_LIB.vital_detected_object_confidence
        do_conf.argtypes = [self.C_TYPE_PTR]
        do_conf.restype = ctypes.c_double
        return do_conf(self)

    def set_confidence(self, confid):
        do_sc = self.VITAL_LIB.vital_detected_object_set_confidence
        do_sc.argtypes = [self.C_TYPE_PTR, ctypes.c_double]
        do_sc(self, confid)

    def type(self):
        do_ty = self.VITAL_LIB.vital_detected_object_get_type
        do_ty.argtypes = [self.C_TYPE_PTR]
        do_ty.restype = DetectedObjectType.C_TYPE_PTR
        c_ptr = do_ty(self)
        if bool(c_ptr) is False:
            # the pointer is null
            return None
        else:
            obj_type = DetectedObjectType(from_cptr=c_ptr)
            return obj_type

    def mask(self):
        """
        Ignore:
            workon_py2
            source ~/code/VIAME/build/install/setup_viame.sh
            export KWIVER_DEFAULT_LOG_LEVEL=info
            export PYTHONPATH=$HOME/code/VIAME/plugins/camtrawl:$PYTHONPATH
            export SPROKIT_PYTHON_MODULES=kwiver.processes:viame.processes:camtrawl_processes

        Example:
            >>> from vital.types import DetectedObject
            >>> self = DetectedObject([0, 0, 1, 1])
        """
        with VitalErrorHandle() as eh:
            return self.C.mask(eh)

    def set_mask(self, mask):
        with VitalErrorHandle() as eh:
            self.C.set_mask(mask, eh)

    def set_type(self, ob_type):
        """
        Example:
            >>> from vital.types import DetectedObject
            >>> from vital.types import DetectedObjectType
            >>> self = DetectedObject([0, 0, 1, 1])
            >>> ob_type = DetectedObjectType.cast({'cat': 1.0})
            >>> ob_type2 = self.type()
        """
        ob_type = DetectedObjectType.cast(ob_type)
        do_ty = self.VITAL_LIB.vital_detected_object_set_type
        do_ty.argtypes = [self.C_TYPE_PTR, DetectedObjectType.C_TYPE_PTR]
        do_ty(self, ob_type)

    # --- Python convineince functions ---

    def __nice__(self):
        """
        Example:
            >>> from vital.types import DetectedObject
            >>> self = DetectedObject([(0, 0), (5, 10)])
            >>> str(self)
            <DetectedObject([0.0, 0.0, 5.0, 10.0], ?type?, 0.0)>
        """
        conf = self.confidence()
        # FIXME: get types working correctly
        # name = self.type().most_likely_class()
        name = '?type?'
        bbox = self.bounding_box().coords
        return '{}, {}, {}'.format(bbox, name, conf)
