from lxml import etree
from random import randint
from hashlib import sha1
from collections import namedtuple

from svg.ast import Svg, Rect, G

Colour = namedtuple('Colour', ('r', 'g', 'b'))
Colour.__str__ = lambda c: 'rgb({}, {}, {})'.format(*c)


def random_colour():
    return Colour(randint(0, 255), randint(0, 255), randint(0, 255))


def hash_to_int(n, string):
    return int(sha1(string).hexdigest(), base=16) % n


def make_grid_rects(size, divisions):
    grid_square_size = size / divisions
    for h in range(divisions):
        for v in range(divisions):
            yield Rect(
                x=grid_square_size * h,
                y=grid_square_size * v,
                width=grid_square_size,
                height=grid_square_size,
                fill=random_colour()
            )


def make_grid(x, y, size, string):
    return G(
        *make_grid_rects(size, hash_to_int(3, string) + 3),
        transform='translate({x}, {y})'.format(x=x, y=y)
    )


if __name__ == '__main__':
    s = Svg(make_grid(30, 44, 100, b'emma'))
    tree = etree.ElementTree(s._etree)
    with open('../build/foo.svg', 'wb') as f:
        tree.write(
            f, pretty_print=True, xml_declaration=True, encoding='utf-8')
