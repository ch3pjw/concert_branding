from .ast import M, a, L


def square(size, x=0, y=0, anticlockwise=False):
    inss = (
        L(x, y + size),
        L(x + size, y + size),
        L(x + size, y),
        L(x, y)
    )
    if anticlockwise:
        inss = tuple(reversed(inss))
    return (M(x, y),) + inss


def circle(r, cx=0, cy=0, anticlockwise=False):
    return (
        M(cx, cy - r),
        a(r, r, 0, 0, int(anticlockwise), 0, 2 * r),
        a(r, r, 0, 0, int(anticlockwise), 0, -2 * r)
    )
