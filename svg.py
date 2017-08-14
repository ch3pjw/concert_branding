import sys
from collections import namedtuple
from functools import partial, wraps
from math import sin, acos

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
            self._tag,
            attrib={k: str(v) for k, v in attributes.items()})
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


def _str_ins(ins):
    if ins is z:
        return 'Z'
    else:
        d = ins.__dict__
        rel = d.pop('rel')
        letter = ins.letter.lower() if rel else ins.letter.upper()
        args = ' '.join(map(str, map(int, d.values())))
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


def clockwise_square(size, x=0, y=0):
    return (
        M(x, y),
        H(size),
        V(size),
        H(x),
        V(y)
    )


def clockwise_circle(r, cx=0, cy=0):
    return (
        M(cx, cy - r),
        a(r, r, 0, 0, 0, 0, 2 * r),
        a(r, r, 0, 0, 0, 0, -2 * r)
    )


if __name__ == '__main__':
    s = Svg(
        Path(
            d=(
                clockwise_square(32) +
                (
                    M(2, 15),
                    V(17),
                    H(6),
                    V(20),
                    v(-sin(acos(1/10))),
                    a(5, 5, 0, 1, 0, 2, 0),
                    V(17),
                    H(24),
                    V(20),
                    v(-sin(acos(1/10))),
                    a(5, 5, 0, 1, 0, 2, 0),
                    V(17),
                    H(30),
                    V(15),
                    H(17),
                    V(12),
                    v(sin(acos(1/10))),
                    a(5, 5, 0, 1, 0, -2, 0),
                    V(15)
                ) +
                clockwise_circle(3, 16, 7) +
                clockwise_circle(3, 7, 25) +
                clockwise_circle(3, 25, 25) +
                (Z,)
            )
        )
    )
    # s = Svg(
    #     Path(
    #         d=(
    #             M(5, 80),
    #             h(130),
    #             m(-65, 0),
    #             v(-60),
    #             m(-40, 50),
    #             v(60),
    #             m(80, -60),
    #             v(60)
    #         )
    #     ),
    # )
    tree = etree.ElementTree(s._etree)
    with open('foo.svg', 'wb') as f:
        tree.write(
            f, pretty_print=True, xml_declaration=True, encoding='utf-8')
