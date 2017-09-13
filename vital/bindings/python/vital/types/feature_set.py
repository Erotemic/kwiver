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

Interface to vital::feature_set class.

"""
import ctypes

from vital.types import Feature
from vital.util import free_void_ptr
from vital.util import VitalObject
from vital.util import VitalErrorHandle


VITAL_LIB = VitalObject.VITAL_LIB


def define_feature_set_c_api():
    """
    Ignore:
        workon_py2
        source ~/code/VIAME/build/install/setup_viame.sh
        export KWIVER_DEFAULT_LOG_LEVEL=info
        export PYTHONPATH=$HOME/code/VIAME/plugins/camtrawl:$PYTHONPATH
        export SPROKIT_PYTHON_MODULES=kwiver.processes:viame.processes:camtrawl_processes

        vital_feature_destroy

        from vital.util import VitalObject
        VITAL_LIB = VitalObject.VITAL_LIB

        from vital.util.find_vital_library import find_vital_library
        VITAL_LIB = find_vital_library(use_cache=False)
        VITAL_LIB.vital_feature_destroy
        VITAL_LIB.vital_feature_set_new_from_list


        with VitalErrorHandle() as eh:
            _inst_ptr = self.C.new_empty(eh)
        feature_set = FeatureSet.from_cptr(_inst_ptr)

    """
    class feature_set_c_api(object):
        pass
    C = feature_set_c_api()
    C.new_from_list = VITAL_LIB.vital_feature_set_new_from_list
    C.new_from_list.argtypes = [ctypes.POINTER(Feature.C_TYPE_PTR), ctypes.c_size_t, VitalErrorHandle.C_TYPE_PTR]
    C.new_from_list.restype = FeatureSet.C_TYPE_PTR

    C.new_empty = VITAL_LIB.vital_feature_set_new_empty
    C.new_empty.argtypes = [VitalErrorHandle.C_TYPE_PTR]
    C.new_empty.restype = FeatureSet.C_TYPE_PTR

    C.destroy = VITAL_LIB.vital_feature_set_destroy
    C.destroy.argtypes = [FeatureSet.C_TYPE_PTR, VitalErrorHandle.C_TYPE_PTR]
    C.destroy.restype = None

    C.size = VITAL_LIB.vital_feature_set_size
    C.size.argtypes = [FeatureSet.C_TYPE_PTR, VitalErrorHandle.C_TYPE_PTR]
    C.size.restype = ctypes.c_size_t

    C.features = VITAL_LIB.vital_feature_set_features
    C.features.argtypes = [FeatureSet.C_TYPE_PTR, ctypes.POINTER(ctypes.POINTER(Feature.C_TYPE_PTR)), VitalErrorHandle.C_TYPE_PTR]
    C.features.restype = None

    C.getitems = VITAL_LIB.vital_feature_set_getitems
    C.getitems.argtypes = [FeatureSet.C_TYPE_PTR, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.POINTER(Feature.C_TYPE_PTR)), VitalErrorHandle.C_TYPE_PTR]
    C.getitems.restype = None

    C.getitem = VITAL_LIB.vital_feature_set_getitem
    C.getitem.argtypes = [FeatureSet.C_TYPE_PTR, ctypes.c_size_t, ctypes.POINTER(Feature.C_TYPE_PTR), VitalErrorHandle.C_TYPE_PTR]
    C.getitem.restype = None

    C.delitem = VITAL_LIB.vital_feature_set_delitem
    C.delitem.argtypes = [FeatureSet.C_TYPE_PTR, ctypes.c_size_t, VitalErrorHandle.C_TYPE_PTR]
    C.delitem.restype = None

    C.add = VITAL_LIB.vital_feature_set_add
    C.add.argtypes = [FeatureSet.C_TYPE_PTR, Feature.C_TYPE_PTR, VitalErrorHandle.C_TYPE_PTR]
    C.add.restype = None
    return C


class FeatureSet (VitalObject):
    """
    vital::feature_set interface class

    SeeAlso:
        ../../../c/types/feature_set.h
        ../../types/feature_set.h
    """

    def __init__(self, feats=None, count=None, from_cptr=None):
        """
        Create a simple detected object type

        """
        super(FeatureSet, self).__init__(from_cptr, feats, count)

    def _new(self, feats=None, count=None):
        if feats is None or count is None or count == 0:
            with VitalErrorHandle() as eh:
                _inst_ptr = self.C.new_empty(eh)
                return _inst_ptr
        else:
            fs_nfl = self.VITAL_LIB.vital_feature_set_new_from_list
            fs_nfl.argtypes = [ctypes.POINTER(Feature.C_TYPE_PTR), ctypes.c_size_t, VitalErrorHandle.C_TYPE_PTR]
            fs_nfl.restype = self.C_TYPE_PTR
            c_feats = []
            with VitalErrorHandle() as eh:
                _inst_ptr = self.C.new_from_list(c_feats, count, eh)
                return _inst_ptr

    def _destroy(self):
        with VitalErrorHandle() as eh:
            return self.C.destroy(self, eh)

    def add(self, feat):
        c_feat = Feature.cast(feat)
        with VitalErrorHandle() as eh:
            return self.C.add(self, c_feat, eh)

    def size(self):
        with VitalErrorHandle() as eh:
            return self.C.size(self, eh)


FeatureSet.C = define_feature_set_c_api()
