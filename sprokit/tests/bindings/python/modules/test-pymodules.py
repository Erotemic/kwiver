#!/usr/bin/env python
#ckwg +28
# Copyright 2012-2013 by Kitware, Inc.
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
"""
Note, if these tests are run with the same python sessions, there will be
failures.  These tests conflict with each other because they depend on
load-time environment variables. It is best to run each test separately.
"""
from __future__ import print_function
from os.path import normpath, expanduser, join
import os
import sys
import pytest

__SINGLE_LOADER_TEST_GAURD__ = False


def _unable_to_run_loader_test():
    global __SINGLE_LOADER_TEST_GAURD__
    if __SINGLE_LOADER_TEST_GAURD__:
        pytest.skip('Unable run this test because another loader test ran')
        return True
    # Allow the first loader test to run
    __SINGLE_LOADER_TEST_GAURD__ = True
    return False


# ------
# Helper utilities (from ubelt)


WIN32  = sys.platform.startswith('win32')
LINUX  = sys.platform.startswith('linux')
DARWIN = sys.platform.startswith('darwin')


def platform_cache_dir():
    """
    Returns a directory which should be writable for any application
    This should be used for temporary deletable data.
    """
    if WIN32:  # nocover
        dpath_ = '~/AppData/Local'
    elif LINUX:  # nocover
        dpath_ = '~/.cache'
    elif DARWIN:  # nocover
        dpath_  = '~/Library/Caches'
    else:  # nocover
        raise NotImplementedError('Unknown Platform  %r' % (sys.platform,))
    dpath = normpath(expanduser(dpath_))
    return dpath


def ensure_app_resource_dir(appname, *args):
    """
    Returns a writable directory for an application and ensures the directory
    exists.  This should be used for temporary deletable data.

    Args:
        appname (str): the name of the application
        *args: any other subdirectories may be specified

    Returns:
        str: dpath: writable cache directory for this application
    """
    dpath = join(platform_cache_dir(), appname, *args)
    return ensuredir(dpath)


def ensuredir(*paths):
    dpath = join(*paths)
    try:
        os.makedirs(dpath)
    except OSError:
        pass
    return dpath


def codeblock(block_str):
    """
    Helper (maybe use ubelt)

    Convinience function for defining code strings. Esspecially useful for
    templated code.
    """
    import textwrap
    return textwrap.dedent(block_str).strip('\n')


def _setup_temp_pythonpath():
    # Create temporary sprokit processes/schedulers that dont exist yet

    test_process_codeblock = codeblock(
        r'''
        from __future__ import print_function
        from sprokit.pipeline import config
        from sprokit.pipeline import process


        class TestPythonProcess(process.PythonProcess):
            def __init__(self, conf):
                process.PythonProcess.__init__(self, conf)


        def __sprokit_register__():
            from sprokit.pipeline import process_factory

            module_name = 'python:' + __name__

            if process_factory.is_process_module_loaded(module_name):
                return

            process_factory.add_process('pythonpath_test_process', 'A test process.', TestPythonProcess)

            process_factory.mark_process_module_as_loaded(module_name)
        '''
    )

    test_scheduler_codeblock = codeblock(
        r'''
        from __future__ import print_function
        from sprokit.pipeline import config
        from sprokit.pipeline import pipeline
        from sprokit.pipeline import scheduler


        class TestPythonScheduler(scheduler.PythonScheduler):
            def __init__(self, conf, pipe):
                scheduler.PythonScheduler.__init__(self, conf, pipe)


        def __sprokit_register__():
            from sprokit.pipeline import scheduler_factory

            module_name = 'python:' + __name__

            if scheduler_factory.is_scheduler_module_loaded(module_name):
                return

            scheduler_factory.add_scheduler('pythonpath_test_scheduler', 'A test scheduler.', TestPythonScheduler)

            scheduler_factory.mark_scheduler_module_as_loaded(module_name)
        ''')

    # Create a temporary place to put the temp modules
    temp_pythonpath = ensure_app_resource_dir('sprokit', 'test_tempfiles',
                                              'test_pythonpath')

    # Clean up and regenerate
    # import shutil
    # shutil.rmtree(temp_pythonpath)
    # ensuredir(temp_pythonpath)

    processes_pkg_dpath = ensuredir(temp_pythonpath, 'temp_processes')
    schedulers_pkg_dpath = ensuredir(temp_pythonpath, 'temp_schedulers')

    process_fpath = join(processes_pkg_dpath, 'pythonpath_test_process.py')
    scheduler_fpath = join(schedulers_pkg_dpath, 'pythonpath_test_scheduler.py')

    with open(join(processes_pkg_dpath, '__init__.py'), 'w') as file:
        file.write('')
    with open(join(schedulers_pkg_dpath, '__init__.py'), 'w') as file:
        file.write('')

    with open(process_fpath, 'w') as file:
        file.write(test_process_codeblock)

    with open(scheduler_fpath, 'w') as file:
        file.write(test_scheduler_codeblock)
    return temp_pythonpath


# -----------
# Tests


def test_import():
    """
    CommandLine:
        python -m sprokit.tests.test-pymodules test_import
    """
    try:
        import sprokit.modules.modules  # NOQA
    except:
        raise AssertionError("Failed to import the modules module")


def test_load():
    if _unable_to_run_loader_test():
        return
    from sprokit.pipeline import config  # NOQA
    from sprokit.pipeline import modules
    from sprokit.pipeline import process_factory

    modules.load_known_modules()

    types = process_factory.types()

    assert 'test_python_process' in types, (
        'Failed to load Python processes')


def test_masking():
    """
    CommandLine:
        python -m sprokit.tests.test-pymodules test_masking
    """
    if _unable_to_run_loader_test():
        return
    os.environ['SPROKIT_NO_PYTHON_MODULES'] = 'ON'
    # os.environ.pop('SPROKIT_NO_PYTHON_MODULES', '')

    from sprokit.pipeline import config  # NOQA
    from sprokit.pipeline import modules
    from sprokit.pipeline import process_factory

    modules.load_known_modules()

    types = process_factory.types()

    assert 'test_python_process' not in types, (
        'Failed to mask out Python processes')


def test_extra_modules():
    """
    CommandLine:
        python -m sprokit.tests.test-pymodules test_extra_modules
    """
    if _unable_to_run_loader_test():
        return
    os.environ['SPROKIT_PYTHON_MODULES'] = 'sprokit.test.python.modules'

    from sprokit.pipeline import config  # NOQA
    from sprokit.pipeline import modules
    from sprokit.pipeline import process_factory

    modules.load_known_modules()

    types = process_factory.types()

    assert 'extra_test_python_process' in types, (
        'Failed to load extra Python processes')


def test_pythonpath():
    """
    CommandLine:
        python -m sprokit.tests.test-pymodules test_pythonpath
    """
    if _unable_to_run_loader_test():
        return
    temp_pythonpath = _setup_temp_pythonpath()

    # Add the temporary dir to the pythonpath
    sys.path.append(temp_pythonpath)
    os.environ['SPROKIT_PYTHON_MODULES'] = os.pathsep.join([
        'temp_processes.pythonpath_test_process',
        'temp_schedulers.pythonpath_test_scheduler',
    ] + os.environ.get('SPROKIT_PYTHON_MODULES', '').split(os.pathsep))

    # os.environ['SPROKIT_PYTHON_SCHEDULERS'] = os.pathsep.join([
    #     'temp_schedulers.pythonpath_test_scheduler',
    # ] + os.environ.get('SPROKIT_PYTHON_SCHEDULERS', '').split(os.pathsep))

    from sprokit.pipeline import config  # NOQA
    from sprokit.pipeline import modules
    from sprokit.pipeline import process_factory
    from sprokit.pipeline import scheduler_factory

    modules.load_known_modules()

    process_types = process_factory.types()

    assert 'pythonpath_test_process' in process_types, (
        'Failed to load extra Python processes accessible from PYTHONPATH')

    scheduler_types = scheduler_factory.types()

    assert 'pythonpath_test_scheduler' in scheduler_types, (
        'Failed to load extra Python schedulers accessible from PYTHONPATH')


if __name__ == '__main__':
    r"""
    CommandLine:
        # Note: running all tests together in this module will fail
        python -m sprokit.tests.test-pymodules
    """
    argv = list(sys.argv[1:])
    if len(argv) > 0 and argv[0] in vars():
        # If arg[0] is a function in this file put it in pytest format
        argv[0] = __file__ + '::' + argv[0]
        argv.append('-s')  # dont capture stdout for single tests
    else:
        # ensure args refer to this file
        argv.insert(0, __file__)
    pytest.main(argv)
