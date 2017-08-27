from lxml import etree
from random import randint
from hashlib import sha1
from itertools import cycle
from collections import namedtuple
import colorsys

from svg.ast import Svg, Rect, G, ViewBox


RgbColour = namedtuple('RgbColour', ('r', 'g', 'b'))
RgbColour.__str__ = lambda c: 'rgb({}, {}, {})'.format(*c)

HsvColour = namedtuple('HsvColour', ('h', 's', 'v'))


def random_colour():
    return RgbColour(randint(0, 255), randint(0, 255), randint(0, 255))


def to256(fl):
    return int(255 * fl / 1.0)


def from256(i):
    return i / 255


def rgb_to_hsv(rgb_colour):
    return HsvColour(
        *map(
            to256, colorsys.rgb_to_hsv(
                *map(
                    from256, rgb_colour))))


def hsv_to_rgb(hsl_colour):
    return RgbColour(
        *map(
            to256, colorsys.hsv_to_rgb(
                *map(
                    from256, hsl_colour))))


def clamp256(i):
    return sorted((0, i, 256))[1]


def rotate(l, n):
    n = n % len(l)
    return l[n:] + l[:n]


def lookup_mod(l, n):
    print('lookup_mod', len(l), n, n % len(l))
    return l[n % len(l)]


def generate_tetradic_colours(hashes):
    print('tetradic')
    h1 = next(hashes) % 256
    print('hue:', h1)
    h3 = (h1 + 128) % 256
    h2 = (h1 + 30) % 256
    h4 = (h2 + 128) % 256
    saturation = 256
    value = 200
    return (
        HsvColour(h1, saturation, value),
        HsvColour(h2, saturation, value),
        HsvColour(h3, saturation, value),
        HsvColour(h4, saturation, value)
    )


def generate_monochromatic_colours(hashes):
    print('mono')
    hue = next(hashes) % 256
    print('hue:', hue)
    saturation = 128
    value = 128
    spread = 128
    d = spread / 4
    return (
        HsvColour(hue, saturation, clamp256(value + 2 * d)),
        HsvColour(hue, saturation, clamp256(value + d)),
        HsvColour(hue, saturation, clamp256(value - 2 * d)),
        HsvColour(hue, saturation, clamp256(value - d))
    )


def generate_analagous_colours(seed):
    h1 = seed % 256
    h2 = (h1 + 10) % 256
    h3 = (h2 + 10) % 256
    h4 = (h3 + 10) % 256
    saturation = 256
    value = 200
    return (
        HsvColour(h1, saturation, value),
        HsvColour(h2, saturation, value),
        HsvColour(h3, saturation, value),
        HsvColour(h4, saturation, value)
    )


def generate_analagous_colours(hashes):
    print('analogue')
    h1 = next(hashes) % 256
    print('hue:', h1)
    h2 = (h1 + 30) % 256
    h3 = (h2 + 30) % 256
    h4 = (h3 + 30) % 256
    saturation = 256
    value = 200
    return (
        HsvColour(h1, saturation, value),
        HsvColour(h2, saturation, value),
        HsvColour(h3, saturation, value),
        HsvColour(h4, saturation, value)
    )


def generate_related_colours(hashes):
    fs = (
        generate_monochromatic_colours,
        generate_analagous_colours,
        generate_split_complimentary_colours,
        generate_tetradic_colours
    )
    return rotate(
        tuple(map(
            hsv_to_rgb,
            lookup_mod(fs, next(hashes))(hashes)
        )),
        next(hashes)
    )


def bilinearly_interpolate(a, b, c, d, x, y):
    '''
    a ---- b
    |      |
    |      |
    d ---- c
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
                fill=RgbColour(
                    r=bilinearly_interpolate(
                        c1.r, c2.r, c3.r, c4.r, x_frac, y_frac),
                    g=bilinearly_interpolate(
                        c1.g, c2.g, c3.g, c4.g, x_frac, y_frac),
                    b=bilinearly_interpolate(
                        c1.b, c2.b, c3.b, c4.b, x_frac, y_frac)
                )
            )


def chunks(i, chunk_size):
    return zip(*([iter(i)] * chunk_size))


def make_grid(size, seed_str):
    hashes = cycle(map(
        lambda c: int(''.join(c), base=16),
        chunks(
            sha1(seed_str).hexdigest(),
            4
        )
    ))
    c1, c2, c3, c4 = generate_related_colours(hashes)
    return G(
        *make_grid_rects(
            size,
            next(hashes) % 2 + 3,
            c1, c2, c3, c4
        )
    )


if __name__ == '__main__':
    seed_str = bytes(randint(0, 255) for _ in range(10))
    s = Svg(
        make_grid(48, seed_str),
        witdh=48, height=48,
        viewBox=ViewBox(0, 0, 48, 48))
    tree = etree.ElementTree(s._etree)
    with open('../build/foo.svg', 'wb') as f:
        tree.write(
            f, pretty_print=True, xml_declaration=True, encoding='utf-8')
