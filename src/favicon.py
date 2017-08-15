from lxml import etree
from math import sin, acos, sqrt

from svg.ast import Svg, Path, M, V, H, a, Z, ViewBox, Circle, Rect
from svg.shapes import clockwise_square, clockwise_circle


def segment_height(chord_width, radius):
    return radius - sqrt(
        radius ** 2 - (chord_width / 2) ** 2)


def icon_path(base_width=6, inner_r=None):
    if inner_r is None:
        inner_r = base_width / 2
    w = base_width / 2
    R = 9
    r = inner_r
    sh = segment_height(w, R)
    return Path(
        d=(
            clockwise_square(64) +
            (
                M(8, 32 - w),
                V(32 + w),
                H(18 - w),
                V(40),
                a(R, R, 0, 1, 0, base_width, 0),
                V(32 + w),
                H(46 - w),
                V(40),
                a(R, R, 0, 1, 0, base_width, 0),
                V(32 + w),
                H(56),
                V(32 - w),
                H(32 + w),
                V(24),
                a(R, R, 0, 1, 0, -base_width, 0),
                V(32 - w),
                H(8)
            ) +
            clockwise_circle(r, 18, 49 - sh) +
            clockwise_circle(r, 46, 49 - sh) +
            clockwise_circle(r, 32, 24 - R + sh) +
            (Z,)
        )
    )


if __name__ == '__main__':
    w = 6
    big_r = 9
    little_r = 3
    sh = segment_height(w, big_r)
    s = Svg(icon_path(), viewBox=ViewBox(0, 0, 64, 64))
    tree = etree.ElementTree(s._etree)
    with open('foo.svg', 'wb') as f:
        tree.write(
            f, pretty_print=True, xml_declaration=True, encoding='utf-8')
