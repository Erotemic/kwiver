"""
Notes:
    C++ uses a left-recursive (non-context free) grammer, so we are not going
    to be able to parse it easilly. The goal of this is to implement some
    hueristics to parse C++ code on a file-by-file basis. Its purpose is to
    autogenerate a template that can then be modified as desired.


References:
    # C++ BNF Grammar
    http://www.nongnu.org/hcb/

"""
from os.path import expanduser, join
import re
import utool as ut
import ubelt as ub
import datetime
from c_patterns import CPatternMatch, CArgspec, CArg, CType
from c_patterns import named, optional, VARNAME, CV_QUALIFIER

BLANK_LINE_PLACEHOLDER = '// NOOP(BLANK_LINE)'

COPYRIGHT = ub.codeblock(
    '''
    /*ckwg +29
     * Copyright 2013-{year} by Kitware, Inc.
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
    '''
).format(year=datetime.datetime.now().year)


class TypeRegistry(object):
    mappings = {
        'vector_t': CType('double *'),
    }


class VitalRegistry(object):
    sptr_caches = {
        'image_container': 'IMGC_SPTR_CACHE',
        'feature': 'FEATURE_SPTR_CACHE',
        'detected_object': 'DOBJ_SPTR_CACHE',
        'detected_object_type': 'DOT_SPTR_CACHE',
    }

    @staticmethod
    def get_sptr_cachename(classname):
        return VitalRegistry.sptr_caches.get(classname, '_' + classname.upper() + 'SPTR_CACHE')

    vital_types = {
        'bounding_box',
        'bounding_box_d',
        'detected_object_type',
    }

    special_cxx_to_c = {
        'bounding_box_d': 'bounding_box_t',
    }

    vital_types.update(sptr_caches.keys())
    vital_types.update(special_cxx_to_c.keys())

    reinterpretable = {
        'bounding_box',
        'bounding_box_d',
    }

    # smart_pointer_types = {
    #     'vital_detected_object_t',
    # }


@ut.reloadable_class
class VitalCArg(CArg):

    def c_spec(arg):
        argtype = arg.c_argtype()
        if arg.default is None:
            return '{} {}'.format(argtype, arg.name)
        else:
            return '{} {}={}'.format(argtype, arg.name, arg.default)

    def c_argtype(carg):
        """
        The C type that corresponds to this C++ type
        """
        data_base = carg.type.data_base
        ptr_degree = carg.type.ptr_degree + carg.type.ref_degree
        if data_base.endswith('_sptr'):
            ptr_degree += 1
            data_base = data_base[:-5]
        # print('carg.type = {}'.format(carg.type))
        # print('data_base = {}'.format(data_base))
        # print('type = {!r}'.format(type))
        if data_base in TypeRegistry.mappings:
            return TypeRegistry.mappings[type]
        elif data_base in VitalRegistry.vital_types:
            if data_base in VitalRegistry.special_cxx_to_c:
                typestr = VitalRegistry.special_cxx_to_c[data_base]
            else:
                typestr = 'vital_{}_t'.format(data_base)
            return CType(typestr + '*' * ptr_degree)
        else:
            return carg.type

    def cxx_name(carg):
        if carg.type.is_native():
            return carg.name
        return '_' + carg.name

    def c_to_cxx(carg):
        # for binding input arguments
        # TODO: robustness

        # c_argtype = carg.c_argtype()
        data_base = carg.type.data_base
        is_smart = data_base.endswith('_sptr')

        cxx_name = carg.cxx_name()
        c_name = carg.name

        # print('carg = {!r}'.format(carg))
        # print('carg.type.is_native = {!r}'.format(carg.type.is_native()))
        if carg.type.is_native():
            # text = '{} {} = {};'.format(carg.type, cxx_name, c_name)
            text = BLANK_LINE_PLACEHOLDER
        elif is_smart:
            cxx_type = str(carg.type)
            pointed_type = data_base[:-5]
            SPTR_CACHE = VitalRegistry.get_sptr_cachename(pointed_type)
            text = ub.codeblock(
                '''
                kwiver::vital::{cxx_type} {cxx_name};
                if( {cxx_name} != NULL )
                {{
                  {cxx_name} = kwiver::vital_c::{SPTR_CACHE}.get( {c_name} );
                }}
                '''
            ).format(cxx_type=cxx_type, cxx_name=cxx_name, c_name=carg.name,
                     SPTR_CACHE=SPTR_CACHE)
        # print('CASTING TO CXX carg.type_ = {!r}'.format(carg.type_))
        # print('base = {!r}'.format(base))
        # print('carg._orig_text = {!r}'.format(carg._orig_text))
        elif data_base in VitalRegistry.reinterpretable:
            # print('carg = {!r}'.format(carg))
            # print('carg.c_argtype = {!r}'.format(carg.c_argtype))
            cxx_type = carg.type.data_base
            ptr_degree = carg.type.ptr_degree + carg.type.ref_degree
            cxx_type1 = cxx_type + '*' * carg.type.ptr_degree + '&' * carg.type.ref_degree
            cxx_type2 = cxx_type + '*' * ptr_degree
            text = 'kwiver::vital::{} {} = reinterpret_cast< kwiver::vital::{} >({});'.format(
                cxx_type1, cxx_name, cxx_type2, c_name)
        else:
            text = 'NOT_IMPLEMENTED({}, {}, {});'.format(carg.type, cxx_name, c_name)
        # print(text)
        # print()
        return text

    def cxx_to_c(carg):
        print('carg = {!r}'.format(carg))
        # TODO: robustness
        # (mostly for ret vars binding output)
        data_base = carg.type.data_base
        is_smart = data_base.endswith('_sptr')

        cxx_name = carg.cxx_name()
        c_name = carg.name
        if carg.type.is_native():
            # return 'auto {} = {};'.format(c_name, cxx_name)
            text = BLANK_LINE_PLACEHOLDER
        elif is_smart:
            sptr_type = data_base.split('::')[-1]
            classname = sptr_type[:-5]
            c_type = 'vital_{}_t*'.format(classname)
            cxx_name += '.get()'
            text = '{} {} = reinterpret_cast< {} >( {} );'.format(c_type, c_name, c_type, cxx_name)
        else:
            text = 'NOT_IMPLEMENTED({}, {}, {})'.format(
                carg.c_argtype(), c_name, cxx_name)
        return text

    def vital_classname(carg):
        base = carg.type.data_base
        match = re.match('vital_' + named('vt', VARNAME) + '_t' + '\s*' + optional(CV_QUALIFIER), base)
        if match:
            return match.groupdict()['vt']
        return None

    def python_ctypes(carg):
        """
        The python ctypes type that corresponds to this C type
        """
        import ctypes

        def wrap_pointer(ctype, degree):
            for _ in range(degree):
                ctype = 'ctypes.POINTER({})'.format(ctype)
            return ctype

        base = carg.type.data_base
        ptr_degree = carg.type.ptr._degree

        if base == 'void' and ptr_degree == 0:
            return None
        elif base == 'vital_error_handle_t':
            assert ptr_degree > 0
            ctype = wrap_pointer('VitalErrorHandle.C_TYPE_PTR', ptr_degree - 1)
            return ctype
        else:
            if hasattr(ctypes, 'c_' + base):
                ctype = wrap_pointer('ctypes.c_' + base, ptr_degree)
                return ctype
            else:
                # match = re.match('vital_' + named('vt', VARNAME) + '_t' + '\s*' + named('is_const', 'const') + '?', base)
                # if match:
                #    c_class = match.groupdict()['vt']
                c_class = carg.vital_classname()
                if c_class is not None:
                    py_class = ut.to_camel_case(c_class)
                    assert ptr_degree > 0
                    ctype = py_class + '.C_TYPE_PTR'
                    ctype = wrap_pointer(ctype, ptr_degree - 1)
                    return ctype
            raise NotImplementedError(str(carg))


CArgspec._CARG = VitalCArg


def inspect_existing_bindings(classname):

    cxxtype = VitalTypeIntrospectCxx(classname)
    cxxtype.parse_cxx_class_header()

    cbind = VitalTypeIntrospectCBind(classname)
    cbind.parse_c_class_bindings()

    cxx_funcnames = {info.cxx_funcname() for info in cxxtype.cxx_method_infos}
    bound_funcnames = {info.cxx_funcname() for info in cbind.cxx_method_infos}

    print('cxx_funcnames = {}'.format(ut.repr4(sorted(cxx_funcnames))))
    print('bound_funcnames = {}'.format(ut.repr4(sorted(bound_funcnames))))

    unbound_funcs = cxx_funcnames.difference(bound_funcnames)
    print('unbound_funcs = {!r}'.format(unbound_funcs))

    nonstandard_bindings = bound_funcnames.difference(cxx_funcnames)
    print('nonstandard_bindings = {!r}'.format(nonstandard_bindings))


def DETECTED_OBJECT_WIP():
    """
    import sys
    sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings/python/vital/types')
    from c_introspect import *  # NOQA
    #classname = 'oriented_bounding_box'
    classname = 'detected_object'


    cxxtype = VitalTypeIntrospectCxx(classname)
    cxxtype.parse_cxx_class_header()
    text = cxxtype.dump_c_bindings()
    print(ub.highlight_code(text, 'cxx'))

    cbind = VitalTypeIntrospectCBind(classname)
    cbind.parse_c_class_bindings()

    inspect_existing_bindings(classname)
    """


class VitalTypeIntrospectCxx(object):
    """
    For the actual C++ class def

    Example:
        >>> import sys
        >>> sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings/python/vital/types')
        >>> from c_introspect import *
        >>> #classname = 'oriented_bounding_box'
        >>> classname = 'detected_object'
        >>> self = VitalTypeIntrospectCxx(classname)
        >>> self.parse_cxx_class_header()
        >>> text = self.dump_c_bindings()
        >>> print(ub.highlight_code(text, 'cxx'))
    """
    def __init__(self, classname):
        self.classname = classname
        self.cxx_type_base = expanduser('~/code/VIAME/packages/kwiver/vital/types/')
        self.cxx_method_infos = []
        self.cxx_rel_includes = []

    def parse_cxx_class_header(self):
        cxx_path = join(self.cxx_type_base, self.classname + '.h')

        text = ub.readfrom(cxx_path)

        # Remove comments
        text = CPatternMatch.strip_comments(text)
        self.cxx_constructor_infos = CPatternMatch.constructors(text, self.classname)
        self.cxx_method_infos = CPatternMatch.func_declarations(text, self.classname)
        self.cxx_rel_includes = CPatternMatch.relative_includes(text)

    def dump_c_bindings(self):
        fmtdict = {
            'c_type': 'vital_{classname}_t'.format(classname=self.classname),
            'copyright': COPYRIGHT,
            'classname': self.classname,
            'CLASSNAME': self.classname.upper()
        }

        sptr_header = self.autogen_vital_header_c(fmtdict)

        parts = [sptr_header]
        parts = []

        if self.cxx_constructor_infos:
            parts.append(ut.codeblock(
                '''
                // --- CONSTRUCTORS ---
                '''))

        for n, info in enumerate(self.cxx_constructor_infos):
            text = self.autogen_vital_sptr_init_c(n, info, fmtdict)
            parts.append(text)

        if self.cxx_constructor_infos:
            parts.append(ut.codeblock(
                '''
                // --- METHODS ---
                '''))

        for n, info in enumerate(self.cxx_method_infos):
            text = self.autogen_vital_method_c(info, fmtdict)
            parts.append(text)
            if n > 0:
                break

        # print(text)
        text = '\n\n\n'.join(parts)
        return text

    def autogen_vital_header_c(self, fmtdict):
        sptr_header = ub.codeblock(
            '''
            {copyright}

            #include "{classname}.h"
            #include <vital/types/{classname}.h>
            #include <vital/bindings/c/helpers/c_utils.h>

            namespace kwiver {{
            namespace vital_c {{

            // Allocate our shared pointer cache object
            SharedPointerCache< kwiver::vital::{classname}, {c_type}>
              {CLASSNAME}_SPTR_CACHE( "{classname}" );

            }} }}

            using namespace kwiver;

            ''').format(**fmtdict)
        return sptr_header

    def autogen_vital_sptr_init_c(self, n, info, fmtdict):
        construct_fmt = ub.codeblock(
            '''
            {c_return_type}
            vital_{classname}_from_{init_name}( {c_argspec} )
            {{
              STANDARD_CATCH(
                "vital_{classname}_from_{init_name}", eh,

                {c_to_cxx_conversion}

                auto _retvar = std::make_shared< kwiver::vital::{classname} >( {cxx_callargs} );
                kwiver::vital_c::{SPTR_CACHE}.store( _retvar );

                {return_conversion}

                return retvar;

              );
              return NULL;
            }}
            ''')

        init_name = 'v{}'.format(n)

        print('info = {!r}'.format(info))
        argsepc = info['argspec']

        ret_type = CType(info['return_type'])

        return_arg = VitalCArg(ret_type.data_base + '_sptr', 'retvar')

        # print('return_arg = {!r}'.format(return_arg))
        c_return_type = return_arg.c_argtype()
        # print('c_return_type = {!r}'.format(c_return_type))

        return_conversion = return_arg.cxx_to_c()

        # print('argsepc = {!r}'.format(argsepc))
        cxx_callargs = argsepc.format_callargs_cxx()

        c_to_cxx_conversion = ub.indent(
            argsepc.c_to_cxx_conversion(), ' ' * 4).lstrip()

        # Hack
        argsepc.args.append(
            VitalCArg('vital_error_handle_t *', 'eh', default='NULL')
        )
        c_argspec = argsepc.format_argspec_c()

        text = construct_fmt.format(
            c_return_type=c_return_type,
            return_conversion=return_conversion,
            SPTR_CACHE=VitalRegistry.get_sptr_cachename(self.classname),
            init_name=init_name,
            c_argspec=c_argspec,
            cxx_callargs=cxx_callargs,
            c_to_cxx_conversion=c_to_cxx_conversion,
            **fmtdict,
        )
        text = '\n'.join([line for line in text.split('\n') if BLANK_LINE_PLACEHOLDER not in line])
        return text

    def autogen_vital_method_c(self, info, fmtdict):
        # TODO: handle outvars
        c_bind_method = ut.codeblock(
            '''
            {c_return_type} vital_{classname}_{c_funcname}({c_argspec})
            {{
              STANDARD_CATCH(
                "vital_{classname}_{c_funcname}", eh,
                {c_to_cxx_conversion}
                auto _retvar = reinterpret_cast<kwiver::vital::{classname}*>(self)->{c_funcname}({cxx_callargs});
                {return_convert}
                return retvar;
              );
              return NULL;
            }}
        ''')

        return_arg = VitalCArg(info['return_type'], 'retvar')

        argsepc = info['argspec']
        cxx_callargs = argsepc.format_callargs_cxx()

        c_to_cxx_conversion = ub.indent(
            argsepc.c_to_cxx_conversion(), ' ' * 4).lstrip()

        # Hack
        argsepc.args.insert(0, VitalCArg('{} *'.format(fmtdict['c_type']), 'self'))
        argsepc.args.append(VitalCArg('vital_error_handle_t *', 'eh', default='NULL'))
        c_argspec = argsepc.format_argspec_c()

        text = c_bind_method.format(
            c_return_type=return_arg.c_argtype(),
            return_convert=return_arg.cxx_to_c(),
            c_funcname=info['c_funcname'],
            c_argspec=c_argspec,
            cxx_callargs=cxx_callargs,
            c_to_cxx_conversion=c_to_cxx_conversion,
            **fmtdict,
        )
        return text


class VitalTypeIntrospectCBind(object):
    """

    Example:
        >>> import sys
        >>> sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings/python/vital/types')
        >>> from c_introspect import *
        >>> classname = 'feature_set'
        >>> self = VitalTypeIntrospectCBind(classname)
        >>> self.parse_c_class_bindings()
    """

    def __init__(self, classname):
        self.classname = classname
        self.c_binding_base = expanduser('~/code/VIAME/packages/kwiver/vital/bindings/c/types/')
        self.cxx_method_infos = []
        self.cxx_rel_includes = []

    def parse_c_class_bindings(self):
        """
        Make a header using the cxx impl
        """
        cxx_path = join(self.c_binding_base, self.classname + '.cxx')

        text = ub.readfrom(cxx_path)

        text = CPatternMatch.strip_comments(text)
        self.cxx_method_infos = CPatternMatch.func_definitions(text, self.classname)
        self.cxx_rel_includes = CPatternMatch.relative_includes(text)

    def dump_c_header(self):
        import ubelt as ub

        method_fmtstr = ub.codeblock(
            '''
            VITAL_C_EXPORT
            {return_type} {c_funcname}({argspec});
            ''')

        fmtdict = dict(
            classname=self.classname,
            CLASSNAME=self.classname.upper()
        )

        methods = []
        for method_info in self.cxx_method_infos:
            d = fmtdict.copy()
            d.update(method_info)
            d['argspec'] = d['argspec'].replace('\n', ' ')
            d['argspec'] = re.sub('  *', ' ', d['argspec'])
            method_prototype = method_fmtstr.format(**d)
            methods.append(method_prototype)

        method_block = '\n\n'.join(methods)
        print(method_block)

        vital_types = []
        for header in self.cxx_rel_includes:
            other = header.rstrip('.h')
            if other != self.classname:
                vital_types.append(other)
        vital_types.append(self.classname)

        vital_type_include_lines = []
        for vital_type in vital_types:
            line = '#include <vital/bindings/c/types/{vital_type}.h>'.format(vital_type=vital_type)
            vital_type_include_lines.append(line)
        vital_type_include_block = '\n'.join(vital_type_include_lines)
        fmtdict['vital_type_include_block'] = vital_type_include_block

        body_fmtstr = ub.codeblock(
            r'''
            {copyright}

            /**
             * \file
             * \brief core {classname} class interface
             *
             * \seealso ../../types/{classname}.h
             * \seealso ../../python/vital/types/{classname}.py
             */

            #ifndef VITAL_C_{CLASSNAME}_H_
            #define VITAL_C_{CLASSNAME}_H_

            #ifdef __cplusplus
            extern "C"
            {{
            #endif

            #include <stddef.h>
            #include <stdint.h>

            #include <vital/bindings/c/error_handle.h>
            #include <vital/bindings/c/vital_c_export.h>
            {vital_type_include_block}


            /// Opaque structure for vital::{classname}
            typedef struct vital_{classname}_s vital_{classname}_t;

            {method_block}

            #ifdef __cplusplus
            }}
            #endif

            #endif // VITAL_C_{CLASSNAME}_H_
            ''')

        d = fmtdict.copy()
        d['method_block'] = method_block
        d['alt_constructors'] = '??'
        d['copyright'] = COPYRIGHT
        autogen_text = body_fmtstr.format(**d)

        print(autogen_text)

        # autogen_fpath = join(self.c_binding_base, self.classname + '.h.autogen')
        autogen_fpath = join(self.c_binding_base, self.classname + '.h')

        # import utool as ut
        # ut.dump_autogen_code(autogen_fpath, autogen_text, codetype='c', show_diff=True)
        # ut.dump_autogen_code(autogen_fpath, autogen_text, codetype='c', dowrite=True)

        ub.writeto(autogen_fpath, autogen_text)

    def make_python_ctypes(self):
        blocks = []
        for method_info in self.cxx_method_infos:

            c_funcname = method_info['c_funcname']
            endre = re.compile('vital_' + self.classname + '_' + named('suffix', VARNAME))
            match = endre.match(c_funcname)
            if match:
                suffix = match.groupdict()['suffix']
            else:
                suffix = c_funcname

            cargs = CArgspec(method_info['argspec'], kind='c')
            # print('')
            c_funcname = method_info['c_funcname']
            # print('c_funcname = {!r}'.format(c_funcname))

            restype = VitalCArg(method_info['return_type']).python_ctypes()
            # print('restype = {!r}'.format(restype))

            argtypes = '[' + cargs.format_typespec_python() + ']'
            # print('argtypes = {!r}'.format(argtypes))

            block = ub.codeblock(
                r'''
                C.{suffix} = VITAL_LIB.{c_funcname}
                C.{suffix}.argtypes = {argtypes}
                C.{suffix}.restype = {restype}
                ''').format(
                    suffix=suffix,
                    c_funcname=c_funcname,
                    argtypes=argtypes,
                    restype=restype)
            blocks.append(block)

        py_c_api = 'def define_{}_c_api():'.format(self.classname)
        py_c_api += '\n    class {}_c_api(object):'.format(self.classname)
        py_c_api += '\n        pass'
        py_c_api += '\n    C = {}_c_api()'.format(self.classname)
        py_c_api += '\n' + ub.indent('\n\n'.join(blocks))
        py_c_api += '\n    return C'

        # import autopep8
        # import utool as ut
        # arglist = ['--max-line-length', '79']
        # arglist.extend(['-a'])
        # # arglist.extend(['-a', '-a'])
        # arglist.extend(['--experimental'])
        # arglist.extend([''])
        # autopep8_options = autopep8.parse_args(arglist)
        # fixed_codeblock = autopep8.fix_code(py_c_api, options=autopep8_options)
        # print(fixed_codeblock)

        # ut.copy_text_to_clipboard(py_c_api)
        print(py_c_api)


def regex_cpp_vital_type_introspect():
    """
    Introspect with regexes because parsing C++ is not easy.

    # Wrap this
    ~/code/VIAME/packages/kwiver/vital/types/feature_set.h

    # Using examples
    ~/code/VIAME/packages/kwiver/vital/types/detected_object_set.h
    ~/code/VIAME/packages/kwiver/vital/bindings/c/types/detected_object_set.h


    """
    from os.path import expanduser, join
    kwiver_base = expanduser('~/code/VIAME/packages/kwiver')
    fpath = join(kwiver_base, 'vital/types/feature_set.h')

    import ubelt as ub
    text = ub.readfrom(fpath)

    VARNAME = '[A-Za-z_][A-Za-z0-9_]*'
    WHITESPACE =  r'\s*'

    def named(key, regex):
        return r'(?P<%s>%s)' % (key, regex)

    def optional(regex):
        return r'(%s)?' % (regex,)

    def regex_or(list_):
        return '(' + '|'.join(list_) + ')'

    import re
    STARTLINE = '^'
    # ENDLINE = '$'
    lparen = re.escape('(')
    rparen = re.escape(')')

    # Regex for attempting to match a C++ header
    header_func_def = WHITESPACE.join([
        STARTLINE,
        optional(named('is_virtual', 'virtual')),
        named('return_type', '.*?'),
        named('funcname', VARNAME),
        lparen,
        rparen,
        optional(named('cv_qualifier', CV_QUALIFIER)),
        optional(named('is_init0', '=' + WHITESPACE + '0')),
        regex_or([
            named('semi', ';'),
            named('is_inline', re.escape('{'))
        ]),
        # ENDLINE
    ])

    method_info_list = []
    flags = re.MULTILINE
    for match in re.finditer(header_func_def, text, flags=flags):
        print('match = {!r}'.format(match))
        d = match.groupdict()
        # print('d = {!r}'.format(d))
        for k, v in d.items():
            if k.startswith('is_'):
                d[k] = v is not None
        # print('d = {}'.format(ut.repr4(d)))
        method_info_list.append(d)


# def c_introspect():
#     """
#     pip isntall pycparser
#     """
#     # http://eli.thegreenplace.net/2011/07/03/parsing-c-in-python-with-clang
#     import pycparser
#     from pycparser import c_parser, c_ast, parse_file

#     # A simple visitor for FuncDef nodes that prints the names and
#     # locations of function definitions.
#     class FuncDefVisitor(c_ast.NodeVisitor):
#         def visit_FuncDef(self, node):
#             print('%s at %s' % (node.decl.name, node.decl.coord))

#     fpath = '/home/joncrall/code/VIAME/packages/kwiver/vital/types/feature.h'
#     # fpath = '/home/joncrall/code/VIAME/packages/kwiver/vital/types/feature.cxx'
#     # fpath = '/home/joncrall/code/VIAME/build/build/src/kwiver-build/vital'

#     cpp_args = [
#         '-E',
#         '-I' + 'utils/fake_libc_include',
#         # '-I' + '/home/joncrall/code/VIAME/build/install/include',
#         '-I' + '/home/joncrall/code/VIAME/build/build/src/kwiver-build/vital',
#         # '-I' + '/usr/include/c++/5',
#         # '-I' + '/usr/include/x86_64-linux-gnu/c++/5',
#     ]

#     # Note that cpp is used. Provide a path to your own cpp or
#     # make sure one exists in PATH.
#     ast = parse_file(fpath, use_cpp=True,
#                      cpp_path='gcc',
#                      cpp_args=cpp_args)

#     v = FuncDefVisitor()
#     v.visit(ast)


# def cpp_introspect():
#     """
#     apt install libclang1
#     apt install libclang-dev
#     sudo updatedb
#     locate libclang

#     http://eli.thegreenplace.net/2011/07/03/parsing-c-in-python-with-clang

#     clang -cc1 -ast-print-xml /home/joncrall/code/VIAME/packages/kwiver/vital/types/feature.h
#     clang -ast-dump /home/joncrall/code/VIAME/packages/kwiver/vital/types/feature.h
#     -ast-dump

#     pip install CppHeaderParser

#     sudo apt-get install gccxml

#     gccxml /home/joncrall/code/VIAME/packages/kwiver/vital/types/feature.h
#     castxml /home/joncrall/code/VIAME/packages/kwiver/vital/types/feature.h
#     """
#     import CppHeaderParser

#     fpath = '/home/joncrall/code/VIAME/packages/kwiver/vital/types/feature.h'
#     cppHeader = CppHeaderParser.CppHeader(fpath)

#     # import sys
#     # import clang.cindex
#     # clang.cindex.Config.set_library_file('/usr/lib/llvm-3.8/lib/libclang.so')

#     # def find_typerefs(node, typename):
#     #     """ Find all references to the type named 'typename'
#     #     """
#     #     if node.kind.is_reference():
#     #         ref_node = clang.cindex.Cursor_ref(node)
#     #         if ref_node.spelling == typename:
#     #             print('Found %s [line=%s, col=%s]' % (
#     #                 typename, node.location.line, node.location.column))
#     #     # Recurse for children of this node
#     #     for c in node.get_children():
#     #         find_typerefs(c, typename)

#     # index = clang.cindex.Index.create()
#     # tu = index.parse(fpath)

if __name__ == '__main__':
    r"""
    CommandLine:
        python -m vital.types.c_introspect
    """
    import pytest
    pytest.main([__file__, '--doctest-modules'])
