from os.path import expanduser, join
import re
import utool as ut
import ubelt as ub
import datetime


VARNAME = '[A-Za-z_][A-Za-z0-9_]*'
C_FILENAME = '[A-Za-z_.][A-Za-z0-9_.]*'
WHITESPACE =  r'\s*'

C_SINGLE_COMMENT = '//.*'
C_MULTI_COMMENT = r'/\*.*?\*/'

TYPENAME = '[A-Za-z_:][:<>A-Za-z0-9_*]*'

SPACE = '[ \t]*'

STARTLINE = '^'
# ENDLINE = '$'
lparen = re.escape('(')
rparen = re.escape(')')
rcurly = re.escape('{')


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


def named(key, regex):
    return r'(?P<%s>%s)' % (key, regex)


def optional(regex):
    return r'(%s)?' % (regex,)


def regex_or(list_):
    return '(' + '|'.join(list_) + ')'


@ut.reloadable_class
class CArg(ub.NiceRepr):
    def __init__(carg, type, name=None, default=None, orig_text=None):
        carg.type = type
        carg.name = name
        carg.default = default
        carg._orig_text = orig_text

    @classmethod
    def parse(CArg, text):
        parts = text.strip().split(' ')
        ctype = ' '.join(parts[0:-1])
        cname = parts[-1]
        ctype += (' ' + ('*' * cname.count('*')))
        cname = cname[cname.count('*'):]
        parts = cname.split('=')
        default = None
        if len(parts) == 2:
            name, default = parts
        else:
            name = parts[0]
        carg = CArg(ctype, name, default, text)
        return carg

    def __nice__(carg):
        if carg.name is not None:
            if carg.default is None:
                return '{}{}'.format(carg.type, carg.name)
            else:
                return '{}{}={}'.format(carg.type, carg.name, carg.default)
        else:
            return '{}'.format(carg.type)

    def split_pointer(carg):
        ptr_match = re.search('(\*|\s)*$', carg.type, flags=re.MULTILINE)
        base = carg.type[:ptr_match.start()].strip()
        ptrs = carg.type[ptr_match.start():ptr_match.end()]
        ptrs = re.sub('\s', '', ptrs)
        return base, ptrs

    def basetype(carg):
        base = carg.split_pointer()[0]
        return base

    def strip_const(carg):
        type = carg.type.strip().rstrip('const&').strip()
        return type

    def pointer_degree(carg):
        return len(carg.split_pointer()[1])

    def c_spec(arg):
        argtype = arg.c_argtype()
        if not argtype.endswith('*'):
            argtype += ' '
        if arg.default is None:
            return '{}{}'.format(argtype, arg.name)
        else:
            return '{}{}={}'.format(argtype, arg.name, arg.default)

    def is_native(carg):
        native_types = ['double', 'int', 'float', 'bool']
        return carg.type.strip() in native_types

    def c_argtype(carg):
        """
        The C type that corresponds to this C++ type
        """
        known_mappings = {
            'vector_t': 'double *',
        }
        type = carg.strip_const()
        if type in known_mappings:
            return known_mappings[type]
        else:
            return carg.type.strip()

    def c_to_cxx(carg):
        # for binding input arguments
        # TODO: robustness
        return 'REINTERP_TYPE({}, {}, {})'.format(
            carg.type, '_' + carg.name, carg.name)

    def vital_classname(carg):
        base = carg.basetype()
        match = re.match('vital_' + named('vt', VARNAME) + '_t' + '\s*' + named('is_const', 'const') + '?', base)
        if match:
            return match.groupdict()['vt']
        return None

    def vital_c_type(carg):
        type = carg.type.strip()
        if type.endswith('_sptr'):
            sptr_type = type.split('::')[-1]
            classname = sptr_type[:-5]
            c_type = 'vital_{}_t'.format(classname)
            return c_type

    def cxx_to_c(carg):
        # TODO: robustness
        # (mostly for ret vars binding output)
        cxx_name = '_' + carg.name
        c_name = carg.name
        if carg.is_native():
            return 'auto {} = {};'.format(c_name, cxx_name)
        elif carg.vital_c_type():
            cxx_type = carg.type.strip()
            c_type = carg.vital_c_type()
            return '{} {} = reinterpret_cast<{}>({})'.format(c_type, c_name, cxx_type, cxx_name)
        else:
            return 'REINTERP_TYPE({}, {}, {})'.format(
                carg.c_argtype(), c_name, cxx_name)

    def python_ctypes(carg):
        """
        The python ctypes type that corresponds to this C type
        """
        import ctypes

        def wrap_pointer(ctype, degree):
            for _ in range(degree):
                ctype = 'ctypes.POINTER({})'.format(ctype)
            return ctype

        base, ptr = carg.split_pointer()
        if base == 'void' and len(ptr) == 0:
            return None
        elif base == 'vital_error_handle_t':
            assert len(ptr) > 0
            ctype = wrap_pointer('VitalErrorHandle.C_TYPE_PTR', len(ptr) - 1)
            return ctype
        else:
            if hasattr(ctypes, 'c_' + base):
                ctype = wrap_pointer('ctypes.c_' + base, len(ptr))
                return ctype
            else:
                # match = re.match('vital_' + named('vt', VARNAME) + '_t' + '\s*' + named('is_const', 'const') + '?', base)
                # if match:
                #    c_class = match.groupdict()['vt']
                c_class = carg.vital_classname()
                if c_class is not None:
                    import utool as ut
                    py_class = ut.to_camel_case(c_class)
                    degree = len(ptr)
                    assert degree > 0
                    ctype = py_class + '.C_TYPE_PTR'
                    ctype = wrap_pointer(ctype, degree - 1)
                    return ctype
            raise NotImplementedError(str(carg))


@ut.reloadable_class
class CArgspec(ub.NiceRepr):
    """
    argspec = d['argspec']
    cargs = CArgspec(argspec)
    cargs.args
    """
    def __init__(cargs, text, kind='cxx'):
        cargs._str = text
        cargs.kind = kind

        text = text.replace('\n', ' ').strip()
        text = re.sub('  *', ' ', text)
        cargs._cleaned = text

        cargs.args = []
        if cargs._cleaned:
            for item in text.split(','):
                cargs.args.append(CArg.parse(item))

    def __iter__(cargs):
        return iter(cargs.args)

    def __nice__(cargs):
        return str(list(map(str, cargs.args)))

    def format_typespec_python(cargs):
        return ', '.join([carg.python_ctypes() for carg in cargs])

    def format_argspec_c(cargs):
        return ', '.join([carg.c_spec() for carg in cargs])

    def format_callargs_cxx(cargs):
        return ', '.join(['_' + carg.name for carg in cargs])

    def c_to_cxx_conversion(cargs):
        block = '\n'.join([carg.c_to_cxx() for carg in cargs])
        return block


class CXXIntrospect(object):
    """
    For the actual C++ class def

    Example:
        >>> import sys
        >>> sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings/python/vital/types')
        >>> from c_introspect import *
        >>> classname = 'oriented_bounding_box'
        >>> self = CXXIntrospect(classname)
        >>> self.parse_cxx_class()
        >>> self.dump_c_bindings()
    """
    def __init__(self, classname):
        self.classname = classname
        self.cxx_type_base = expanduser('~/code/VIAME/packages/kwiver/vital/types/')
        self.cxx_method_infos = []
        self.cxx_rel_includes = []

    def parse_cxx_class(self):
        cxx_path = join(self.cxx_type_base, self.classname + '.h')

        import ubelt as ub
        text = ub.readfrom(cxx_path)

        import re
        # Remove comments
        text = re.sub(C_SINGLE_COMMENT, '', text)
        text = re.sub(C_MULTI_COMMENT, '', text, flags=re.MULTILINE | re.DOTALL)

        flags = re.MULTILINE | re.DOTALL

        # Regex for attempting to match a cxx func
        cxx_func_def = WHITESPACE.join([
            STARTLINE + SPACE + '\\b' + named('return_type', TYPENAME),
            '\s',
            named('c_funcname', VARNAME),
            lparen,
            named('argspec', '[^-+]*?'),
            rparen,
            optional(named('is_const', 'const')),
            optional(named('is_init0', '=' + WHITESPACE + '0')),
            regex_or([
                named('semi', ';'),
                named('begin_body', rcurly),
            ]),
        ])

        # match = re.search(cxx_func_def, text, flags=flags)
        # d = match.groupdict()
        # print('match = {!r}'.format(match))

        cxx_method_infos = []
        for match in re.finditer(cxx_func_def, text, flags=flags):
            # print('match = {!r}'.format(match))
            d = match.groupdict()
            if d.get('argspec', None) is not None:
                d['argspec'] = CArgspec(d.get('argspec'), kind='cxx')
            for k, v in d.items():
                if k.startswith('is_'):
                    d[k] = v is not None
            cxx_method_infos.append(d)
        self.cxx_method_infos = cxx_method_infos
        import utool as ut
        print('cxx_method_infos = {}'.format(ut.repr4(cxx_method_infos)))

        cxx_constructor_def = WHITESPACE.join([
            STARTLINE + SPACE + '\\b' + self.classname,
            lparen,
            named('argspec', '[^-+]*?'),
            rparen,
            optional(named('initilizer', ':.*?')),
            # optional(named('is_const', 'const')),
            # optional(named('is_init0', '=' + WHITESPACE + '0')),
            regex_or([
                named('semi', ';'),
                named('begin_body', rcurly),
            ]),
        ])
        cxx_constructor_infos = []
        for match in re.finditer(cxx_constructor_def, text, flags=flags):
            # print('match = {!r}'.format(match))
            d = match.groupdict()
            if d.get('argspec', None) is not None:
                d['argspec'] = CArgspec(d.get('argspec'), kind='cxx')
            for k, v in d.items():
                if k.startswith('is_'):
                    d[k] = v is not None
            cxx_constructor_infos.append(d)
        self.cxx_constructor_infos = cxx_constructor_infos
        import utool as ut
        print('cxx_constructor_infos = {}'.format(ut.repr4(cxx_constructor_infos)))

        # Regex for attempting to match a relative header
        cxx_rel_header = WHITESPACE.join([
            '#include \"' + named('header', C_FILENAME) + '\"'
        ])
        self.cxx_rel_includes = []
        for match in re.finditer(cxx_rel_header, text, flags=flags):
            self.cxx_rel_includes.append(match.groupdict()['header'])

    def dump_c_bindings(self):
        fmtdict = {
            'c_type': 'vital_{classname}_t'.format(classname=self.classname),
            'copyright': COPYRIGHT,
            'classname': self.classname,
            'CLASSNAME': self.classname.upper()
        }

        header = ub.codeblock(
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

        has_sptr = True
        body_parts = []

        if has_sptr:
            construct_fmt = ub.codeblock(
                '''
                {c_type}*
                vital_{classname}_from_{init_name}( {c_argspec}, vital_error_handle_t *eh=NULL)
                {{
                  STANDARD_CATCH(
                    "vital_{classname}_from_{init_name}", eh,

                    // TODO: ENSURE THIS IS CORRECT
                    {c_to_cxx_conversion}

                    auto _sptr = std::make_shared< vital::{classname} >( {cxx_callargs} );
                    vital_c::{CLASSNAME}_SPTR_CACHE.store( _sptr );

                    return reinterpret_cast< {c_type}* >( _sptr.get() );

                  );
                  return NULL;
                }}
                ''')
        else:
            assert False

        for n, info in enumerate(self.cxx_constructor_infos):
            init_name = 'v{}'.format(n)

            argsepc = info['argspec']

            cxx_callargs = argsepc.format_callargs_cxx()

            c_to_cxx_conversion = ub.indent(
                argsepc.c_to_cxx_conversion(), ' ' * 4).lstrip()

            # Hack
            argsepc.args.append(
                CArg('vital_error_handle_t *', 'eh', default='NULL')
            )
            c_argspec = argsepc.format_argspec_c()

            text = construct_fmt.format(
                init_name=init_name,
                c_argspec=c_argspec,
                cxx_callargs=cxx_callargs,
                c_to_cxx_conversion=c_to_cxx_conversion,
                **fmtdict,
            )
            body_parts.append(text)

        # TODO: handle outvars
        c_bind_method = ut.codeblock(
            '''
            {c_return_type} vital_bounding_box_{c_funcname}({c_argspec})
            {{
              STANDARD_CATCH(
                "vital_bounding_box_{c_funcname}", eh,
                {c_to_cxx_conversion}
                auto _retvar = reinterpret_cast<kwiver::vital::{classname}*>(self)->{c_funcname}({cxx_callargs});
                {return_convert}
                return retvar;
              );
              return NULL;
            }}
        ''')

        for n, info in enumerate(self.cxx_method_infos):

            return_arg = CArg(info['return_type'], 'retvar')

            argsepc = info['argspec']
            cxx_callargs = argsepc.format_callargs_cxx()

            c_to_cxx_conversion = ub.indent(
                argsepc.c_to_cxx_conversion(), ' ' * 4).lstrip()

            # Hack
            argsepc.args.insert(0, CArg('{} *'.format(fmtdict['c_type']), 'self'))
            argsepc.args.append(CArg('vital_error_handle_t *', 'eh', default='NULL'))
            c_argspec = argsepc.format_argspec_c()

            text = c_bind_method.format(
                c_return_type=return_arg.c_argtype(),
                return_convert=return_arg.cxx_to_c(),
                init_name=init_name,
                c_funcname=info['c_funcname'],
                c_argspec=c_argspec,
                cxx_callargs=cxx_callargs,
                c_to_cxx_conversion=c_to_cxx_conversion,
                **fmtdict,
            )
            body_parts.append(text)

        # print(text)
        text = header + '\n\n'.join(body_parts)
        print(text)


class CBindIntrospect(object):
    """

    Example:
        >>> import sys
        >>> sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings/python/vital/types')
        >>> from c_introspect import *
        >>> classname = 'feature_set'
        >>> self = CBindIntrospect(classname)
        >>> self.parse_cxx_bindings()
    """

    def __init__(self, classname):
        self.classname = classname
        self.c_binding_base = expanduser('~/code/VIAME/packages/kwiver/vital/bindings/c/types/')
        self.cxx_method_infos = []
        self.cxx_rel_includes = []

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

            restype = CArg(method_info['return_type']).python_ctypes()
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

    def parse_cxx_bindings(self):
        """
        Make a header using the cxx impl
        """
        cxx_path = join(self.c_binding_base, self.classname + '.cxx')

        import ubelt as ub
        text = ub.readfrom(cxx_path)

        import re
        # Remove comments
        text = re.sub(C_SINGLE_COMMENT, '', text)
        text = re.sub(C_MULTI_COMMENT, '', text, flags=re.MULTILINE | re.DOTALL)

        print(text)

        flags = re.MULTILINE | re.DOTALL

        # Regex for attempting to match a cxx func
        cxx_func_def = WHITESPACE.join([
            STARTLINE + SPACE + '\\b' + named('return_type', TYPENAME),
            '\s',
            named('c_funcname', VARNAME),
            lparen,
            named('argspec', '.*?'),
            rparen,
            named('begin_body', rcurly),
            # ENDLINE
        ])

        match = re.search(cxx_func_def, text, flags=flags)
        d = match.groupdict()
        # print('match = {!r}'.format(match))

        cxx_method_infos = []
        for match in re.finditer(cxx_func_def, text, flags=flags):
            # print('match = {!r}'.format(match))
            d = match.groupdict()
            for k, v in d.items():
                if k.startswith('is_'):
                    d[k] = v is not None
            # print('d = {}'.format(ut.repr4(d)))
            cxx_method_infos.append(d)
        self.cxx_method_infos = cxx_method_infos

        # Regex for attempting to match a relative header
        cxx_rel_header = WHITESPACE.join([
            '#include \"' + named('header', C_FILENAME) + '\"'
        ])
        self.cxx_rel_includes = []
        for match in re.finditer(cxx_rel_header, text, flags=flags):
            self.cxx_rel_includes.append(match.groupdict()['header'])

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
    pass


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
        optional(named('is_const', 'const')),
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
