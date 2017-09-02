

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
