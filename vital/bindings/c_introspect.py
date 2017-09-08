"""
To generate bindings for a type:

    Need to make .cxx, .h, and .hxx c bindings in:
        ~/code/VIAME/packages/kwiver/vital/bindings/c/types

        # and add them to cmake lists
        ~/code/VIAME/packages/kwiver/vital/bindings/c/types/CMakeLists.txt

    Need to make .py bindings in:
        ~/code/VIAME/packages/kwiver/vital/bindings/python/vital/types


    Need to define type converters:

        ~/code/VIAME/packages/kwiver/sprokit/processes/bindings/c/vital_type_converters.cxx
        ~/code/VIAME/packages/kwiver/sprokit/processes/bindings/c/vital_type_converters.h
        ~/code/VIAME/packages/kwiver/sprokit/processes/bindings/python/kwiver/util/vital_type_converters.py

    Need to register type converters:

        ~/code/VIAME/packages/kwiver/sprokit/processes/kwiver_type_traits.h
        ~/code/VIAME/packages/kwiver/sprokit/processes/bindings/python/kwiver/kwiver_process.py
"""

from os.path import expanduser, join
import re
import ubelt as ub
from c_patterns import CPatternMatch, CArgspec, CArg, CType
from c_patterns import named, VARNAME
import fmt_templates

BLANK_LINE_PLACEHOLDER = '// NOOP(BLANK_LINE)'


class TypeRegistry(object):
    mappings = {
        'vector_t': CType('double*'),
        'std::string': CType('char*'),
        'vector_3d': CType('vital_eigen_matrix3x1d_t*'),
        'covariance_3d':  CType('vital_covariance_3d_t*'),
        'rotation_d': CType('vital_rotation_d_t*')
    }


class VitalRegistry(object):
    sptr_caches = {
        'image_container': 'IMGC_SPTR_CACHE',
        'feature': 'FEATURE_SPTR_CACHE',
        'detected_object': 'DOBJ_SPTR_CACHE',
        'detected_object_type': 'DOT_SPTR_CACHE',
        'camera': 'CAMERA_SPTR_CACHE',
    }

    #
    copy_on_set = {
        # 'detected_object_type'
    }

    @staticmethod
    def get_sptr_cachename(cxx_classname):
        default = '_' + cxx_classname.upper() + '_SPTR_CACHE'
        base_cachename = VitalRegistry.sptr_caches.get(cxx_classname, default)
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
        'vector_3d',
        'covariance_3d',
        'rotation_d',
    }


class VitalCArg(CArg):

    def __init__(carg, *args, **kwargs):
        carg.check_null = kwargs.get('check_null', True)
        carg.use_default = kwargs.get('use_default', False)
        super(VitalCArg, carg).__init__(*args, **kwargs)

    def is_smart(carg):
        return carg.type.data_base.endswith('_sptr')

    def smart_type(carg):
        if carg.is_smart():
            sptr_type = carg.type.data_base.split('::')[-1]
            pointed_type = sptr_type[:-5]
            return pointed_type
        else:
            return None

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
            pointed_type = carg.smart_type()

            if pointed_type in VitalRegistry.copy_on_set:
                # I dont think this is used anymore (or at least should be)
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
            pointed_type = carg.smart_type()
            fmtdict.update({
                'c_type': 'vital_{}_t*'.format(pointed_type)
            })
            text = ub.codeblock(
                '''
                // DEBUG(cxx-to-c smart-pointer)
                {c_type} {c_name} = reinterpret_cast< {c_type} >( {cxx_name}.get() );
                '''
            ).format(**fmtdict)
        elif carg.type.data_base in VitalRegistry.reinterpretable:
            """
            Test With:
                python -m c_introspect VitalTypeIntrospectCxx:0 --class=camera  --func=get_rotation
                python -m c_introspect VitalTypeIntrospectCxx:0 --class=detected_object  --func=bounding_box,set_bounding_box
            """


            # Copy and reinteperet
            # Ensure this always works with vital_detected_object_bounding_box
            # cxx_type1 = CType(cxx_ns + 'bounding_box_d*')
            cxx_type = CType(cxx_ns + str(carg.type))
            cxx_type1 = cxx_type.copy().addr().no_ref()
            cxx_type2 = cxx_type1.dref().no_modifiers()

            fmtdict.update({
                'cxx_type1': str(cxx_type1),
                'cxx_type2': str(cxx_type2),
                'c_type': carg.c_type(),
                # + '==' +'vital_bounding_box_t*',
            })
            # text = ub.codeblock(
            #     '''
            #     // DEBUG(cxx-to-c reinterpretable)
            #     {c_type} {c_name} = *reinterpret_cast< {c_type} >( new {cxx_type2}( {cxx_name} ) );
            #     ''').format(**fmtdict)
            text = ub.codeblock(
                '''
                // DEBUG(cxx-to-c reinterpretable)
                {cxx_type1} {cxx_name}_copy = new {cxx_type2}( {cxx_name} )
                {c_type} {c_name} = reinterpret_cast< {c_type} >( {cxx_name}_copy );
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
                    import utool as ut
                    py_classname = ut.to_camel_case(c_class)
                    assert ptr_degree > 0
                    ctype = py_classname + '.C_TYPE_PTR'
                    ctype = wrap_pointer(ctype, ptr_degree - 1)
                    return ctype
            raise NotImplementedError('ctypes parsing for {}'.format(carg))


CArgspec._CARG = VitalCArg


def inspect_existing_bindings(cxx_classname):

    cxxtype = VitalTypeIntrospectCxx(cxx_classname)
    cxxtype.parse_cxx_class_header()

    cbind = VitalTypeIntrospectCBind(cxx_classname)
    cbind.parse_c_class_bindings()

    def cxx_funcname(info):
        prefix = 'vital_{}_'.format(info.cxx_classname)
        funcname = info.info['cxx_funcname']
        if funcname.startswith(prefix):
            return funcname[len(prefix):]
        else:
            return funcname

    cxx_funcnames = {cxx_funcname(info) for info in cxxtype.cxx_method_infos}
    bound_funcnames = {cxx_funcname(info) for info in cbind.cxx_method_infos}

    import utool as ut
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
    #cxx_classname = 'oriented_bounding_box'
    cxx_classname = 'detected_object'


    cxxtype = VitalTypeIntrospectCxx(cxx_classname)
    cxxtype.parse_cxx_class_header()
    text = cxxtype.dump_c_bindings()
    print(ub.highlight_code(text, 'cxx'))

    cbind = VitalTypeIntrospectCBind(cxx_classname)
    cbind.parse_c_class_bindings()

    inspect_existing_bindings(cxx_classname)
    """


class VitalTypeIntrospectCxx(object):
    """
    For the actual C++ class def

    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/VIAME/packages/kwiver/vital/bindings
        python -m c_introspect VitalTypeIntrospectCxx:0 --class=detected_object
        python -m c_introspect VitalTypeIntrospectCxx:0 --class=detected_object --func=mask

        python -m c_introspect VitalTypeIntrospectCxx:0 --class=camera

    Example:
        >>> import sys
        >>> sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings')
        >>> from c_introspect import *
        >>> #cxx_classname = 'oriented_bounding_box'
        >>> cxx_classname = ub.argval('--class', default='detected_object')
        >>> funcnames = ub.argval('--func', default=None)
        >>> self = VitalTypeIntrospectCxx(cxx_classname)
        >>> self.parse_cxx_class_header()
        >>> text = self.dump_c_bindings(funcnames)
        >>> print(ub.highlight_code(text, 'cpp'))
    """
    def __init__(self, cxx_classname):
        self.cxx_classname = cxx_classname
        self.cxx_type_base = expanduser('~/code/VIAME/packages/kwiver/vital/types/')
        self.cxx_method_infos = []
        self.cxx_rel_includes = []

    def parse_cxx_class_header(self):
        cxx_path = join(self.cxx_type_base, self.cxx_classname + '.h')

        text = ub.readfrom(cxx_path)

        # Remove comments
        text = CPatternMatch.strip_comments(text)
        self.cxx_constructor_infos = CPatternMatch.constructors(text, self.cxx_classname)
        self.cxx_method_infos = CPatternMatch.func_declarations(text, self.cxx_classname)
        self.cxx_rel_includes = CPatternMatch.relative_includes(text)

    def dump_c_bindings(self, funcnames=None):
        fmtdict = {
            'c_type': 'vital_{cxx_classname}_t'.format(cxx_classname=self.cxx_classname),
            'copyright': fmt_templates.COPYRIGHT,
            'cxx_classname': self.cxx_classname,
            'CXX_CLASSNAME': self.cxx_classname.upper()
        }

        sptr_header = self.autogen_vital_header_c(fmtdict)

        parts = [sptr_header]
        parts = []

        if funcnames is not None:
            funcnames = set([p.strip()
                             for p in funcnames.split(',') if p.strip()])

        init_parts = []
        for n, info in enumerate(self.cxx_constructor_infos):
            if funcnames is None or '__init__' in funcnames:
                text = self.autogen_vital_init_c(n, info, fmtdict)
                init_parts.append(text)
        if init_parts:
            parts += [ub.codeblock(
                '''
                // --- CONSTRUCTORS ---
                ''')] + init_parts

        method_parts = []
        for n, info in enumerate(self.cxx_method_infos):
            if funcnames is None or info['cxx_funcname'] in funcnames:
                text = self.autogen_vital_method_c(info, fmtdict)
                method_parts.append(text)
        if method_parts:
            parts += [ub.codeblock(
                '''
                // --- METHODS ---
                ''')] + method_parts

        sptr_conversions = self.autogen_vital_sptr_conversions(fmtdict)

        if sptr_conversions:
            parts += [ub.codeblock(
                '''
                // --- SMART POINTER CONVERSIONS ---
                ''')] + sptr_conversions

        # print(text)
        text = '\n\n\n'.join(parts)
        return text

    def autogen_vital_sptr_conversions(self, fmtdict):
        fmtdict = fmtdict.copy()
        fmtdict['c_type'] = fmtdict['c_type'] + '*'
        fmtdict['sptr_type'] = 'kwiver::vital::' + fmtdict['cxx_classname'] + '_sptr'
        fmtdict['SPTR_CACHE'] = VitalRegistry.get_sptr_cachename(fmtdict['cxx_classname'])

        sptr_conversions = []

        sptr_conversions += [
            fmt_templates.VITAL_BINDING_FROM_SPTR_CONVERSION.format(**fmtdict)
        ]

        sptr_conversions += [
            fmt_templates.VITAL_BINDING_TO_SPTR_CONVERSION.format(**fmtdict)
        ]

        if True:
            # HACK: this part belongs in a different file
            # the
            import utool as ut
            fmtdict['py_classname'] = ut.to_camel_case(fmtdict['cxx_classname'])
            fmtdict['brief_doc'] = 'TODO: parse and insert brief class description'

            sptr_conversions += [ub.codeblock(
                '''
                // ----
                // PUT INTO kwiver/sprokit/processes/bindings/c/vital_type_converters.cxx

                #include <vital/types/{cxx_classname}.h>
                #include <vital/bindings/c/types/{cxx_classname}.hxx>

                VITAL_FROM_DATUM({cxx_classname}, {sptr_type}, {c_type})
                VITAL_TO_DATUM(  {cxx_classname}, {sptr_type}, {c_type})

                // ----
                // PUT INTO kwiver/sprokit/processes/bindings/c/vital_type_converters.h

                #include <vital/bindings/c/types/{cxx_classname}.h>

                VITAL_TYPE_CONVERTERS_EXPORT
                {c_type} vital_{cxx_classname}_from_datum( PyObject* args );

                VITAL_TYPE_CONVERTERS_EXPORT
                PyObject* vital_{cxx_classname}_to_datum( {c_type} handle );

                // ----
                // PUT INTO ~/code/VIAME/packages/kwiver/sprokit/processes/kwiver_type_traits.h

                #include <vital/types/{cxx_classname}.h>


                create_type_trait( {cxx_classname}, "kwiver:{cxx_classname}", {sptr_type} );
                create_port_trait( {cxx_classname}, {cxx_classname}, "{brief_doc}" );

                ''').format(**fmtdict)
            ]

            print(ub.highlight_code(ub.codeblock(
                '''
                // ----
                // PUT INTO ~/code/VIAME/packages/kwiver/sprokit/processes/bindings/python/kwiver/util/vital_type_converters.py

                from vital.types import {py_classname}

                def _convert_{cxx_classname}_in(datum_ptr):
                    """
                    Convert datum as PyCapsule to {cxx_classname} opaque handle.
                    """
                    _VCL = find_vital_library.find_vital_type_converter_library()
                    # Convert from datum to opaque handle.
                    func = _VCL.vital_{cxx_classname}_from_datum
                    func.argtypes = [ctypes.py_object]
                    func.restype = {py_classname}.C_TYPE_PTR
                    # get opaque handle from the datum
                    handle = func(datum_ptr)

                    # convert handle to python object - from c-ptr
                    py_ic_obj = {py_classname}(None, handle)

                    return py_ic_obj


                def _convert_{cxx_classname}_out(handle):
                    """
                    Convert datum as PyCapsule from {cxx_classname} opaque handle.
                    """
                    _VCL = find_vital_library.find_vital_type_converter_library()
                    # convert opaque handle to datum (as PyCapsule)
                    func =  _VCL.vital_{cxx_classname}_to_datum
                    func.argtypes = [ {py_classname}.C_TYPE_PTR ]
                    func.restype = ctypes.py_object
                    retval = func(handle)
                    return retval

                // ----
                // PUT INTO ~/code/VIAME/packages/kwiver/sprokit/processes/bindings/python/kwiver/kwiver_process.py

                self.add_type_trait('{cxx_classname}', 'kwiver:{cxx_classname}',
                                    VTC._convert_{cxx_classname}_in,
                                    VTC._convert_{cxx_classname}_out)

                self.add_port_trait("{cxx_classname}", "{cxx_classname}", "{brief_doc}")



                ''').format(**fmtdict)))

        return sptr_conversions

    def autogen_vital_header_c(self, fmtdict):
        sptr_header = ub.codeblock(
            '''
            {copyright}

            #include "{cxx_classname}.h"
            #include <vital/types/{cxx_classname}.h>
            #include <vital/bindings/c/helpers/c_utils.h>

            namespace kwiver {{
            namespace vital_c {{

            // Allocate our shared pointer cache object
            SharedPointerCache< kwiver::vital::{cxx_classname}, {c_type}>
              {CXX_CLASSNAME}_SPTR_CACHE( "{cxx_classname}" );

            }} }}

            using namespace kwiver;

            ''').format(**fmtdict)
        return sptr_header

    def autogen_vital_init_c(self, n, info, fmtdict):
        fmtdict = fmtdict.copy()

        init_name = 'v{}'.format(n)

        c_funcname = 'vital_{cxx_classname}_from_{init_name}'.format(
            cxx_classname=self.cxx_classname, init_name=init_name)

        # fmtdict['cxx_type'] = 'kwiver::vital::' + self.cxx_classname

        ret_type = CType(info['return_type'])
        info.info['return_type'] = ret_type.data_base + '_sptr'

        text = self.autogen_vital_method_c(
            info, fmtdict, c_funcname=c_funcname,
            is_constructor=True, needs_self=False
        )
        return text

    def autogen_vital_method_c(self, info, fmtdict, c_funcname=None,
                               is_constructor=False, needs_self=True):
        # TODO: handle outvars
        c_bind_method = ub.codeblock(
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
            c_funcname = 'vital_{cxx_classname}_{cxx_funcname}'.format(**fmtdict)
        fmtdict['c_funcname'] = c_funcname

        if needs_self:
            self_cxx_arg = VitalCArg(fmtdict['cxx_classname'] + '_sptr', 'self')
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

        # if call_cxx_func_fmt is None:
        if is_constructor:
            cxx_ns = 'kwiver::vital::'
            fmtdict['cxx_pointed_type'] = cxx_ns + str(return_arg.smart_type())
            call_cxx_func = 'std::make_shared< {cxx_pointed_type} >( {cxx_callargs} );'.format(**fmtdict)
        else:
            call_cxx_func = '_self->{cxx_funcname}({cxx_callargs});'.format(**fmtdict)
        if not returns_none:
            cxx_ret_name = return_arg.cxx_name()
            cxx_ret_type = 'auto'
            cxx_ns = 'kwiver::vital::'
            cxx_ret_type = cxx_ns + str(return_arg.type)
            call_cxx_func = '{} {} = {}'.format(cxx_ret_type, cxx_ret_name,
                                                call_cxx_func)
            if return_arg.is_smart():
                # Make sure the external refcount is increased whenever we
                # return a smart pointer from the C-API.
                pointed_type = return_arg.smart_type()
                SPTR_CACHE = VitalRegistry.get_sptr_cachename(
                    pointed_type)
                call_cxx_func += '\n{SPTR_CACHE}.store( {cxx_name} );'.format(
                    SPTR_CACHE=SPTR_CACHE, cxx_name=cxx_ret_name
                )
        # else:
        #     call_cxx_func = call_cxx_func_fmt.format(**fmtdict)

        method_body = c_bind_method_body.format(
            convert_return=convert_return,
            return_c_var=return_c_var,
            call_cxx_func=call_cxx_func,
            convert_cxx_to_c=convert_cxx_to_c,
            **fmtdict
        )

        text = c_bind_method.format(
            c_argspec=c_argspec,
            c_return_type=return_arg.c_type(),
            return_error=return_error,
            method_body=block_indent(method_body, 4),
            **fmtdict
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
        >>> cxx_classname = ub.argval('--class', default='feature_set')
        >>> self = VitalTypeIntrospectCBind(cxx_classname)
        >>> self.parse_c_class_bindings()
    """

    def __init__(self, cxx_classname):
        self.cxx_classname = cxx_classname
        self.c_binding_base = expanduser('~/code/VIAME/packages/kwiver/vital/bindings/c/types/')
        self.cxx_method_infos = []
        self.cxx_rel_includes = []

    def parse_c_class_bindings(self):
        """
        Make a header using the cxx impl
        """
        cxx_path = join(self.c_binding_base, self.cxx_classname + '.cxx')

        text = ub.readfrom(cxx_path)

        text = CPatternMatch.strip_comments(text)
        self.cxx_method_infos = CPatternMatch.func_definitions(text, self.cxx_classname)
        self.cxx_rel_includes = CPatternMatch.relative_includes(text)

    def dump_c_header(self):
        """
        CommandLine:
            export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/VIAME/packages/kwiver/vital/bindings
            python -m c_introspect VitalTypeIntrospectCBind.dump_c_header:0 --class=detected_object

        Example:
            >>> from c_introspect import *
            >>> cxx_classname = ub.argval('--class', default='feature_set')
            >>> self = VitalTypeIntrospectCBind(cxx_classname)
            >>> self.parse_c_class_bindings()
            >>> self.dump_c_header()
        """
        method_fmtstr = ub.codeblock(
            '''
            VITAL_C_EXPORT
            {return_type} {cxx_funcname}({argspec});
            ''')

        fmtdict = dict(
            cxx_classname=self.cxx_classname,
            CXX_CLASSNAME=self.cxx_classname.upper()
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
            if other != self.cxx_classname:
                vital_types.append(other)
        vital_types.append(self.cxx_classname)

        vital_type_include_lines = []
        for vital_type in vital_types:
            line = '#include <vital/bindings/c/types/{vital_type}.h>'.format(vital_type=vital_type)
            vital_type_include_lines.append(line)
        vital_type_include_block = '\n'.join(vital_type_include_lines)
        fmtdict['vital_type_include_block'] = vital_type_include_block

        body_fmtstr = fmt_templates.VITAL_C_BINDING_H_FILE

        d = fmtdict.copy()
        d['method_block'] = method_block
        d['alt_constructors'] = '??'
        d['copyright'] = fmt_templates.COPYRIGHT
        autogen_text = body_fmtstr.format(**d)

        print(autogen_text)

        # autogen_fpath = join(self.c_binding_base, self.cxx_classname + '.h.autogen')
        # autogen_fpath = join(self.c_binding_base, self.cxx_classname + '.h')
        print(autogen_text)
        # ub.writeto(autogen_fpath, autogen_text)

    def dump_python_ctypes(self):
        """
        CommandLine:
            export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/VIAME/packages/kwiver/vital/bindings
            python -m c_introspect VitalTypeIntrospectCBind.dump_python_ctypes:0 --class=detected_object

        Example:
            >>> from c_introspect import *
            >>> cxx_classname = ub.argval('--class', default='feature_set')
            >>> self = VitalTypeIntrospectCBind(cxx_classname)
            >>> self.parse_c_class_bindings()
            >>> self.dump_python_ctypes()
        """
        blocks = []
        for method_info in self.cxx_method_infos:

            cxx_funcname = method_info['cxx_funcname']
            endre = re.compile('vital_' + self.cxx_classname + '_' + named('suffix', VARNAME))
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

            # prefix = 'C.'
            prefix = 'c_'
            block = ub.codeblock(
                r'''
                {prefix}{suffix} = VITAL_LIB.{cxx_funcname}
                {prefix}{suffix}.argtypes = {argtypes}
                {prefix}{suffix}.restype = {restype}
                ''').format(
                    prefix=prefix,
                    suffix=suffix,
                    cxx_funcname=cxx_funcname,
                    argtypes=argtypes,
                    restype=restype)
            blocks.append(block)

        py_c_api = 'def define_{}_c_api():'.format(self.cxx_classname)
        py_c_api += '\n    class {}_c_api(object):'.format(self.cxx_classname)
        py_c_api += '\n        pass'
        py_c_api += '\n    C = {}_c_api()'.format(self.cxx_classname)
        py_c_api += '\n' + ub.indent('\n\n'.join(blocks))
        py_c_api += '\n    return C'
        print(py_c_api)

if __name__ == '__main__':
    r"""
    CommandLine:
        python -m vital.types.c_introspect
    """
    ub.doctest_package()
    # import pytest
    # pytest.main([__file__, '--doctest-modules'])
