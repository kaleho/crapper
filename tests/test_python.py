from crapper.languages.python import functions_in_source


def test_function_method_and_nested_function():
    source = """
def choose(x, ready):
    if x > 0 and x < 10:
        return 1
    elif x == 0 or ready:
        return 0
    for i in xs:
        if i == 2:
            return i
    while ready:
        break
    try:
        return x
    except ValueError:
        return 0
    except KeyError:
        return -1
    match x:
        case 1:
            return 1
        case 2 | 3:
            return 2
        case _:
            return 0
    return x if x > 0 else 0

class Box:
    def open(self, flag=False):
        return 1 if flag else 0

    @staticmethod
    def shut(self):
        xs = [n for n in range(3) if n]
        return xs

def outer():
    def inner(n):
        if n:
            return 1
        return 0
    return inner(1)

async def load():
    if True:
        return 1
"""
    functions = functions_in_source(source, "src/demo/box.py", "/proj")
    assert [(fn.namespace, fn.name, fn.complexity) for fn in functions] == [
        ("demo.box", "choose", 14),
        ("demo.box.Box", "open", 2),
        ("demo.box.Box", "shut", 2),
        ("demo.box", "outer", 2),
        ("demo.box", "load", 2),
    ]


def test_nested_class_method_is_its_own_entry():
    source = """
class Outer:
    class Inner:
        def tick(self, ready, ok):
            if ready and ok:
                return 1
            return 0

def factory():
    class Hidden:
        def secret(self):
            if True:
                return 1
            return 0
    return Hidden()
"""
    functions = functions_in_source(source, "src/demo/sample.py", "/proj")
    assert [(fn.namespace, fn.name, fn.complexity) for fn in functions] == [
        ("demo.sample.Outer.Inner", "tick", 3),
        ("demo.sample", "factory", 1),
        ("demo.sample.Hidden", "secret", 2),
    ]


def test_namespace_strips_roots_src_and_init():
    source = "def f():\n    return 1\n"
    assert functions_in_source(source, "/proj/src/demo/app.py", "/proj")[0].namespace == "demo.app"
    assert functions_in_source(source, "./src/demo/app.py", ".")[0].namespace == "demo.app"
    assert functions_in_source(source, "pkg/src/demo/__init__.py", None)[0].namespace == "demo"
    assert functions_in_source(source, "__init__.py", None)[0].namespace == "__init__"


def test_strings_comments_and_package_init_do_not_add_decisions():
    source = '''
def literal():
    """if and or for while except"""
    text = "if x and y"
    # if x: return 1
    return text
'''
    functions = functions_in_source(source, "src/demo/__init__.py", "/proj")
    assert [(fn.namespace, fn.name, fn.complexity) for fn in functions] == [
        ("demo", "literal", 1)
    ]


def test_overload_stubs_are_not_functions():
    source = """
import typing
from typing import overload

class Tag:
    @overload
    def __call__(self, fn: int) -> int: ...
    @typing.overload
    def __call__(self, fn: str) -> str: ...
    def __call__(self, fn):
        return fn

@overload
def pick(x: int) -> int: ...
@staticmethod
def pick(x):
    return x
"""
    found = functions_in_source(source, "src/pkg/tag.py")
    assert [(f.namespace, f.name, f.start_line) for f in found] == [
        ("pkg.tag.Tag", "__call__", 10),
        ("pkg.tag", "pick", 16),
    ]


def test_protocol_stub_members_are_not_functions():
    source = '''
import typing
from typing import Protocol

class Clock(Protocol):
    def now(self) -> int: ...
    def sleep(self, seconds: float) -> None:
        """Wait."""
        ...
    def doc_only(self) -> None:
        """Only a docstring."""
    def real(self) -> int:
        return 1

class Unit(typing.Protocol[T]):
    @property
    def name(self) -> str: ...

class Plain:
    def todo(self) -> None: ...

def stub() -> None: ...
'''
    found = functions_in_source(source, "src/pkg/clock.py")
    assert [(f.namespace, f.name) for f in found] == [
        ("pkg.clock.Clock", "real"),
        ("pkg.clock.Plain", "todo"),
        ("pkg.clock", "stub"),
    ]
