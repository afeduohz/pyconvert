import re
from collections import namedtuple
from typing import Any, List, Tuple, Union, Callable, Dict

io_types = Union[dict, list, str, bool, int, float, None]


class Asserter:
    @classmethod
    def eq(cls, token: str, desired: str) -> Any:
        if token != desired:
            raise Exception('need %s, but given %s' % (desired, token))
        return cls

    @classmethod
    def gt(cls, token: str, length: int) -> Any:
        if len(token) <= length:
            raise Exception('length of token %s should great than %s' % (token, length))
        return cls


class Token:
    predefined = ['=', '{', '}', '[', ']', '(', ')', '<', '>']
    ignored = [' ', '\t', '\n', '\r']
    reserved = ['True', 'False', 'None']

    @classmethod
    def tokenize(cls, inputs: str) -> List[str]:
        if not isinstance(inputs, str) or len(inputs) == 0:
            return []
        cache, s, e, t = [], 0, 1, len(inputs)
        while s < t:
            s, e = cls.eat(cache, inputs, s, e)
        return cache

    @classmethod
    def eat(cls, cache: List[str], i: str, s: int, e: int) -> Tuple[int, int]:
        d, z = i[s:e], len(i)
        if d in cls.predefined:
            cache.append(d)
            return e, e + 1
        elif d in cls.ignored:
            return e, e + 1
        while e < z:
            e = e + 1
            d = i[e - 1:e]
            if d in cls.predefined:
                cache.append(i[s:e - 1])
                return e - 1, e
        return e, z


def converter(template: str = '') -> Tuple[bool, Callable[[str], Any]]:
    Context = namedtuple('Context', ['parent', 'source', 'refer'])
    _template: str = template
    _processor: Dict[str, Callable[..., None]] = {}

    def _factory(sets: Union[list, tuple, dict], tokens: List[str]) -> Tuple[Any, List[str]]:
        cur, size = 0, len(sets)
        for x in sets:
            if cur < size - 1:
                yield x, [i for i in tokens]
            else:
                yield x, tokens
            cur += 1

    def deal(s: Union[str, List[str], Tuple[str]]):
        heads = [s] if isinstance(s, str) else [x for x in s if isinstance(s, (list, tuple,)) and isinstance(x, str)]

        def dock(handle):
            _processor.update({head: handle for head in heads})

            def dealer(*args, **kwargs):
                return handle(*args, **kwargs)

            return dealer

        return dock

    def strip(s: str, e: str):
        def peel(f):
            def handle(*args, **kwargs):
                ok = len(args) > 0
                if not ok:
                    return f(*args, **kwargs)
                tokens = args[0]
                if isinstance(tokens, list):
                    Asserter.eq(tokens.pop(0), s)
                    v = f(*args, **kwargs)
                    Asserter.eq(tokens.pop(0), e)
                    return v
                else:
                    return f(*args, **kwargs)

            return handle

        return peel

    def process(source: io_types) -> io_types:
        return _proc(Token.tokenize(_template), Context(None, source, source))

    def _proc(tokens, context: Context) -> Any:
        return None if len(tokens) == 0 else _processor.get(tokens[0], _processor.get('*'))(tokens, context)

    def _lookup(path: str, context: Context) -> Any:
        if not isinstance(path, str):
            return None
        if '/' == path:
            return context.source
        elif './' == path:
            return context.refer
        p, r = [], None
        m = re.search(r'^/(.*)$', path)
        if m:
            p, r = str.split(m.group(1), '/'), context.source
        m = re.search(r'^./(.*)$', path)
        if m:
            p, r = str.split(m.group(1), '/'), context.refer
        d = None
        while len(p) > 0:
            if not isinstance(r, dict):
                return None
            cur = p.pop(0)
            d = r.get(cur)
            r = d
        return d

    @deal('<')
    @strip('<', '>')
    def _proc_cur(tokens, parent):
        v = None
        if tokens[0] != '>':
            v = _lookup(tokens.pop(0), parent)
        return v

    @deal('[')
    @strip('[', ']')
    def _proc_list(tokens, parent):
        Asserter.eq(tokens[0], '<')
        current = _proc(tokens, parent)
        val = []
        while not tokens[0] == ']':
            if isinstance(current, (list, tuple, dict)):
                collections = current if isinstance(current, (list, tuple)) else current.items()
                if len(collections) == 0:  # if source is empty, go through silently (ignore data)
                    _proc(tokens, Context(parent, parent.source, {}))
                else:
                    for v, t in _factory(collections, tokens):  # trick(ugly) for non-ast intercept.
                        val.append(_proc(t, Context(parent, parent.source, v)))
            else:
                t = _proc(tokens, Context(parent, parent.source, current))
                if current is not None:
                    val.append(t)
        return val

    @deal('{')
    @strip('{', '}')
    def _proc_dict(tokens: List[str], parent: Context) -> Dict[str, Any]:
        Asserter.eq(tokens[0], '<')
        current = _proc(tokens, parent)
        val = {}
        while not tokens[0] == '}':
            key = str.strip(tokens.pop(0))
            Asserter.gt(key, 0).eq(tokens.pop(0), '=')
            value = _proc(tokens, Context(parent, parent.source, current))
            val.update({key: value})
        return val

    @deal('(')
    @strip('(', ')')
    def _proc_eval(tokens: List[str], context: Context) -> Any:
        return _proc(tokens, context)

    @deal(['True', 'False', 'None'])
    def _proc_literal(tokens: List[str], context: Context) -> Union[bool, None]:
        t = tokens.pop(0)
        return None if t == 'None' else True if t == 'True' else False

    @deal('*')
    def _proc_others(tokens: List[str], context: Context) -> Any:
        # path/number/str
        t = tokens.pop(0)
        if '/' == t[0] or './' == t[0:2]:
            return _lookup(t, context)
        elif re.search(r'^[-+]?\d+$', str.strip(t)):
            return int(t)
        elif re.search(r'^[-+]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][-+]?[0-9]+)?$', str.strip(t)):
            return float(t)
        return str(t)

    return not not _template, process


class Converter:

    def __init__(self, template: str = ''):
        self._c = converter(template)

    def validate(self) -> bool:
        return self._c[0]

    def convert(self, source: io_types) -> io_types:
        if not self.validate():
            return source
        return self._c[1](source)
