"""Small pieces shared by the revivals' build scripts: drawing fitted outlines into fontTools pens, and hinting."""
from fontTools.cu2qu import curve_to_quadratic


def draw(pen, contours, quad=False):
    """contours: lists of ('L', p0, p1) and ('C', p0, c1, c2, p3) segments in font units"""
    R = lambda p: (round(p[0], 1 if not quad else 0), round(p[1], 1 if not quad else 0))
    for c in contours:
        pen.moveTo(R(c[0][1]))
        for s in c:
            if s[0] == 'L': pen.lineTo(R(s[2]))
            elif quad:
                q = curve_to_quadratic([tuple(p) for p in s[1:]], 0.5)
                pen.qCurveTo(*[R(p) for p in q[1:]])
            else: pen.curveTo(*[R(p) for p in s[2:]])
        pen.closePath()


def autohint(path):
    """TrueType hinting by ttfautohint: aligns the baseline, x-height, cap height and stems to the pixel grid at
    small sizes (matters mainly on Windows at 1x)."""
    from ttfautohint import ttfautohint
    data = open(path, 'rb').read()
    out = ttfautohint(in_buffer=data, default_script='latn', fallback_script='latn',
                      hinting_range_min=8, hinting_range_max=50, increase_x_height=14)
    open(path, 'wb').write(out)
