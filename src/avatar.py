from lxml import etree
from random import randint
from hashlib import sha1
from collections import namedtuple

from svg.ast import Svg, Rect, G, ViewBox

Colour = namedtuple('Colour', ('r', 'g', 'b'))
Colour.__str__ = lambda c: 'rgb({}, {}, {})'.format(*c)


def random_colour():
    return Colour(randint(0, 255), randint(0, 255), randint(0, 255))


def hash_to_int(n, string):
    return int(sha1(string).hexdigest(), base=16) % n


def bilinearly_interpolate(a, b, c, d, x, y):
    '''
    a ---- b
    |      |
    |      |
    c ---- d
    '''
    return (
        a * (1 - x) * (1 - y) +
        b * x * (1 - y) +
        c * x * y +
        d * (1 - x) * y)


def make_grid_rects(size, divisions, c1, c2, c3, c4):
    grid_square_size = size / divisions
    for h in range(divisions):
        for v in range(divisions):
            x_frac = h / divisions
            y_frac = v / divisions
            yield Rect(
                x=grid_square_size * h,
                y=grid_square_size * v,
                width=grid_square_size,
                height=grid_square_size,
                fill=Colour(
                    r=bilinearly_interpolate(
                        c1.r, c2.r, c3.r, c4.r, x_frac, y_frac),
                    g=bilinearly_interpolate(
                        c1.g, c2.g, c3.g, c4.g, x_frac, y_frac),
                    b=bilinearly_interpolate(
                        c1.b, c2.b, c3.b, c4.b, x_frac, y_frac)
                )
            )


def make_grid(size, string):
    return G(
        *make_grid_rects(
            size,
            hash_to_int(2, string) + 3,
            random_colour(),
            random_colour(),
            random_colour(),
            random_colour()
        )
    )


if __name__ == '__main__':
    s = Svg(
        make_grid(60, b'paul@ruthorn.co.uk'),
        viewBox=ViewBox(0, 0, 60, 60))
    tree = etree.ElementTree(s._etree)
    with open('../build/foo.svg', 'wb') as f:
        tree.write(
            f, pretty_print=True, xml_declaration=True, encoding='utf-8')
