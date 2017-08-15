from math import sin, acos
from lxml import etree

from svg.ast import Svg, Path, M, V, H, v, a, Z
from svg.shapes import clockwise_square, clockwise_circle


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
    tree = etree.ElementTree(s._etree)
    with open('foo.svg', 'wb') as f:
        tree.write(
            f, pretty_print=True, xml_declaration=True, encoding='utf-8')
