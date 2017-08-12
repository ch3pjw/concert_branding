import sys
from collections import namedtuple
from functools import partial, wraps

from lxml import etree

_module = sys.modules[__name__]


class Element:
    def __init__(self, *children, __content__='', **attributes):
        self.children = children
        self.content = __content__
        cls = attributes.pop('cls', None)
        if cls:
            attributes['class'] = cls
        self.attributes = attributes

    @property
    def tag(self):
        n = type(self).__name__
        return n[0].lower() + n[1:]

    @property
    def element(self):
        e = etree.Element(
            self.tag,
            attrib={k: str(v) for k, v in self.attributes.items()})
        for c in self.children:
            e.append(c.element)
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
    pass


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
        self._inss = inss

    def __str__(self):
        return '  '.join(map(str, self._inss))


if __name__ == '__main__':
    s = Svg(
        Defs(
            Circle(id='record_symbol')
        ),
        Symbol(
            Path(
                cls='logo_stroke',
                d=(
                    M(5, 80),
                    h(130),
                    m(-65, 0),
                    v(-60),
                    m(-40, 50),
                    v(60),
                    m(80, -60),
                    v(60)
                )
            ),
            Use(x=70, y=30, href='#record_symbol'),
            Use(x=30, y=130, href='#record_symbol'),
            Use(x=110, y=130, href='#record_symbol'),
            id='ethernet'
        ),
        G(
            Rect(
                x=0, y=0, width=200, height=205, cls='logo_stroke', fill=None),
            Use(x=30, y=22, width=140, height=160, href='#ethernet'),
            id='logo'
        )
    )
    print(etree.tostring(s.element))
