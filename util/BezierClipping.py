import math, cmath
from collections import namedtuple

# -----------------------------------------------------------------------------
Bezier = namedtuple('Bezier', 'x0 y0 x1 y1 x2 y2 x3 y3')

def eval_cubic_bezier(bez, t):
    return (bez.x0*(1-t)**3 + 3*bez.x1*(1-t)**2*t \
            + 3*bez.x2*(1-t)*t**2 + bez.x3*t**3,
            bez.y0*(1-t)**3 + 3*bez.y1*(1-t)**2*t \
            + 3*bez.y2*(1-t)*t**2 + bez.y3*t**3)

def find_intersections(left, right, bottom, top, bez):
    def is_t_in(t, eps = 1e-5):
        pt = eval_cubic_bezier(bez, t)
        return left-eps <=pt[0]<= right+eps and top-eps <=pt[1]<= bottom+eps
    def find_cubic_root(a, b, c, d=None):
        ''' 
        solve ax^3 + bx^2 + cx + d = 0 

        reference
        =========
            http://www.physics.rutgers.edu/~masud
            /computing/WPark_recipes_in_python.html
        '''
        def quadratic(a, b, c=None):
            ''' solve ax^2 + bx + c = 0 '''
            if c:   a, b = b / float(a), c / float(a)
            t = a / 2.0
            r = t**2 - b
            if r >= 0:  y1 = math.sqrt(r)
            else:       y1 = cmath.sqrt(r)
            y2 = -y1
            return y1 - t, y2 - t
        def cbrt(x):
            if x >= 0:  return math.pow(x, 1.0/3.0)
            else:       return -math.pow(abs(x), 1.0/3.0)
        def polar(x, y, deg=0):     # radian if deg=0; degree if deg=1
            if deg:     return math.hypot(x,y), 180.0 * math.atan2(y,x)/math.pi
            else:       return math.hypot(x,y), math.atan2(y,x)
        if a == 0:
            y1, y2 = quadratic(b, c, d)
            return y1, y2, None
        a = float(a)
        if d:           # (ax^3 + bx^2 + cx + d = 0)
            a, b, c = b / a, c / a, d / a
        t = a / 3.0
        p, q = b - 3 * t**2, c - b * t + 2 * t**3
        u, v = quadratic(q, -(p/3.0)**3)
        if type(u) == type(0j): # complex cubic root
            r, w = polar(u.real, u.imag)
            y1 = 2 * cbrt(r) * math.cos(w / 3.0)
        else:           # real root
            y1 = cbrt(u) + cbrt(v)
        y2, y3 = quadratic(y1, p + y1**2)
        return y1 - t, y2 - t, y3 - t
    ax, bx = -bez.x0+3*bez.x1-3*bez.x2+bez.x3, 3*bez.x0-6*bez.x1+3*bez.x2
    cx, _dx = 3*bez.x1-3*bez.x0, bez.x0
    ay, by = -bez.y0+3*bez.y1-3*bez.y2+bez.y3, 3*bez.y0-6*bez.y1+3*bez.y2
    cy, _dy = 3*bez.y1-3*bez.y0, bez.y0
    ts = []
    ts += find_cubic_root(ax, bx, cx, _dx-left)
    ts += find_cubic_root(ax, bx, cx, _dx-right)
    ts += find_cubic_root(ay, by, cy, _dy-bottom)
    ts += find_cubic_root(ay, by, cy, _dy-top)
    intersections = [t for t in ts if t is not None \
                    and type(t) != complex and 0 <= t <= 1 and is_t_in(t)]
    return sorted(intersections)


if __name__ == '__main__':
    import cv2, numpy as np
    from random import randint
    w, h = 500, 500
    rect = (int(w*0.25), int(h*0.25), int(w*0.75), int(h*0.75))

    while True:
        vis = np.zeros((h,w,4), np.uint8)
        bezier = Bezier(randint(0,w-1),randint(0,h-1), 
                        randint(0,w-1),randint(0,h-1), 
                        randint(0,w-1),randint(0,h-1), 
                        randint(0,w-1),randint(0,h-1))
        print bezier
        ts = np.linspace(0,1, num=50)
        for start, end in zip(ts[:-1], ts[1:]):
            sx, sy = eval_cubic_bezier(bezier, start)
            ex, ey = eval_cubic_bezier(bezier, end)
            cv2.line(vis, (int(sx), int(sy)), (int(ex), int(ey)), 
                (0,0,255), 2, cv2.CV_AA)
        cv2.rectangle(vis, rect[:2], rect[2:], (255,0,0))

        ts = find_intersections(rect[0],rect[2],rect[3],rect[1], bezier)
        for i, t in enumerate(ts):
            x, y = eval_cubic_bezier(bezier, t)
            cv2.circle(vis, (int(x), int(y)), 2, (255,0,255), 2)
            cv2.putText(vis,'%d' % i, (int(x)+3, int(y)), 
                cv2.FONT_HERSHEY_PLAIN, 1.0, (0,255,0))
        cv2.circle(vis, bezier[:2], 2, (0,0,255), 5)

        cv2.namedWindow('raster')
        cv2.imshow('raster', vis[:,:,:3])
        cv2.waitKey(100)