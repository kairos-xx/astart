"""Hand-written patterns that exercise specialised refinement passes."""

import contextlib
import functools
import itertools
import typing
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import partial, wraps


class Meta(type):
    """Registry metaclass."""

    _registry = {}
    _instances = {}

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace)
        mcs._registry[name] = cls
        return cls

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        cls.registered = True


class Service(metaclass=Meta):
    def __init__(self, name):
        self.name = name
        self.items = []
        self.mapping = {}
        self.count = 0

    def add(self, item):
        self.items.append(item)
        self.count += 1
        return self


class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, value=0):
        self.value = value


class Descriptor:
    def __set_name__(self, owner, name):
        self.name = "_" + name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return getattr(instance, self.name)

    def __set__(self, instance, value):
        setattr(instance, self.name, value)

    def __delete__(self, instance):
        delattr(instance, self.name)


class Managed:
    attr = Descriptor()

    def __init__(self, attr=1):
        self.attr = attr


class Base:
    def __init__(self, a, b=2):
        self.a = a
        self.b = b

    def method(self, x):
        return x * self.a


class Child(Base):
    def __init__(self, a, b=3, c=None):
        super().__init__(a, b)
        self.c = c

    def method(self, x):
        return super().method(x) + 1


def make_class(flag):
    class Local(Base):
        def extra(self):
            return self.a

    class Other:
        pass

    if flag:
        return Local
    return Other


def make_instance():
    cls = make_class(True)
    return cls(1)


@contextmanager
def opened(path):
    handle = open(path)
    try:
        yield handle
    finally:
        handle.close()


@contextlib.contextmanager
def counter():
    n = 0
    yield n


def gen_numbers(limit):
    i = 0
    while i < limit:
        yield i
        i += 1
    return i


def gen_pairs(items):
    for i, item in enumerate(items):
        yield i, item
    yield from gen_numbers(3)


def gen_strings():
    yield "a"
    yield "b"
    return "done"


def identity_decorator(fn):
    return fn


def proxy_decorator(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def timing(fn):
    def inner(*args, **kwargs):
        result = fn(*args, **kwargs)
        return result

    return inner


@identity_decorator
def decorated_a(x):
    return x + 1


@proxy_decorator
def decorated_b(x, y):
    return x + y


@timing
def decorated_c(x):
    return str(x)


@functools.lru_cache(maxsize=None)
def cached(n):
    return n * 2


@functools.cache
def cached2(n):
    return [n]


def use_partial():
    add = partial(decorated_b, 1)
    return add(2)


def pad(a, b):
    return list(itertools.zip_longest(a, b, fillvalue=0))


def pad2(a, b):
    return list(itertools.zip_longest(a, b, fillvalue="x"))


def chained(*iterables):
    return list(itertools.chain(*iterables))


def nested_numeric(x):
    def inner(y):
        return y * 2.5

    return inner(x) + 1


def numeric_assign(values):
    total = 0
    for v in values:
        total += v * 1.5
    return total


def returns_dict():
    return {"a": 1, "b": 2}


def returns_nested_dict(x):
    return {"a": [x], "b": {"c": x}}


def get_override(d, key, default=None):
    if key in d:
        return d[key]
    return default


def narrowing(x):
    if isinstance(x, int):
        return x + 1
    if isinstance(x, str):
        return x.upper()
    if x is None:
        return 0
    if callable(x):
        return x()
    return x


def globals_lookup(name):
    return globals()[name]


def locals_lookup(name):
    return vars()[name]


def callbacks(handlers, event):
    for handler in handlers:
        handler(event)
    return handlers


def apply_all(fns, value):
    return [fn(value) for fn in fns]


def compose(f, g):
    def composed(x):
        return f(g(x))

    return composed


def kwargs_forward(**options):
    return dict(options)


def varargs(*values, sep=" "):
    return sep.join(str(v) for v in values)


async def fetch(url, retries=3):
    for _ in range(retries):
        data = await download(url)
        if data:
            return data
    return None


async def download(url):
    return url.encode()


async def agen(n):
    for i in range(n):
        yield i


async def consume():
    result = []
    async for v in agen(3):
        result.append(v)
    async with contextlib.AsyncExitStack() as stack:
        stack.push_async_callback(download, "x")
    return result


class Node:
    def __init__(self, value, next=None):
        self.value = value
        self.next = next

    def __iter__(self):
        node = self
        while node:
            yield node.value
            node = node.next

    def __len__(self):
        return sum(1 for _ in self)

    def __getitem__(self, index):
        return list(self)[index]

    def __contains__(self, item):
        return item in list(self)

    def __eq__(self, other):
        return isinstance(other, Node) and self.value == other.value

    def __repr__(self):
        return f"Node({self.value!r})"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __add__(self, other):
        return Node(self.value + other.value)

    def __call__(self, x):
        return x


class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        return self._items.pop()

    def peek(self):
        return self._items[-1] if self._items else None

    @property
    def size(self):
        return len(self._items)

    @size.setter
    def size(self, value):
        del self._items[value:]

    @classmethod
    def from_iterable(cls, items):
        s = cls()
        for item in items:
            s.push(item)
        return s

    @staticmethod
    def helper(a, b):
        return a if a > b else b


class Config(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def update_all(self, **kw):
        for k, v in kw.items():
            self[k] = v


class Visitor:
    def visit(self, node):
        method = getattr(self, "visit_" + type(node).__name__, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        for child in getattr(node, "children", []):
            self.visit(child)


def tuple_things(a, b):
    x, y = a, b
    first, *rest = [a, b, a]
    return x, y, first, rest


def comprehension(data):
    squares = [d * d for d in data]
    lookup = {d: str(d) for d in data}
    uniq = {d for d in data}
    gen = (d for d in data if d)
    return squares, lookup, uniq, gen


def string_things(text):
    parts = text.split(",")
    joined = "-".join(parts)
    stripped = joined.strip()
    return stripped.encode("utf-8"), len(parts)


def file_things(path):
    with open(path, "rb") as f:
        raw = f.read()
    with open(path + ".out", "w") as g:
        g.write(raw.decode())
    return raw


def try_things(x):
    try:
        value = int(x)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("bad") from exc
    else:
        return value
    finally:
        pass


def lambdas():
    key = lambda item: item[1]
    pairs = sorted([(1, "b"), (2, "a")], key=key)
    return pairs, list(map(lambda v: v + 1, [1, 2])), list(filter(None, [0, 1]))


def walrus(data):
    if (n := len(data)) > 3:
        return n
    return 0


def match_things(command):
    match command:
        case ["go", direction]:
            return direction
        case {"action": action}:
            return action
        case int(n) if n > 0:
            return n
        case _:
            return None


def globals_and_nonlocal():
    count = 0

    def bump():
        nonlocal count
        count += 1
        return count

    return bump


T = typing.TypeVar("T")


def generic_first(items: list[T]) -> T:
    return items[0]


class Pair(typing.Generic[T]):
    def __init__(self, a: T, b: T) -> None:
        self.a = a
        self.b = b

    def swap(self):
        return Pair(self.b, self.a)


class Reader(typing.Protocol):
    def read(self, n: int = -1) -> bytes: ...


def consume_reader(reader: Reader, store):
    store.value = reader.read()
    return store


def callable_param(cb: Callable[..., object], arg):
    return cb(arg, 1)


def typed_iter() -> Iterator[int]:
    yield 1


class Enumish:
    A = 1
    B = 2
    names = {A: "a", B: "b"}

    @classmethod
    def label(cls, value):
        return cls.names.get(value, "?")


CONSTANT = 3.14
NAMES = ["a", "b"]
TABLE = {"x": 1}
FLAG = True
NOTHING = None
PAIR = (1, "a")
