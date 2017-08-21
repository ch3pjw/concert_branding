from lxml import etree
from random import randint

from svg.ast import Svg, Rect


def random_colour():
    return 'rgb({r}, {g}, {b})'.format(
        r=randint(0, 255), g=randint(0, 255), b=randint(0, 255)
    )


def make_grid(x, y, size, divisions):
    grid_square_size = size / divisions
    for h in range(divisions):
        for v in range(divisions):
            yield Rect(
                x=x + (grid_square_size * h),
                y=y + (grid_square_size * v),
                width=grid_square_size,
                height=grid_square_size,
                fill=random_colour()
            )


if __name__ == '__main__':
    s = Svg(
        *make_grid(30, 44, 100, 5)
    )
    tree = etree.ElementTree(s._etree)
    with open('../build/foo.svg', 'wb') as f:
        tree.write(
            f, pretty_print=True, xml_declaration=True, encoding='utf-8')
