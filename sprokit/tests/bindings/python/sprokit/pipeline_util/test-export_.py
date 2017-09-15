#!/usr/bin/env python
#ckwg +28
# Copyright 2011-2013 by Kitware, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  * Neither name of Kitware, Inc. nor the names of any contributors may be used
#    to endorse or promote products derived from this software without specific
#    prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import os


def test_import():
    try:
        import sprokit.pipeline_util.export_  # NOQA
    except:
        raise AssertionError("Failed to import the export_ module")


def test_simple_pipeline():
    # Try and find the pipeline directory
    from sprokit.test import test
    path = test.grab_test_pipeline_file('simple_pipeline.pipe')

    from sprokit.pipeline import pipeline  # NOQA
    from sprokit.pipeline import modules
    from sprokit.pipeline_util import bake
    from sprokit.pipeline_util import export_

    modules.load_known_modules()

    p = bake.bake_pipe_file(path)
    r, w = os.pipe()

    name = 'graph'

    export_.export_dot(w, p, name)

    p.setup_pipeline()

    export_.export_dot(w, p, name)

    os.close(r)
    os.close(w)


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m sprokit.tests.test-export_
    """
    import sprokit.test
    sprokit.test.test_module()
