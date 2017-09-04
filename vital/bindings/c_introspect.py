from os.path import expanduser, join
import re
import utool as ut
import ubelt as ub
from c_patterns import CPatternMatch, CArgspec, CArg, CType
from c_patterns import named, VARNAME
import fmt_templates

BLANK_LINE_PLACEHOLDER = '// NOOP(BLANK_LINE)'


class TypeRegistry(object):
    mappings = {
        'vector_t': CType('double *'),
        'std::string': CType('char*'),
    }


class VitalRegistry(object):
    sptr_caches = {
        'image_container': 'IMGC_SPTR_CACHE',
        'feature': 'FEATURE_SPTR_CACHE',
        'detected_object': 'DOBJ_SPTR_CACHE',
        'detected_object_type': 'DOT_SPTR_CACHE',
    }

    #
    copy_on_set = {
        # 'detected_object_type'
    }

    @staticmethod
    def get_sptr_cachename(classname):
        default = '_' + classname.upper() + 'SPTR_CACHE'
        base_cachename = VitalRegistry.sptr_caches.get(classname, default)
        return 'kwiver::vital_c::' + base_cachename

    vital_types = {
        'bounding_box',
        'bounding_box_d',
        'detected_object_type',
    }

    special_cxx_to_c = {
        'bounding_box_d': 'vital_bounding_box_t*',
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

    def __init__(carg, *args, **kwargs):
        carg.check_null = kwargs.get('check_null', True)
        carg.use_default = kwargs.get('use_default', False)
        super(VitalCArg, carg).__init__(*args, **kwargs)

    def is_smart(carg):
        return carg.type.data_base.endswith('_sptr')

    def c_spec(carg):
        argtype = carg.c_type()
        if not carg.use_default or carg.default is None:
            return '{} {}'.format(argtype, carg.name)
        else:
            return '{} {}={}'.format(argtype, carg.name, carg.default)

    def c_type(carg):
        """
        Converts this C++ type to its corresponding C type
        """
        data_base = carg.type.data_base
        ptr_degree = carg.type.ptr_degree + carg.type.ref_degree
        if data_base.endswith('_sptr'):
            ptr_degree += 1
            data_base = data_base[:-5]
        if data_base in TypeRegistry.mappings:
            return TypeRegistry.mappings[data_base]
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

    def c_to_cxx(carg, check_null=None):
        """
        Used for transforming (typically an argument) from C to C++
        """
        if check_null is None:
            check_null = carg.check_null

        data_base = carg.type.data_base

        fmtdict = {}
        fmtdict['c_name'] = carg.name
        fmtdict['cxx_name'] = carg.cxx_name()
        cxx_ns = 'kwiver::vital::'
        # c_ns = 'kwiver::vital_c::'

        # print('carg = {!r}'.format(carg))
        # print('carg.type.is_native = {!r}'.format(carg.type.is_native()))
        if carg.type.is_native():
            # text = '{} {} = {};'.format(carg.type, cxx_name, c_name)
            text = BLANK_LINE_PLACEHOLDER
        elif carg.is_smart():
            pointed_type = data_base[:-5]

            if pointed_type in VitalRegistry.copy_on_set:
                fmtdict['cxx_type1'] = CType(cxx_ns + pointed_type)
                fmtdict['cxx_type2'] = fmtdict['cxx_type1'].addr()
                # Construct a new smart pointer
                text = ub.codeblock(
                    '''
                    auto {cxx_name} = std::make_shared< {cxx_type1} >(
                        * reinterpret_cast< {cxx_type2} >({c_name}) );
                    '''
                ).format(**fmtdict)

            else:
                # Lookup in existing smart pointer cache
                fmtdict['SPTR_CACHE'] = VitalRegistry.get_sptr_cachename(
                    pointed_type)
                fmtdict['cxx_type'] = cxx_ns + str(carg.type)

                if check_null:
                    text = ub.codeblock(
                        '''
                        {cxx_type} {cxx_name};
                        if( {c_name} != NULL )
                        {{
                          {cxx_name} = {SPTR_CACHE}.get( {c_name} );
                        }}
                        '''
                    ).format(**fmtdict)
                else:
                    text = ub.codeblock(
                        '''
                        {cxx_type} {cxx_name} = {SPTR_CACHE}.get( {c_name} );
                        '''
                    ).format(**fmtdict)
        # print('CASTING TO CXX carg.type_ = {!r}'.format(carg.type_))
        # print('base = {!r}'.format(base))
        # print('carg._orig_text = {!r}'.format(carg._orig_text))
        elif data_base in VitalRegistry.reinterpretable:
            # print('carg = {!r}'.format(carg))
            # print('carg.c_type = {!r}'.format(carg.c_type))
            cxx_type = carg.type.data_base
            ptr_degree = carg.type.ptr_degree + carg.type.ref_degree
            fmtdict['cxx_type1'] = (cxx_ns + cxx_type +
                                    '*' * carg.type.ptr_degree +
                                    '&' * carg.type.ref_degree)
            fmtdict['cxx_type2'] = cxx_ns + cxx_type + '*' * ptr_degree
            text = ('{cxx_type1} {cxx_name} = '
                    '*reinterpret_cast< {cxx_type2} >({c_name});'.format(**fmtdict))
        elif data_base == 'std::string':
            fmtdict['cxx_type'] = carg.type.data_base
            text = ('{cxx_type} {cxx_name}({c_name});'.format(**fmtdict))
        else:
            fmtdict['c_type'] = carg.c_type()
            text = 'NOT_IMPLEMENTED({c_type}, {cxx_name}, {c_name});'.format(**fmtdict)
        # print(text)
        # print()
        return text

    def cxx_to_c(carg):
        """
        Used for transforming (generally a return value) from C++ to C.
        """
        print('carg = {!r}'.format(carg))

        cxx_name = carg.cxx_name()
        c_name = carg.name

        cxx_ns = 'kwiver::vital::'
        fmtdict = {
            'cxx_name': cxx_name,
            'c_name': c_name,
        }

        if carg.type.is_native():
            # text = ub.codeblock(
            #     '''
            #     // DEBUG(cxx-to-c noop)
            #     auto {c_name} = {cxx_name};
            #     '''
            # )
            text = BLANK_LINE_PLACEHOLDER
        elif carg.is_smart():
            sptr_type = carg.type.data_base.split('::')[-1]
            classname = sptr_type[:-5]
            fmtdict.update({
                'c_type': 'vital_{}_t*'.format(classname)
            })
            text = ub.codeblock(
                '''
                // DEBUG(cxx-to-c smart-pointer)
                {c_type} {c_name} = reinterpret_cast< {c_type} >( {cxx_name}.get() );
                '''
            ).format(**fmtdict)
        elif carg.type.data_base in VitalRegistry.reinterpretable:
            # Copy and reinteperet
            # Ensure this always works with vital_detected_object_bounding_box
            # cxx_type1 = CType(cxx_ns + 'bounding_box_d*')
            cxx_type1 = CType(cxx_ns + str(carg.type.addr()) )
            cxx_type2 = cxx_type1.dref()
            fmtdict.update({
                'cxx_type1': str(cxx_type1),
                'cxx_type2': str(cxx_type2),
                'c_type': carg.c_type(),
                # + '==' +'vital_bounding_box_t*',
            })
            text = ub.codeblock(
                '''
                // DEBUG(cxx-to-c reinterpretable)
                {cxx_type1} {cxx_name}_copy = new {cxx_type2}( {cxx_name} )
                {c_type} {c_name} = *reinterpret_cast< {c_type} >( {cxx_name}_copy );
                ''').format(**fmtdict)
        elif carg.type.data_base == 'std::string':
            text = ub.codeblock(
                '''
                // DEBUG(cxx-to-c std::string)
                // The caller must not forget to free this str
                char *{c_name} = malloc(sizeof(char) * ({cxx_name}.length() + 1));
                strcpy({c_name}, {cxx_name}.c_str());
                ''').format(**fmtdict)
        else:
            fmtdict['c_type'] = carg.c_type()
            text = ub.codeblock(
                '''
                // DEBUG(cxx-to-c not-implemented)
                NOT_IMPLEMENTED({c_type}, {c_name}, {cxx_name})
                '''
            ).format(**fmtdict)
        return text

    def vital_classname(carg):
        base = carg.type.data_base
        match = re.match('vital_' + named('vt', VARNAME) + '_t', base)
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
        print('base = {!r}'.format(base))
        ptr_degree = carg.type.ptr_degree

        if base == 'void' and ptr_degree == 0:
            return None
        elif base == 'vital_error_handle_t':
            assert ptr_degree > 0
            ctype = wrap_pointer('VitalErrorHandle.C_TYPE_PTR', ptr_degree - 1)
            return ctype
        else:
            if base.endswith('_t') and hasattr(ctypes, 'c_' + base[:-2]):
                ctype = wrap_pointer('ctypes.c_' + base[:-2], ptr_degree)
                return ctype
            if hasattr(ctypes, 'c_' + base):
                ctype = wrap_pointer('ctypes.c_' + base, ptr_degree)
                return ctype
            else:
                c_class = carg.vital_classname()
                if c_class is not None:
                    py_class = ut.to_camel_case(c_class)
                    assert ptr_degree > 0
                    ctype = py_class + '.C_TYPE_PTR'
                    ctype = wrap_pointer(ctype, ptr_degree - 1)
                    return ctype
            raise NotImplementedError('ctypes parsing for {}'.format(carg))


CArgspec._CARG = VitalCArg


def inspect_existing_bindings(classname):

    cxxtype = VitalTypeIntrospectCxx(classname)
    cxxtype.parse_cxx_class_header()

    cbind = VitalTypeIntrospectCBind(classname)
    cbind.parse_c_class_bindings()

    def cxx_funcname(info):
        prefix = 'vital_{}_'.format(info.classname)
        funcname = info.info['cxx_funcname']
        if funcname.startswith(prefix):
            return funcname[len(prefix):]
        else:
            return funcname

    cxx_funcnames = {cxx_funcname(info) for info in cxxtype.cxx_method_infos}
    bound_funcnames = {cxx_funcname(info) for info in cbind.cxx_method_infos}

    print('cxx_funcnames = {}'.format(ut.repr4(sorted(cxx_funcnames))))
    print('bound_funcnames = {}'.format(ut.repr4(sorted(bound_funcnames))))

    unbound_funcs = cxx_funcnames.difference(bound_funcnames)
    print('unbound_funcs = {!r}'.format(unbound_funcs))

    nonstandard_bindings = bound_funcnames.difference(cxx_funcnames)
    print('nonstandard_bindings = {!r}'.format(nonstandard_bindings))


def DETECTED_OBJECT_WIP():
    """
    import sys
    sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings')
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

    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/VIAME/packages/kwiver/vital/bindings
        python -m c_introspect VitalTypeIntrospectCxx:0 --class=detected_object

    Example:
        >>> import sys
        >>> sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings')
        >>> from c_introspect import *
        >>> #classname = 'oriented_bounding_box'
        >>> classname = ub.argval('--class', default='detected_object')
        >>> self = VitalTypeIntrospectCxx(classname)
        >>> self.parse_cxx_class_header()
        >>> text = self.dump_c_bindings()
        >>> print(ub.highlight_code(text, 'cpp'))
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
            'copyright': fmt_templates.COPYRIGHT,
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
            text = self.autogen_vital_init_c(n, info, fmtdict)
            parts.append(text)

        if self.cxx_constructor_infos:
            parts.append(ut.codeblock(
                '''
                // --- METHODS ---
                '''))

        only_funcnames = {
            # 'bounding_box',
            # 'set_bounding_box',
            # 'set_detector_name',
            # 'detector_name',
            # 'type',
            # 'set_type',
            'mask',
            'set_mask',
            # 'confidence',
            # 'set_confidence',
        }

        for n, info in enumerate(self.cxx_method_infos):
            if only_funcnames is None or info['cxx_funcname'] in only_funcnames:
                text = self.autogen_vital_method_c(info, fmtdict)
                parts.append(text)

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

    def autogen_vital_init_c(self, n, info, fmtdict):
        fmtdict = fmtdict.copy()

        init_name = 'v{}'.format(n)

        c_funcname = 'vital_{classname}_from_{init_name}'.format(
            classname=self.classname, init_name=init_name)

        fmtdict['cxx_type'] = 'kwiver::vital::' + self.classname

        call_cxx_func_fmt = ub.codeblock(
            '''
            auto _retvar = std::make_shared< {cxx_type} >( {cxx_callargs} );
            {SPTR_CACHE}.store( _retvar );
            '''
        )

        fmtdict['SPTR_CACHE'] = VitalRegistry.get_sptr_cachename(self.classname)
        ret_type = CType(info['return_type'])
        info.info['return_type'] = ret_type.data_base + '_sptr'

        text = self.autogen_vital_method_c(
            info, fmtdict, c_funcname=c_funcname,
            call_cxx_func_fmt=call_cxx_func_fmt, needs_self=False
        )
        return text

    def autogen_vital_method_c(self, info, fmtdict, c_funcname=None,
                               call_cxx_func_fmt=None, needs_self=True):
        # TODO: handle outvars
        c_bind_method = ut.codeblock(
            '''
            {c_return_type}
            {c_funcname}( {c_argspec} )
            {LCURLY}
              STANDARD_CATCH("{c_funcname}", eh,
                {method_body}
              );
              {return_error}
            {RCURLY}
            ''')

        c_bind_method_body = ub.codeblock(
            '''
            REM // --- Convert C arguments to C++ ---
            {convert_cxx_to_c}
            REM // --- Call C++ function ---
            {call_cxx_func}
            REM // --- Convert C++ return value to C ---
            {convert_return}
            {return_c_var}
            ''')

        def block_indent(block, n=4):
            # indents all lines but the first (so fmtstrings work)
            return ub.indent(block, ' ' * n).lstrip()

        fmtdict = fmtdict.copy()
        fmtdict['LCURLY'] = '{'
        fmtdict['RCURLY'] = '}'

        return_arg = VitalCArg(info['return_type'], 'retvar')
        returns_none = (return_arg.type == 'void')

        argsepc = info['argspec']
        fmtdict['cxx_callargs'] = argsepc.format_callargs_cxx()
        fmtdict['cxx_funcname'] = info['cxx_funcname']

        if c_funcname is None:
            c_funcname = 'vital_{classname}_{cxx_funcname}'.format(**fmtdict)
        fmtdict['c_funcname'] = c_funcname

        if needs_self:
            self_cxx_arg = VitalCArg(fmtdict['classname'] + '_sptr', 'self')
            self_cxx_arg.check_null = False
            argsepc.args.insert(0, self_cxx_arg)

        convert_cxx_to_c = '\n'.join(
            [str(carg.c_to_cxx()) for carg in argsepc.args])

        # Hack: add in error handling
        error_handling = True
        if error_handling:
            eh = VitalCArg('vital_error_handle_t *', 'eh', default='NULL')
            eh.use_default = True
            argsepc.args.append(eh)

        c_argspec = ', '.join([carg.c_spec() for carg in argsepc.args])
        if returns_none:
            convert_return = BLANK_LINE_PLACEHOLDER
            return_c_var = BLANK_LINE_PLACEHOLDER
            return_error = BLANK_LINE_PLACEHOLDER
        else:
            convert_return = return_arg.cxx_to_c()
            return_c_var = 'return retvar;'
            return_error = 'return NULL;'

        if call_cxx_func_fmt is None:
            call_cxx_func = '_self->{cxx_funcname}({cxx_callargs});'.format(**fmtdict)
            if not returns_none:
                cxx_ret_name = return_arg.cxx_name()
                call_cxx_func = 'auto ' + cxx_ret_name + ' = ' + call_cxx_func
        else:
            call_cxx_func = call_cxx_func_fmt.format(**fmtdict)

        method_body = c_bind_method_body.format(
            convert_return=convert_return,
            return_c_var=return_c_var,
            call_cxx_func=call_cxx_func,
            convert_cxx_to_c=convert_cxx_to_c,
            **fmtdict,
        )

        text = c_bind_method.format(
            c_argspec=c_argspec,
            c_return_type=return_arg.c_type(),
            return_error=return_error,
            method_body=block_indent(method_body, 4),
            **fmtdict,
        )
        return self._postprocess(text)

    @staticmethod
    def _postprocess(text):
        text = '\n'.join([
            line for line in text.split('\n')
            if (BLANK_LINE_PLACEHOLDER not in line and
                not line.lstrip().startswith('REM') and
                not line.lstrip().startswith('// DEBUG(')
                )
        ])
        return text


class VitalTypeIntrospectCBind(object):
    """

    Example:
        >>> import sys
        >>> sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings')
        >>> from c_introspect import *
        >>> classname = ub.argval('--class', default='feature_set')
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
        """
        CommandLine:
            export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/VIAME/packages/kwiver/vital/bindings
            python -m c_introspect VitalTypeIntrospectCBind.dump_c_header:0 --class=detected_object

        Example:
            >>> from c_introspect import *
            >>> classname = ub.argval('--class', default='feature_set')
            >>> self = VitalTypeIntrospectCBind(classname)
            >>> self.parse_c_class_bindings()
            >>> self.dump_c_header()
        """
        method_fmtstr = ub.codeblock(
            '''
            VITAL_C_EXPORT
            {return_type} {cxx_funcname}({argspec});
            ''')

        fmtdict = dict(
            classname=self.classname,
            CLASSNAME=self.classname.upper()
        )

        methods = []
        for method_info in self.cxx_method_infos:
            d = fmtdict.copy()
            d.update(method_info.info)
            # d['argspec'] = d['argspec'].replace('\n', ' ')
            # d['argspec'] = re.sub('  *', ' ', d['argspec'])
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
        d['copyright'] = fmt_templates.COPYRIGHT
        autogen_text = body_fmtstr.format(**d)

        print(autogen_text)

        # autogen_fpath = join(self.c_binding_base, self.classname + '.h.autogen')
        autogen_fpath = join(self.c_binding_base, self.classname + '.h')

        # import utool as ut
        # ut.dump_autogen_code(autogen_fpath, autogen_text, codetype='c', show_diff=True)
        # ut.dump_autogen_code(autogen_fpath, autogen_text, codetype='c', dowrite=True)

        ub.writeto(autogen_fpath, autogen_text)

    def dump_python_ctypes(self):
        """
        CommandLine:
            export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/VIAME/packages/kwiver/vital/bindings
            python -m c_introspect VitalTypeIntrospectCBind.dump_python_ctypes:0 --class=detected_object

        Example:
            >>> from c_introspect import *
            >>> classname = ub.argval('--class', default='feature_set')
            >>> self = VitalTypeIntrospectCBind(classname)
            >>> self.parse_c_class_bindings()
            >>> self.dump_python_ctypes()
        """
        blocks = []
        for method_info in self.cxx_method_infos:

            cxx_funcname = method_info['cxx_funcname']
            endre = re.compile('vital_' + self.classname + '_' + named('suffix', VARNAME))
            match = endre.match(cxx_funcname)
            if match:
                suffix = match.groupdict()['suffix']
            else:
                suffix = cxx_funcname

            cargs = method_info['argspec']
            # print('')
            cxx_funcname = method_info['cxx_funcname']
            # print('cxx_funcname = {!r}'.format(cxx_funcname))

            return_arg = VitalCArg(method_info['return_type'])
            restype = return_arg.python_ctypes()
            # print('restype = {!r}'.format(restype))

            argtypes = '[' + cargs.format_typespec_python() + ']'
            # print('argtypes = {!r}'.format(argtypes))

            block = ub.codeblock(
                r'''
                C.{suffix} = VITAL_LIB.{cxx_funcname}
                C.{suffix}.argtypes = {argtypes}
                C.{suffix}.restype = {restype}
                ''').format(
                    suffix=suffix,
                    cxx_funcname=cxx_funcname,
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

if __name__ == '__main__':
    r"""
    CommandLine:
        python -m vital.types.c_introspect
    """
    ub.doctest_package()
    # import pytest
    # pytest.main([__file__, '--doctest-modules'])
