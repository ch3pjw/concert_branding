from .ast import M, H, V, a


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
