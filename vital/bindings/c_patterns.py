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
import re
import six
import ubelt as ub
import copy

NATIVE_TYPES = {
    'double', 'int', 'float', 'bool', 'char', 'int64_t'
}

C_SINGLE_COMMENT = '//.*'
C_MULTI_COMMENT = r'/\*.*?\*/'

C_FILENAME = '[A-Za-z_.][A-Za-z0-9_.]*'

STARTLINE = '^'
# ENDLINE = '$'
lparen = re.escape('(')
rparen = re.escape(')')
rcurly = re.escape('{')

WHITESPACE =  r'\s*'
SPACE = '[ \t]*'

VARNAME = '[A-Za-z_][A-Za-z0-9_]*'


def named(key, regex):
    return r'(?P<%s>%s)' % (key, regex)


def optional(regex):
    return r'(%s)?' % (regex,)


def regex_or(list_):
    return '(' + '|'.join(list_) + ')'


CV_QUALIFIER = regex_or(['const', 'volatile'])

_TYPENAME = '[A-Za-z_:][:<>A-Za-z0-9_*]*'
TYPENAME = optional(CV_QUALIFIER + '\s+') + _TYPENAME + optional('\s*?(&|&&)')


class MethodInfo(ub.NiceRepr):
    def __init__(self, info):
        d = info
        if d.get('argspec', None) is not None:
            d['argspec'] = CArgspec(d.get('argspec'), kind='cxx')
        for k, v in d.items():
            if k.startswith('is_'):
                d[k] = v is not None
        self.info = info

    def __getitem__(self, index):
        return self.info[index]

    def __nice__(self):
        argspec_type_str = self.info['argspec'].format_typespec()
        return '{}({}) -> {}'.format(self.info['cxx_funcname'],
                                     argspec_type_str,
                                     self.info['return_type'])


class CPatternMatch(object):
    @staticmethod
    def strip_comments(text):
        # Remove comments
        text = re.sub(C_SINGLE_COMMENT, '', text)
        text = re.sub(C_MULTI_COMMENT, '', text, flags=re.MULTILINE | re.DOTALL)
        return text

    @staticmethod
    def balanced_paren_hack():
        # Hack, to ensure balanced parens.  define argspec pattern to allow for
        # at most some constant number of nested parens, otherwise it will
        # break.
        invalids = '^-+;'
        base_argspec = '[' + invalids + lparen + ']*?'
        def simulated_depth(n=0):
            """
            assert re.match(simulated_depth(0) + rparen, 'foo)')
            assert not re.match(simulated_depth(0) + rparen, 'foo())')
            assert re.match(simulated_depth(1) + rparen, 'foo())')
            assert re.match(simulated_depth(1) + rparen, 'foo(bar))')
            assert not re.match(simulated_depth(1) + rparen, 'foo(ba()r))')
            assert re.match(simulated_depth(2) + rparen, 'foo(ba()r))')
            """
            if n == 0:
                return base_argspec
            deep_part = simulated_depth(n - 1)
            return base_argspec + optional(lparen + deep_part + rparen + base_argspec)

        def simulated_breadth(deep_argspec_pat, n=0):
            if n == 0:
                return deep_argspec_pat
            return deep_argspec_pat + optional(simulated_breadth(deep_argspec_pat, n - 1))

        # Up to 7 args with parens, each can have at most 2 nestings
        deep_argspec_pat = simulated_depth(n=2)
        argspec_pattern = simulated_breadth(deep_argspec_pat, n=7)
        # argspec_pattern = '[^-+;]*?'

        # argspec_base = '[^-+;' + lparen + ']*?'
        # nest = lparen + argspec_base + rparen
        # argspec_pattern = argspec_base + optional(nest)
        return argspec_pattern

    @staticmethod
    def constructors(text, classname):
        """
        >>> import sys
        >>> sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings')
        >>> from c_patterns import *
        >>> text = ub.codeblock(
        ...     '''
        ...
        ...     class dummy;
        ...
        ...     typedef std::shared_ptr< dummy > dummy_sptr;
        ...
        ...     dummy( const int& a, int x=a(), int y=b(1, d()), int z = q(1) );
        ...     dummy( const int& a, int x=a(), int z = q(1) );
        ...     dummy( const int& a, int z = q(1) );
        ...     dummy( const int& a, int y=b(1, d()) );
        ...     dummy( const int& a );
        ...
        ...     dummy( const int& a, double b = 1.0, int x=a(), int y=b(1, d()), int z = q(1) );
        ...
        ...     virtual ~dummy() VITAL_DEFAULT_DTOR
        ...     ''')
        >>> classname = 'dummy'
        >>> method_infos = CPatternMatch.constructors(text, classname)
        >>> for info in method_infos:
        >>>     print(list(map(str, info['argspec'].args)))

        """
        argspec_pattern = CPatternMatch.balanced_paren_hack()

        cxx_constructor_def = WHITESPACE.join([
            STARTLINE + SPACE + '\\b' + classname,
            lparen,
            named('argspec', argspec_pattern),  # This needs work
            # breaks if there are nested parens
            rparen,
            # optional(CV_QUALIFIER),
            # optional(named('is_init0', '=' + WHITESPACE + '0')),
            regex_or([
                # initializer-clause
                optional(named('initilizer', ':.*?')),
                named('braced_init_list', rcurly),
                ';',
            ]),
        ])
        cxx_constructor_infos = []
        flags = re.MULTILINE | re.DOTALL
        for match in re.finditer(cxx_constructor_def, text, flags=flags):
            # match_text = match.string[match.start():match.end()]
            # print('match_text = {!r}'.format(match_text.replace('\n', ' ').strip()))
            d = match.groupdict()
            d['cxx_funcname'] = '__init__'
            d['return_type'] = classname + '*'
            info = MethodInfo(d)
            cxx_constructor_infos.append(info)

        import utool as ut
        print('cxx_constructor_infos = {}'.format(ut.repr4(cxx_constructor_infos)))
        return cxx_constructor_infos

    @staticmethod
    def func_declarations(text, classname=None):
        """
        Can this be rectified with func_definitions?
        """
        # Regex for attempting to match a cxx func
        # function-definition:
        # attribute-specifier-seqopt decl-specifier-seqopt declarator function-body     C++0x
        # attribute-specifier-seqopt decl-specifier-seqopt declarator = default ;     C++0x
        # attribute-specifier-seqopt decl-specifier-seqopt declarator = delete ;     C++0x

        cxx_func_def = WHITESPACE.join([
            STARTLINE + SPACE + '\\b' + named('return_type', TYPENAME),
            '\s',
            named('cxx_funcname', VARNAME),
            lparen,
            named('argspec', '[^-+;]*?'),  # This needs work
            rparen,
            optional(CV_QUALIFIER),
            # should go in initializer clause
            optional(named('is_init0', '=' + WHITESPACE + '0')),
            regex_or([
                # initializer-clause
                named('semi', ';'),
                named('braced_init_list', rcurly),
            ]),
        ])

        # match = re.search(cxx_func_def, text, flags=flags)
        # d = match.groupdict()
        # print('match = {!r}'.format(match))
        flags = re.MULTILINE | re.DOTALL

        cxx_func_declares = []
        for match in re.finditer(cxx_func_def, text, flags=flags):
            # print('match = {!r}'.format(match))
            match_text = match.string[match.start():match.end()]
            print('match_text = {!r}'.format(match_text.replace('\n', ' ').strip()))
            d = match.groupdict()
            info = MethodInfo(d)
            info.classname = classname
            cxx_func_declares.append(info)

        import utool as ut
        text = ut.repr4([i.__nice__() for i in cxx_func_declares], strvals=True)
        text = ut.align(text, '->')
        print('FUNC DECLARATIONS')
        print('cxx_func_declares = {}'.format(text))
        return cxx_func_declares

    @staticmethod
    def func_definitions(text, classname=None):
        """
        Can we implement a simple pyparsing for this to handle most cases?
        """
        flags = re.MULTILINE | re.DOTALL

        # Regex for attempting to match a cxx func
        cxx_func_def = WHITESPACE.join([
            STARTLINE + SPACE + '\\b' + named('return_type', TYPENAME),
            '\s',
            named('cxx_funcname', VARNAME),
            lparen,
            named('argspec', '[^;]*'),  # This needs work
            rparen,
            named('braced_init_list', rcurly),
            # ENDLINE
        ])

        match = re.search(cxx_func_def, text, flags=flags)
        d = match.groupdict()
        # print('match = {!r}'.format(match))
        import utool as ut

        cxx_func_defs = []
        for match in re.finditer(cxx_func_def, text, flags=flags):
            # print('match = {!r}'.format(match))
            d = match.groupdict()
            info = MethodInfo(d)
            info.classname = classname
            cxx_func_defs.append(info)

        text = ut.repr4([i.__nice__() for i in cxx_func_defs], strvals=True)
        text = ut.align(text, '->')
        print('FUNC DEFINITIONS')
        print('cxx_func_defs = {}'.format(text))
        return cxx_func_defs

    @staticmethod
    def relative_includes(text):
        # Regex for attempting to match a relative header
        cxx_rel_header = WHITESPACE.join([
            '#include \"' + named('header', C_FILENAME) + '\"'
        ])
        cxx_rel_includes = []
        flags = re.MULTILINE | re.DOTALL
        for match in re.finditer(cxx_rel_header, text, flags=flags):
            cxx_rel_includes.append(match.groupdict()['header'])
        return cxx_rel_includes


class CArg(ub.NiceRepr):
    """
    Example:
        >>> import sys
        >>> sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings/python/vital/types')
        >>> from c_introspect import *
        >>> print(CArg.parse('double **foo=0'))
        >>> print(CArg.parse('double **foo=0').__dict__)
        >>> print(CArg.parse('char* const& ptr'))
        >>> print(CArg.parse('const int &p'))
        >>> print(CArg.parse('const char ** const * * const &p'))
        >>> print(CArg.parse('const char ** const **const*&&p=d()').__dict__)
        >>> print(CArg.parse('void'))

    """
    def __init__(carg, type, name=None, default=None, orig_text=None):
        if isinstance(type, six.string_types):
            type = CType(type)
        carg.type = type
        carg.name = name
        carg.default = default
        carg._orig_text = orig_text

    def copy(self):
        return copy.deepcopy(self)

    @classmethod
    def parse(VitalCArg, text):
        """
        TODO:
            group consts with their appropriate pointer / type
            handle single or double reference only
        """
        parts = text.split('=')
        left = parts[0]
        default = None
        if len(parts) > 1:
            default = '='.join(parts[1:]).strip()

        parts = left.strip().split(' ')
        # the name will always be on the far right if it exists
        # but it may be mangled with refs or pointers. However, refs
        # may only exist directly next the the name
        cname = parts[-1]
        pos = max(cname.rfind('&'), cname.rfind('*'))
        if pos >= 0:
            name = cname[pos + 1:]
            # The rest belongs with the type
            type_text = ' '.join(parts[:-1]) + cname[:pos + 1]
        else:
            name = cname
            type_text = ' '.join(parts[:-1])

        type = CType(type_text)
        carg = VitalCArg(type, name, default, text)
        return carg

    def __nice__(carg):
        if carg.name is not None:
            if carg.default is None:
                return '{} {}'.format(carg.type, carg.name)
            else:
                return '{} {}={}'.format(carg.type, carg.name, carg.default)
        else:
            return '{}'.format(carg.type)


class CArgspec(ub.NiceRepr):
    """
    argspec = d['argspec']
    cargs = CArgspec(argspec)
    cargs.args

    http://www.nongnu.org/hcb/#dcl.decl

    http://www.nongnu.org/hcb/#parameter-declaration

    parameters-and-qualifiers:
        ( parameter-declaration-clause ) attribute-specifier-seqopt \
                cv-qualifier-seqopt ref-qualifieropt \
                exception-specificationopt

    Example:
        >>> # DISABLE_DOCTEST
        >>> sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings')
        >>> from c_patterns import *
        >>> text = 'const int& a, int x=a("foob,a()r"), int y=b(1, d()), int z = q(1)'
        >>> CArgspec(text)
    """

    _CARG = CArg  # HACK (changed to VitalCArg)

    def __init__(cargs, text, kind='cxx'):
        cargs._str = text
        cargs.kind = kind

        text = text.replace('\n', ' ').strip()
        text = re.sub('  *', ' ', text)
        cargs._cleaned = text

        def _paren_aware_split(text):
            import utool as ut
            parts = []
            prev_nested = False
            for tag, part in ut.parse_nestings2(text):
                if tag == 'nonNested':
                    part_split = part.split(',')
                    if prev_nested:
                        parts[-1] += part_split[0]
                        parts += part_split[1:]
                    else:
                        parts += part_split
                    prev_nested = False
                else:
                    parts[-1] += ut.recombine_nestings([(tag, part)])
                    prev_nested = True
            return parts

        cargs.args = []
        if cargs._cleaned:
            for item in _paren_aware_split(text):
                cargs.args.append(cargs._CARG.parse(item))

    def copy(self):
        return copy.deepcopy(self)

    def __iter__(cargs):
        return iter(cargs.args)

    def __nice__(cargs):
        return str(list(map(str, cargs.args)))

    def format_argspec(cargs):
        return ', '.join([carg.__nice__() for carg in cargs])

    def format_typespec_python(cargs):
        return ', '.join([carg.python_ctypes() for carg in cargs])

    def format_callargs_cxx(cargs):
        return ', '.join([carg.cxx_name() for carg in cargs])

    def format_typespec(cargs):
        return ', '.join([str(carg.type) for carg in cargs])


class CType(ub.NiceRepr):
    """
    This should be able to (more-or-less) parse C++ "trailing-type-specifier"
    http://www.nongnu.org/hcb/#trailing-type-specifier

    Note about const:
        Generally, const applies to the left unless it is at the extreme left
        in which case it applies to the right.

        EG:
        char *p              = "data"; //non-const pointer, non-const data
        const char *p        = "data"; //non-const pointer, const data
        char const *p        = "data"; //non-const pointer, const data
        char * const p       = "data"; //const pointer, non-const data
        const char * const p = "data"; //const pointer, const data

        note:
            ref(&) must be to the left of the name
            Can only have single or double refs

        # use this for testing what syntax is valid
        https://www.onlinegdb.com/online_c++_compiler

    Note:
        unsigned int const == unsigned int const

    Example:
        >>> import sys
        >>> sys.path.append('/home/joncrall/code/VIAME/packages/kwiver/vital/bindings')
        >>> from c_patterns import *
        >>> CType('char const * * const * * const * &&').tokens
        >>> CType('char const * * const * * const * &&')
        >>> CType('char const * * const * * const &&').tokens
        >>> CType('char const * * const * * const * &').tokens
        >>> CType('char const * * const * * const &').tokens
        >>> CType('const int&')
        >>> CType('vector< std::string >').tokens
        >>> CType('unsigned int')
        >>> CType('unsigned const int').ref_degree
        >>> CType('unsigned const int&').ref_degree
        >>> CType('long long long').base
        >>> ctype = CType('const volatile long long long &')
        >>> ctype = CType('signed long long int')
    """
    def __init__(ctype, tokens_or_text):
        if isinstance(tokens_or_text, six.string_types):
            ctype.tokens = ctype._tokenize(tokens_or_text)
        else:
            ctype.tokens = tokens_or_text

    @staticmethod
    def _tokenize(text):
        # TODO: const volatile is a thing
        cv_ = {'const', 'volatile'}

        parts = text.split(' ')
        parts = [p for part in parts for p in re.split('(const)', part)]
        parts = [p for part in parts for p in re.split('(\*)', part) ]
        parts = [p for part in parts for p in re.split('(&)', part) ]
        parts = [p for p in parts if p]
        if parts[0] in cv_:
            assert len(parts) > 1, 'const should be applied to something'
            if parts[1] in cv_.difference({parts[0]}):
                # VERY RARE CASE (const+volatile)
                parts[0], parts[1], parts[2] = parts[2], parts[0], parts[1]
            else:
                # swap for consistent order
                parts[0], parts[1] = parts[1], parts[0]

        # Group consts with appropriate parts
        angle_count = 0

        tokens = []
        curr_t, curr_cv = [], []
        def _push():
            # Helper to push current onto tokens
            if not curr_cv:
                if curr_t[0] in {'*', '&'}:
                    tokens.append((''.join(curr_t),))
                else:
                    tokens.append((' '.join(curr_t),))
            elif curr_t[0] == '*':
                tokens.append((''.join(curr_t),  ' '.join(curr_cv)))
            else:
                tokens.append((' '.join(curr_t), ' ', ' '.join(curr_cv)))
        for c in parts:
            if len(curr_t) > 0 and angle_count == 0:
                if c == '*':
                    _push()
                    curr_t, curr_cv = [], []
                elif c == '&' and curr_t[-1] != '&':
                    _push()
                    curr_t, curr_cv = [], []

            # Ensure we only split things outside balanced templates
            angle_count += c.count('<')
            angle_count -= c.count('>')
            if c not in cv_:
                curr_t.append(c)
            else:
                curr_cv.append(c)
        _push()
        return tokens

    def dref(ctype):
        """
        Example:
            >>> from c_patterns import *
            >>> ctype = CType('int * const*')
            >>> assert ctype.deref() == 'int *'
            >>> assert ctype.deref().deref() == 'int'
        """
        if ctype.ptr_degree == 0:
            raise ValueError('Cannot dereference further')
        new_tokens = []
        done = False
        for t in ctype.tokens[::-1]:
            if not done and t[0] == '*':
                done = True
            else:
                new_tokens.append(t)
        return CType(new_tokens[::-1])

    def addr(ctype):
        if ctype.ref_degree > 0:
            new_tokens = ctype.tokens[:-1] + [('*',)] + ctype.tokens[-1:]
        else:
            new_tokens = ctype.tokens[:] + [('*',)]
        return CType(new_tokens)

    @property
    def ref_degree(ctype):
        return ctype.tokens[-1].count('&')

    @property
    def ptr_degree(ctype):
        return sum(['*' in t for t in ctype.tokens])

    @property
    def base(ctype):
        return ctype.tokens[0]

    @property
    def data_base(ctype):
        return ctype.tokens[0][0]

    def __str__(ctype):
        return ctype.format()

    def __nice__(ctype):
        return ctype.format()

    def format(ctype):
        return ''.join([''.join(t) for t in ctype.tokens])

    def is_native(ctype):
        return ctype.data_base in NATIVE_TYPES

    def __eq__(self, other):
        if isinstance(other, six.string_types):
            other = CType(other)
        if not isinstance(other, CType):
            raise TypeError('Cannot compare {} to {}'.format(
                type(self), type(other)))
        return self.tokens == other.tokens
