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

Interface to VITAL image_container class.

"""
import ctypes
from vital.util import VitalObject
from vital.util import VitalErrorHandle
from vital.util.mixins import NiceRepr
from vital.util import free_void_ptr

VITAL_LIB = VitalObject.VITAL_LIB


class DetectedObjectType (VitalObject, NiceRepr):
    """
    vital::detected_object_type interface class

    Example:
        >>> from vital.types import DetectedObjectType
        >>> self = DetectedObjectType()
        >>> print('self = {!r}'.format(self))
        >>> names = ['foo', 'bar', 'baz']
        >>> scores = [0.0, .9, .1]
        >>> count = len(names)
        >>> self = DetectedObjectType(['foo'], [0.0])
        >>> print('self = {!r}'.format(self))
    """

    def __init__(self, names=None, scores=None, from_cptr=None):
        """
        Create a simple detected object type

        """
        count = None
        super(DetectedObjectType, self).__init__(from_cptr, count, names,
                                                 scores)

    def _new(self, count=None, names=None, scores=None):
        """
        Create a new type container
        """
        if (count is None and names is None and scores is None):
            dot_new = VITAL_LIB.vital_detected_object_type_new
            dot_new.argtypes = []
            dot_new.restype = DetectedObjectType.C_TYPE_PTR
            _inst_ptr = dot_new()
            return _inst_ptr
        else:
            if names is None or scores is None:
                raise ValueError('must specify scores or names')
            if count is None:
                count = len(names)
            if count != len(names) or count != len(scores):
                raise ValueError('count must agree with names and scores')
            dot_nfl = VITAL_LIB.vital_detected_object_type_new_from_list
            dot_nfl.argtypes = [self.C_TYPE_PTR,
                                ctypes.c_size_t,
                                ctypes.POINTER(ctypes.c_char_p),
                                ctypes.POINTER(ctypes.c_double)]
            dot_nfl.restype = DetectedObjectType.C_TYPE_PTR

            # Case params to C types
            c_names = (ctypes.c_char_p * count)()
            c_scores = (ctypes.c_double * count)()
            c_names[:] = names
            c_scores[:] = scores

            _inst_ptr = dot_nfl(None, count, c_names, c_scores)
            return _inst_ptr

    def _destroy(self):
        dot_del = self.VITAL_LIB.vital_detected_object_type_destroy
        dot_del.argtypes = [self.C_TYPE_PTR, VitalErrorHandle.C_TYPE_PTR]
        with VitalErrorHandle() as eh:
            dot_del(self, eh)

    def has_class_name(self, name):
        dot_hcn = self.VITAL_LIB.vital_detected_object_type_has_class_name
        dot_hcn.argtypes = [self.C_TYPE_PTR, ctypes.c_char_p]
        dot_hcn.restype = ctypes.c_bool
        return dot_hcn(self, name)

    def score(self, name):
        if not self.has_class_name(name):
            raise KeyError('name={}'.format(name))
        dot_score = self.VITAL_LIB.vital_detected_object_type_score
        dot_score.argtypes = [self.C_TYPE_PTR, ctypes.c_char_p]
        dot_score.restype = ctypes.c_double
        return dot_score(self, name )

    def get_most_likely_class(self):
        dot_gmlc = self.VITAL_LIB.vital_detected_object_type_get_most_likely_class
        dot_gmlc.argtypes = [self.C_TYPE_PTR]
        dot_gmlc.restype = ctypes.c_char_p
        return dot_gmlc(self)

    def get_most_likely_score(self):
        dot_gmls = self.VITAL_LIB.vital_detected_object_type_get_most_likely_score
        dot_gmls.argtypes = [self.C_TYPE_PTR]
        dot_gmls.restype = ctypes.c_double
        return dot_gmls(self)

    def set_score(self, name, score):
        dot_ss = self.VITAL_LIB.vital_detected_object_type_set_score
        dot_ss.argtypes = [self.C_TYPE_PTR, ctypes.c_char_p, ctypes.c_double]
        dot_ss(self, name, score)

    def delete_score(self, name):
        dot_ds = self.VITAL_LIB.vital_detected_object_type_delete_score
        dot_ds.argtypes[self.C_TYPE_PTR, ctypes.c_char_p]
        dot_ds(self, name)

    def size(self):
        dot_size = VITAL_LIB.vital_detected_object_type_size
        dot_size.argtypes = [self.C_TYPE_PTR]
        dot_size.restype = ctypes.c_size_t
        size = dot_size(self)
        if size < 0:
            size = None
        return size

    def class_names(self, thresh=None):
        """

        Example:
            >>> from vital.types import DetectedObjectType
            >>> self = DetectedObjectType()
            >>> names = ['foo', 'bar', 'baz']
            >>> scores = [0.0, .9, .1]
            >>> self = DetectedObjectType(names, scores)
            >>> self.class_names()
            ['bar', 'baz', 'foo']
            >>> self.class_names(.5)
            ['bar']
        """
        num = self.size()
        if num is None:
            raise Exception('class types are not initialized')
        # Note: this function allocates memory for a string
        dot_cn = self.VITAL_LIB.vital_detected_object_type_class_names
        dot_cn.restype = ctypes.POINTER(ctypes.c_char_p)
        if thresh is None:
            dot_cn.argtypes = [self.C_TYPE_PTR]
            c_names = dot_cn(self)
        else:
            dot_cn.argtypes = [self.C_TYPE_PTR, ctypes.c_double]
            c_names = dot_cn(self, thresh)
        # names = [c_names[i] for i in range(num)]
        # Some names may not be returned if they have a value less than the
        # threshold
        names = []
        for i in range(num):
            name = c_names[i]
            # null terminated
            if name is None:
                break
            names.append(name)
        free_void_ptr(c_names)
        return names

    @staticmethod
    def all_class_size(self):
        dot_acs = VITAL_LIB.vital_detected_object_type_all_class_size
        dot_acs.argtypes = []
        dot_acs.restype = ctypes.c_size_t
        # Note: this function allocates memory for a string
        size = dot_acs()
        if size < 0:
            size = None
        return size

    @staticmethod
    def all_class_names():
        """
        Returns class names used across all instances of DetectedObjectType

        Example:
            >>> from vital.types import DetectedObjectType
            >>> self1 = DetectedObjectType(['foo', 'bar', 'baz'],  [0, 0, 0])
            >>> self2 = DetectedObjectType(['spam', 'eggs'], [.99, .01])
            >>> sorted(self1.all_class_names())
            ['bar', 'baz', 'eggs', 'foo', 'spam']
        """
        num = DetectedObjectType.all_class_size()
        if num is None:
            raise Exception('all class types are not initialized')
        dot_acn = VITAL_LIB.vital_detected_object_type_all_class_names
        # dot_acn.argtypes = [self.C_TYPE_PTR]
        dot_acn.argtypes = []
        dot_acn.restype = ctypes.POINTER(ctypes.c_char_p)
        # Note: this function allocates memory for a string
        c_names = dot_acn()
        names = [c_names[i] for i in range(num)]
        free_void_ptr(c_names)
        return names

    # ----
    @classmethod
    def cast(cls, data):
        """
        Example:
            >>> from vital.types import DetectedObjectType
            >>> obj_type = DetectedObjectType.cast({'cat': 1.0})
            >>> assert obj_type.class_names() == ['cat']
        """
        if isinstance(data, dict):
            names = list(data.keys())
            scores = list(data.values())
            return DetectedObjectType(names=names, scores=scores)
        return super(DetectedObjectType, cls).cast(data)

    def __contains__(self, name):
        return self.has_class_name(name)

    def __len__(self):
        num = self.size()
        if num is None:
            num = 0
        return num

    def to_dict(self):
        name_to_score = {name: self.score(name) for name in self.class_names()}
        return name_to_score

    def __nice__(self):
        size = self.size()
        if size is None:
            return 'NULL'
        else:
            most_likely = self.get_most_likely_class()
            return '{}, n={}'.format(size, most_likely)
