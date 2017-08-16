import sys
from collections import namedtuple
from functools import partial, wraps

from lxml import etree

_module = sys.modules[__name__]


class Element:
    def __init__(self, *children, **attributes):
        self._children = children
        self._attributes = attributes

    def __len__(self):
        return len(self._children)

    def __iter__(self):
        return iter(self._children)

    def __getitem__(self, idx):
        return self._children[idx]

    def __getattr__(self, name):
        return self._attributes[name]

    @property
    def _tag(self):
        n = type(self).__name__
        return n[0].lower() + n[1:]

    @property
    def _etree(self):
        attributes = dict(self._attributes)
        cls = attributes.pop('cls', None)
        if cls:
            attributes['class'] = cls
        e = etree.Element(
            self._tag, attrib={
                k.replace('_', '-'): str(v) for k, v in attributes.items()
            }
        )
        last_child_etree_elem = None
        for c in self._children:
            if isinstance(c, str):
                if last_child_etree_elem is None:
                    e.text = c
                else:
                    last_child_etree_elem.tail = c
            else:
                last_child_etree_elem = c._etree
                e.append(last_child_etree_elem)
        return e


class Circle(Element):
    pass


class Defs(Element):
    pass


class G(Element):
    pass


class Path(Element):
    def __init__(self, *children, d, **attributes):
        super().__init__(*children, d=PathD(d), **attributes)


class Rect(Element):
    pass


class Style(Element):
    pass


class Svg(Element):
    def __init__(self, *children, **attributes):
        super().__init__(
            *children,
            xmlns='http://www.w3.org/2000/svg',
            version='1.1',
            **attributes)


class Symbol(Element):
    pass


class Text(Element):
    pass


class Use(Element):
    pass


def _str_number(n):
    return '{:f}'.format(n).rstrip('0').rstrip('.')


def _str_ins(ins):
    if ins is z:
        return 'Z'
    else:
        d = ins.__dict__
        rel = d.pop('rel')
        letter = ins.letter.lower() if rel else ins.letter.upper()
        args = ' '.join(map(str, map(_str_number, d.values())))
        return '{} {}'.format(letter, args)


MoveTo = namedtuple('MoveTo', ('x', 'y', 'rel'))
MoveTo.letter = 'm'
MoveTo.__str__ = _str_ins

LineTo = namedtuple('LineTo', ('x', 'y', 'rel'))
LineTo.letter = 'l'
LineTo.__str__ = _str_ins

HorizontalLineTo = namedtuple('HorizontalLineTo', ('x', 'rel'))
HorizontalLineTo.letter = 'h'
HorizontalLineTo.__str__ = _str_ins

VerticalLineTo = namedtuple('VerticalLineTo', ('y', 'rel'))
VerticalLineTo.letter = 'v'
VerticalLineTo.__str__ = _str_ins

ArcTo = namedtuple(
    'ArcTo', ('rx', 'ry', 'x_axis_rotate', 'large', 'sweep', 'x', 'y', 'rel'))
ArcTo.letter = 'a'
ArcTo.__str__ = _str_ins

ClosePath = namedtuple('ClosePath', ())
ClosePath.letter = 'z'
ClosePath.__str__ = lambda _: 'Z'
ClosePath.__call__ = lambda: z
z = ClosePath()
Z = z


for instruction in (MoveTo, LineTo, HorizontalLineTo, VerticalLineTo, ArcTo):
    for rel, str_f in ((True, str.lower), (False, str.upper)):
        setattr(
            _module,
            str_f(instruction.letter),
            wraps(instruction)(partial(instruction, rel=rel)))


class PathD:
    def __init__(self, inss):
        self._inss = tuple(inss)

    def __str__(self):
        return '  '.join(map(str, self._inss))


ViewBox = namedtuple('ViewBox', ('ox', 'oy', 'width', 'height'))
ViewBox.__str__ = lambda vb: ' '.join(map(str, vb))


class Kern(tuple):
    def __new__(cls, *args):
        return super().__new__(cls, args)

    def __str__(self):
        return ' '.join(map(_str_number, self))
