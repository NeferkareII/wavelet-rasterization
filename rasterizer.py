import math, copy
from collections import namedtuple

# -----------------------------------------------------------------------------
Point = namedtuple('Point', 'x y')
# -----------------------------------------------------------------------------

class Rasterizer:

    def __init__(self, contour, w, h):
        self.w = w
        self.h = h
        self.max_j = int(math.ceil(math.log(max(w,h), 2)))-1
        self.wh = 2 ** (self.max_j+1)
        def normalize(p):   return (p[0]/float(self.wh), p[1]/float(self.wh))
        self.contour = copy.deepcopy(contour)
        self.contour.process(normalize)
        self.area = self.contour.area()
        self.lattice = [Point(*normalize((x,y))) \
                        for x in xrange(h) for y in xrange(w)]
        # prepare all c
        self.all_c = {}
        for j in xrange(self.max_j+1):
            for kx in xrange(2**j):
                for ky in xrange(2**j):
                    self.all_c[(j, kx,ky)] = self.c(j, (kx,ky))

    def psi(self, p, e, j, k):
        def psi_1d(p, e):
            if e == 0:   return 1 if 0 <= p < 1 else 0
            else:        return (1 if 0<=p<0.5 else -1) if 0 <= p < 1 else 0 
        return 2**j * psi_1d(2**j*p.x-k.x, e.x) * psi_1d(2**j*p.y-k.y, e.y)

    def c(self, j, k):
        def transform(section, Q):
            return (2**(j+1)*p[i]-k[i]*2-Q[i] \
                    for p in section for i in xrange(2))
        Q_00, Q_01 = Point(0, 0), Point(0, 1)
        Q_10, Q_11 = Point(1, 0), Point(1, 1)
        c10, c01, c11 = 0, 0, 0
        for section in self.contour.each():
            KQ00, LQ00 = self.contour.get_KL(transform(section, Q_00))
            KQ01, LQ01 = self.contour.get_KL(transform(section, Q_01))
            KQ10, LQ10 = self.contour.get_KL(transform(section, Q_10))
            KQ11, LQ11 = self.contour.get_KL(transform(section, Q_11))
            c10 += LQ00.x + LQ01.x + KQ10.x \
                 - LQ10.x + KQ11.x - LQ11.x
            c01 += LQ00.y + LQ10.y + KQ01.y \
                 - LQ01.y + KQ11.y - LQ11.y
            c11 += LQ00.x - LQ01.x + KQ10.x \
                 - LQ10.x - KQ11.x + LQ11.x
        return c01, c10, c11

    def g(self, p):
        s = self.area
        E = [Point(0,1), Point(1,0), Point(1,1)]
        for j in xrange(self.max_j+1):
            for kx in xrange(2**j):
                for ky in xrange(2**j):
                    k = Point(kx, ky)
                    cs = self.all_c[(j, kx,ky)]
                    for i, e in enumerate(E):
                        psi = self.psi(p, e, j, k)
                        if psi > 0:     s += cs[i]
                        elif psi < 0:   s -= cs[i]
        return s

    def g_fast(self, p):
        s = self.area
        E = (Point(0,1), Point(1,0), Point(1,1))
        for j in xrange(self.max_j+1):
            exp_j = 2**j
            exp_jpx, exp_jpy = exp_j*p.x, exp_j*p.y
            for kx in xrange(exp_j):
                for ky in xrange(exp_j):
                    cs = self.all_c[(j,kx,ky)]
                    exp_jpkx, exp_jpky = exp_jpx-kx, exp_jpy-ky
                    if exp_jpkx < 0 or exp_jpkx >= 1:     continue
                    if exp_jpky < 0 or exp_jpky >= 1:     continue
                    for i, e in enumerate(E):
                        neg_x = exp_jpkx >= 0.5 and e.x != 0
                        neg_y = exp_jpky >= 0.5 and e.y != 0
                        if neg_x and not neg_y or not neg_x and neg_y: 
                            s -= cs[i]
                        else:   
                            s += cs[i]
        return s

    def get(self):
        px_arr = [self.g_fast(p) for p in self.lattice]
        px_mat = [px_arr[i*self.w : (i+1)*self.w] for i in xrange(self.h)]
        return px_mat

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import cv2, numpy as np,time
    from contour import *

    ts = time.time()
    contour= Line.Contour([(4,4), (30,6), (10,14)])
    raster = Rasterizer(contour, 32, 32).get()
    raster = np.array(np.asarray(raster)*255+0.5, np.uint8)
    cv2.imwrite('var/Line.png', raster)

    contour= QuadraticBezier.Contour([(4,4), (28,4), (28,28), (4,28)])
    raster = Rasterizer(contour, 32, 32).get()
    raster = np.array(np.asarray(raster)*255+0.5, np.uint8)
    cv2.imwrite('var/QuadraticBezier.png', raster)

    contour= CubicBezier.Contour([(4,4),(12,4),(28,12),(28,28),(12,28),(4,12)])
    raster = Rasterizer(contour, 32, 32).get()
    raster = np.array(np.asarray(raster)*255+0.5, np.uint8)
    cv2.imwrite('var/CubicBezier.png', raster)
    print time.time() - ts