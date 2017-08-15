from lxml import etree
from math import sin, acos, sqrt

from svg.ast import Svg, Path, M, V, H, a, Z, ViewBox, Circle, Rect
from svg.shapes import clockwise_square, clockwise_circle


def segment_height(chord_width, radius):
    return radius - sqrt(
        radius ** 2 - (chord_width / 2) ** 2)


if __name__ == '__main__':
    w = 6
    big_r = 9
    little_r = 3
    sh = segment_height(w, big_r)
    s = Svg(
        Path(
            d=(
                clockwise_square(64) +
                (
                    M(8, 29),
                    V(35),
                    H(15),
                    V(40),
                    a(big_r, big_r, 0, 1, 0, 6, 0),
                    V(35),
                    H(43),
                    V(40),
                    a(big_r, big_r, 0, 1, 0, 6, 0),
                    V(35),
                    H(56),
                    V(29),
                    H(35),
                    V(24),
                    a(big_r, big_r, 0, 1, 0, -6, 0),
                    V(29),
                    H(8)
                ) +
                clockwise_circle(little_r, 18, 49 - sh) +
                clockwise_circle(little_r, 46, 49 - sh) +
                clockwise_circle(little_r, 32, 24 - big_r + sh) +
                (Z,)
            )
        ),
        viewBox=ViewBox(0, 0, 64, 64)
    )
    tree = etree.ElementTree(s._etree)
    with open('foo.svg', 'wb') as f:
        tree.write(
            f, pretty_print=True, xml_declaration=True, encoding='utf-8')
