#!/usr/bin/env python3
"""Science Brawl sprite generator — 'Cabinet Luminance' art direction.

Builds 64x64-per-frame sprite sheets (15 frames) for each of the 12 fighters.
All figures are drawn facing RIGHT; the game mirrors them at draw time.

Frame map:
  0-1  idle (breathe)      6 punch windup   10 special charge   13 hit
  2-5  walk cycle          7 punch extend   11 special release  14 block
                           8 kick windup    12 jump
                           9 kick extend
"""
import math, os
from PIL import Image

FRAME_W, FRAME_H, N_FRAMES = 64, 64, 15
BASELINE = 60                     # feet contact row
INK = (28, 21, 38, 255)           # deep violet ink for all outlines

# ---------------------------------------------------------------- palette ----
def hx(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))

def clamp(v): return max(0, min(255, int(v)))

def shift(rgb, mul, hue_to=None, amt=0.0):
    """Multiply value; optionally pull toward a hue anchor (hue-shifted shadows)."""
    r, g, b = [c * mul for c in rgb]
    if hue_to:
        r = r * (1 - amt) + hue_to[0] * amt
        g = g * (1 - amt) + hue_to[1] * amt
        b = b * (1 - amt) + hue_to[2] * amt
    return (clamp(r), clamp(g), clamp(b), 255)

VIOLET = (70, 40, 110)
CREAM  = (255, 244, 200)

def ramp(hexcol):
    base = hx(hexcol)
    return {
        'd': shift(base, 0.62, VIOLET, 0.18),   # shadow, pulled violet
        'b': shift(base, 1.00),
        'l': shift(base, 1.28, CREAM, 0.14),    # light, pulled warm
    }

# ---------------------------------------------------------------- parts ------
class Part:
    """One body part on its own layer: filled, shaded, ink-outlined, composited."""
    def __init__(self):
        self.img = Image.new('RGBA', (FRAME_W, FRAME_H), (0, 0, 0, 0))
        self.px = self.img.load()
        self.shade_color = None     # ramp whose 'b' pixels get auto-shaded

    def dot(self, x, y, c):
        if 0 <= x < FRAME_W and 0 <= y < FRAME_H:
            self.px[x, y] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.dot(x, y, c)

    def disc(self, cx, cy, r, c):
        rr = r * r + 0.4
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if (x - cx) ** 2 + (y - cy) ** 2 <= rr:
                    self.dot(x, y, c)

    def capsule(self, p1, p2, w, c):
        (x1, y1), (x2, y2) = p1, p2
        steps = max(1, int(math.hypot(x2 - x1, y2 - y1) * 2))
        for i in range(steps + 1):
            t = i / steps
            self.disc(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, w / 2, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(int(round(xs[j])), int(round(xs[j + 1])) + 1):
                    self.dot(x, y, c)

    def shade(self, rmp):
        """Auto rim-light: light on top edges, shadow on bottom edges of 'b' pixels."""
        base, d, l = rmp['b'], rmp['d'], rmp['l']
        w, h = FRAME_W, FRAME_H
        src = [[self.px[x, y] for y in range(h)] for x in range(w)]
        def a(x, y): return 0 <= x < w and 0 <= y < h and src[x][y][3] > 0
        for y in range(h):
            for x in range(w):
                if src[x][y] != base:
                    continue
                top = not a(x, y - 1)
                bot = not a(x, y + 1)
                if top and not bot:
                    self.px[x, y] = l
                elif bot or (not a(x + 1, y) and not top):
                    self.px[x, y] = d

    def outline(self):
        w, h = FRAME_W, FRAME_H
        src = [[self.px[x, y][3] > 0 for y in range(h)] for x in range(w)]
        for y in range(h):
            for x in range(w):
                if src[x][y]:
                    continue
                if ((x > 0 and src[x-1][y]) or (x < w-1 and src[x+1][y]) or
                        (y > 0 and src[x][y-1]) or (y < h-1 and src[x][y+1])):
                    self.px[x, y] = INK

def compose(frame, parts):
    for p in parts:
        p.outline()
        frame.alpha_composite(p.img)

# ---------------------------------------------------------------- poses ------
# Joints: shoulder-back SB, shoulder-front SF at y=24; hips HB(30,38) HF(34,38).
# Each pose: arm/leg chains (elbow, hand), (knee, foot); lean shifts shoulders;
# drop shifts the whole upper body down (crouch / breathe).
def P(**kw): return kw

POSES = [
    P(name='idle0', lean=1, drop=0,
      bArm=((27, 31), (30, 27)), fArm=((38, 32), (41, 27)),
      bLeg=((28, 48), (27, 59)), fLeg=((36, 48), (37, 59)), fists=True),
    P(name='idle1', lean=1, drop=1,
      bArm=((27, 32), (30, 28)), fArm=((38, 33), (41, 28)),
      bLeg=((28, 48), (27, 59)), fLeg=((36, 48), (37, 59)), fists=True),
    P(name='walk0', lean=2, drop=0,
      bArm=((35, 30), (38, 34)), fArm=((27, 30), (24, 34)),
      bLeg=((27, 47), (24, 58)), fLeg=((38, 46), (41, 58))),
    P(name='walk1', lean=2, drop=1,
      bArm=((32, 31), (34, 35)), fArm=((30, 31), (28, 35)),
      bLeg=((30, 47), (30, 56)), fLeg=((35, 47), (36, 59))),
    P(name='walk2', lean=2, drop=0,
      bArm=((27, 30), (24, 34)), fArm=((35, 30), (38, 34)),
      bLeg=((36, 46), (39, 58)), fLeg=((28, 47), (26, 58))),
    P(name='walk3', lean=2, drop=1,
      bArm=((30, 31), (28, 35)), fArm=((32, 31), (34, 35)),
      bLeg=((32, 47), (33, 59)), fLeg=((30, 47), (29, 56))),
    P(name='punch_wind', lean=-1, drop=1,
      bArm=((27, 31), (30, 27)), fArm=((36, 33), (33, 28)),
      bLeg=((28, 48), (26, 59)), fLeg=((36, 48), (36, 59)), fists=True),
    P(name='punch_ext', lean=4, drop=1,
      bArm=((26, 31), (24, 35)), fArm=((43, 25), (51, 25)),
      bLeg=((27, 49), (23, 59)), fLeg=((38, 48), (40, 59)), fists=True, big_fist=True),
    P(name='kick_wind', lean=0, drop=1,
      bArm=((27, 31), (30, 27)), fArm=((38, 31), (41, 27)),
      bLeg=((29, 48), (28, 59)), fLeg=((38, 31), (35, 38)), fists=True),
    P(name='kick_ext', lean=-3, drop=1,
      bArm=((36, 29), (39, 31)), fArm=((26, 29), (23, 33)),
      bLeg=((29, 48), (27, 59)), fLeg=((42, 33), (52, 31)), fists=True),
    P(name='sp_charge', lean=-1, drop=2,
      bArm=((33, 34), (36, 36)), fArm=((36, 34), (38, 35)),
      bLeg=((28, 48), (26, 59)), fLeg=((36, 48), (38, 59)), fists=True, glow=(40, 36)),
    P(name='sp_release', lean=4, drop=1,
      bArm=((39, 30), (47, 31)), fArm=((41, 27), (48, 27)),
      bLeg=((27, 49), (24, 59)), fLeg=((38, 48), (40, 59)), fists=True, glow=(50, 29)),
    P(name='jump', lean=2, drop=0,
      bArm=((27, 28), (25, 23)), fArm=((39, 29), (42, 25)),
      bLeg=((28, 44), (27, 52)), fLeg=((37, 44), (36, 52)), fists=True, airborne=True),
    P(name='hit', lean=-5, drop=2,
      bArm=((27, 29), (24, 25)), fArm=((39, 30), (43, 27)),
      bLeg=((27, 46), (28, 58)), fLeg=((38, 48), (41, 59)), hurt=True),
    P(name='block', lean=0, drop=2,
      bArm=((34, 34), (33, 26)), fArm=((38, 33), (37, 25)),
      bLeg=((27, 48), (25, 59)), fLeg=((37, 48), (39, 59)), fists=True),
]

# ---------------------------------------------------------------- figure -----
def draw_limb(part, origin, elbow, hand, w_upper, w_fore, rmp):
    part.capsule(origin, elbow, w_upper, rmp['b'])
    part.capsule(elbow, hand, w_fore, rmp['b'])

def draw_shoe(part, knee, foot, col_ramp, heel=False):
    kx, ky = knee; fx, fy = foot
    dx, dy = fx - kx, fy - ky
    n = math.hypot(dx, dy) or 1
    ex, ey = fx + dx / n * 1.8, fy + dy / n * 1.8
    part.capsule((fx, fy), (ex, ey), 3.4, col_ramp['b'])
    part.dot(int(ex), int(ey), col_ramp['l'])
    if heel:
        part.dot(int(fx - dx / n * 1.5), int(fy + 2), col_ramp['d'])

def head_center(pose):
    return (33 + pose.get('lean', 0), 13 + pose.get('drop', 0) - (1 if pose.get('hurt') else 0) - (2 if pose.get('hurt') else 0) * 0 )

# ---------------------------------------------------------------- heads ------
def draw_face(part, C, hx0, hy0, hurt=False):
    """Base face: skull, shading, eye, brow, nose, mouth, ear. (hx0,hy0)=center."""
    sk = C['skin']
    for dy in range(-8, 9):
        for dx in range(-7, 8):
            if (dx / 7.2) ** 2 + (dy / 8.2) ** 2 <= 1.0:
                part.dot(hx0 + dx, hy0 + dy, sk['b'])
    # back-of-head shadow + front highlight
    for dy in range(-8, 9):
        for dx in range(-7, 8):
            if (dx / 7.2) ** 2 + (dy / 8.2) ** 2 <= 1.0:
                if dx < -3: part.dot(hx0 + dx, hy0 + dy, sk['d'])
                elif dx > 4 and dy < 2: part.dot(hx0 + dx, hy0 + dy, sk['l'])
    # jaw shade
    for dx in range(-3, 6):
        part.dot(hx0 + dx, hy0 + 7, sk['d'])
    # ear
    part.rect(hx0 - 5, hy0 + 0, hx0 - 4, hy0 + 2, sk['d'])
    part.dot(hx0 - 5, hy0 + 1, INK)
    # nose
    part.dot(hx0 + 8, hy0 + 2, sk['b'])
    part.dot(hx0 + 8, hy0 + 3, sk['d'])
    # eye + brow (closed X when hurt)
    if hurt:
        part.dot(hx0 + 3, hy0 - 1, INK); part.dot(hx0 + 5, hy0 - 1, INK)
        part.dot(hx0 + 4, hy0 + 0, INK)
        part.dot(hx0 + 3, hy0 + 1, INK); part.dot(hx0 + 5, hy0 + 1, INK)
    else:
        part.rect(hx0 + 3, hy0 - 1, hx0 + 5, hy0 + 0, (250, 250, 255, 255))
        part.rect(hx0 + 5, hy0 - 1, hx0 + 5, hy0 + 0, (30, 30, 46, 255))
        part.rect(hx0 + 2, hy0 - 3, hx0 + 6, hy0 - 3, C['hair']['d'])
    # mouth
    part.rect(hx0 + 3, hy0 + 5, hx0 + 5, hy0 + 5, sk['d'])

def hair_einstein(p, C, x, y):
    h = C['hair']
    for a in range(0, 19):
        ang = math.pi * (0.02 + 0.96 * a / 18)
        rr = 8.5 + (2.6 if a % 2 else 0.6) + (1.4 if a % 3 == 0 else 0)
        p.disc(x - math.cos(ang) * rr * 0.9, y - 3 - math.sin(ang) * rr * 0.62, 2.6, h['b'] if a % 2 else h['l'])
    p.capsule((x - 8, y - 4), (x + 7, y - 5), 5, h['b'])
    p.rect(x + 2, y + 3, x + 6, y + 4, h['l'])          # mustache
    p.rect(x + 3, y + 5, x + 5, y + 5, h['b'])

def hair_tesla(p, C, x, y):
    h = C['hair']
    p.capsule((x - 6, y - 6), (x + 5, y - 6), 6, h['b'])
    p.rect(x - 7, y - 7, x + 6, y - 4, h['b'])
    p.rect(x - 7, y - 4, x - 5, y + 1, h['b'])
    p.rect(x - 1, y - 8, x - 1, y - 5, h['d'])          # center part
    p.rect(x - 6, y - 8, x - 2, y - 7, h['l'])          # sheen
    p.rect(x + 2, y + 4, x + 5, y + 4, h['b'])          # thin mustache

def hair_curie(p, C, x, y):
    h = C['hair']
    p.capsule((x - 5, y - 6), (x + 4, y - 6), 6.5, h['b'])
    p.rect(x - 7, y - 6, x + 5, y - 3, h['b'])
    p.rect(x - 8, y - 4, x - 6, y + 2, h['b'])
    p.disc(x - 8, y + 1, 3.2, h['b'])                    # low bun
    p.disc(x - 9, y + 0, 1.6, h['d'])
    p.rect(x - 4, y - 8, x + 3, y - 7, h['l'])          # sheen sweep

def hair_newton(p, C, x, y):
    h = C['hair']
    p.capsule((x - 6, y - 6), (x + 5, y - 6), 6.5, h['b'])
    for s, xx in ((0, x - 8), (1, x + 7)):
        for j in range(5):
            p.disc(xx + (1 if s else -1) * (j % 2), y - 3 + j * 3.1, 2.5, h['d'] if j % 2 else h['b'])
    p.rect(x - 5, y - 8, x + 4, y - 7, h['l'])

def hair_darwin(p, C, x, y):
    h = C['hair']
    p.rect(x - 7, y - 3, x - 5, y + 1, h['b'])           # side fringe
    p.rect(x + 4, y - 3, x + 6, y - 1, h['b'])
    for dy in range(2, 10):
        wdt = 7 - max(0, dy - 7)
        p.rect(x - wdt + 1, y + dy, x + wdt + 1, y + dy, h['b'] if dy < 6 else h['d'])
    p.rect(x + 3, y + 5, x + 5, y + 5, C['skin']['d'])   # mouth peeks out

def hair_hawking(p, C, x, y):
    h = C['hair']
    p.capsule((x - 5, y - 6), (x + 4, y - 6), 5.5, h['b'])
    p.rect(x - 7, y - 6, x + 5, y - 4, h['b'])
    p.rect(x - 7, y - 6, x - 2, y - 5, h['d'])
    # round glasses
    g = (32, 46, 58, 255)
    for cx in (x + 1, x + 6):
        for ang in range(0, 360, 18):
            p.dot(int(cx + 2.2 * math.cos(math.radians(ang))), int(y - 0.2 + 2.2 * math.sin(math.radians(ang))), g)
    p.dot(x + 4, y + 0, g)

def hair_ada(p, C, x, y):
    h = C['hair']
    p.capsule((x - 5, y - 6), (x + 4, y - 6), 6.5, h['b'])
    p.rect(x - 7, y - 6, x + 5, y - 2, h['b'])
    p.rect(x - 1, y - 9, x, y - 5, h['d'])               # center part
    p.disc(x - 3, y - 9, 2.4, h['b'])                    # crown updo
    for j in range(4):                                    # side ringlets
        p.disc(x - 8, y - 1 + j * 2.6, 1.9, h['d'] if j % 2 else h['b'])
    p.dot(x - 3, y - 10, C['accent']['b'])               # jeweled pin

def hair_franklin(p, C, x, y):
    h = C['hair']
    p.capsule((x - 5, y - 6), (x + 5, y - 6), 7, h['b'])
    p.rect(x - 8, y - 6, x + 6, y - 2, h['b'])
    p.rect(x - 8, y - 3, x - 6, y + 4, h['b'])           # bob sides
    p.rect(x + 5, y - 3, x + 6, y + 1, h['b'])
    for i in range(3):                                    # 50s waves
        p.capsule((x - 7 + i, y - 6 + i * 3), (x - 5 + i, y - 5 + i * 3), 1.6, h['l'])
    p.rect(x - 2, y - 8, x + 4, y - 7, h['l'])

def hair_johnson(p, C, x, y):
    h = C['hair']
    for i in range(-3, 4):
        p.disc(x + i * 2.1, y - 6.5 - (0.9 if i % 2 else 0), 2.5, h['b'] if i % 2 else h['d'])
    p.rect(x - 6, y - 5, x + 5, y - 4, h['b'])
    g = (32, 46, 58, 255)                                # cat-eye glasses
    p.rect(x + 1, y - 1, x + 3, y + 0, (0, 0, 0, 0))
    for cx in (x + 2, x + 6):
        p.rect(cx - 1, y - 1, cx + 1, y + 0, g)
        p.dot(cx + 1, y - 2, g)                          # upswept corner
    p.rect(x + 4, y - 1, x + 4, y - 1, g)
    p.rect(x + 2, y - 1, x + 2, y - 1, (250, 250, 255, 255))
    p.dot(x - 4, y + 3, (223, 120, 140, 255))            # earring

def hair_galileo(p, C, x, y):
    h = C['hair']
    p.rect(x - 8, y - 2, x - 6, y + 5, h['b'])           # long sides
    p.rect(x + 5, y - 2, x + 7, y + 3, h['b'])
    cap = C['coat']
    p.capsule((x - 5, y - 7), (x + 4, y - 7), 5.5, cap['d'])   # scholar's cap
    p.rect(x - 7, y - 7, x + 5, y - 5, cap['d'])
    p.rect(x - 7, y - 8, x + 5, y - 8, cap['b'])
    for dy in range(2, 9):                                # full beard
        wdt = 6 - max(0, dy - 6)
        p.rect(x - wdt + 1, y + dy, x + wdt + 1, y + dy, h['b'] if dy < 6 else h['d'])

def hair_turing(p, C, x, y):
    h = C['hair']
    p.capsule((x - 5, y - 6), (x + 4, y - 6), 6, h['b'])
    p.rect(x - 7, y - 6, x + 5, y - 3, h['b'])
    p.rect(x + 1, y - 8, x + 2, y - 4, h['l'])           # side part sheen
    p.rect(x - 7, y - 6, x - 3, y - 5, h['d'])

def hair_archimedes(p, C, x, y):
    h = C['hair']
    for i in range(-3, 4):
        p.disc(x + i * 2.1, y - 6 - (0.8 if i % 2 else 0), 2.3, h['b'] if i % 2 else h['d'])
    for dy in range(2, 10):                               # grand beard
        wdt = 7 - max(0, dy - 6)
        p.rect(x - wdt + 1, y + dy, x + wdt + 1, y + dy, h['b'] if dy < 7 else h['d'])
    lv = (111, 174, 78, 255)                              # laurel wreath
    for i in range(-3, 4):
        p.dot(x + i * 2, y - 8 + (1 if i % 2 else 0), lv)
        p.dot(x + i * 2 + 1, y - 7 + (1 if i % 2 else 0), (86, 140, 60, 255))

HEADS = {
    'einstein': hair_einstein, 'tesla': hair_tesla, 'curie': hair_curie,
    'newton': hair_newton, 'darwin': hair_darwin, 'hawking': hair_hawking,
    'ada': hair_ada, 'franklin': hair_franklin, 'johnson': hair_johnson,
    'galileo': hair_galileo, 'turing': hair_turing, 'archimedes': hair_archimedes,
}

# ---------------------------------------------------------------- torso ------
def draw_torso(part, C, lean, drop, female, labcoat):
    co = C['coat']
    sx, sy = 31 + lean, 23 + drop
    hxp, hyp = 31 + lean * 0.3, 37 + drop
    part.capsule((sx, sy + 2), (hxp, hyp - 1), 12, co['b'])
    part.capsule((sx - 3, sy + 1), (sx + 4, sy + 1), 6, co['b'])       # shoulders
    if labcoat:                                                          # coat tails
        part.poly([(sx - 6, hyp - 2), (sx + 6, hyp - 2), (sx + 7, hyp + 5), (sx - 7, hyp + 5)], co['b'])
        part.rect(int(sx), int(hyp + 1), int(sx), int(hyp + 5), co['d'])  # slit
    # shirt V
    sh = (243, 240, 230, 255)
    part.poly([(sx - 3, sy - 0.5), (sx + 4, sy - 0.5), (sx + 0.5, sy + 7)], sh)
    if female:
        part.rect(int(sx) - 1, int(sy + 2), int(sx) + 1, int(sy + 4), C['accent']['b'])   # brooch
        part.dot(int(sx), int(sy + 3), C['accent']['l'])
    else:
        part.rect(int(sx), int(sy + 1), int(sx) + 1, int(sy + 8), C['accent']['b'])       # tie
        part.rect(int(sx), int(sy + 1), int(sx) + 1, int(sy + 2), C['accent']['d'])
        part.dot(int(sx) + 4, int(sy + 5), co['l'])                                        # buttons
        part.dot(int(sx) + 4, int(sy + 8), co['l'])
        part.rect(int(sx) - 5, int(hyp - 2), int(sx) + 5, int(hyp - 1), shift(hx('#221c16'), 1.0))

def draw_skirt(part, C, lean, drop):
    co = C['coat']
    sx = 31 + lean * 0.3
    top, bot = 36 + drop, 46 + drop
    part.poly([(sx - 5, top), (sx + 5, top), (sx + 8, bot), (sx - 8, bot)], co['b'])
    for i in (-4, 0, 4):
        part.rect(int(sx + i), int(top + 2), int(sx + i), int(bot - 1), co['d'])
    part.rect(int(sx - 8), int(bot), int(sx + 8), int(bot), co['l'])

def draw_chair(back, front, C, roll):
    """Hawking's chair: 'back' behind torso, 'front' over legs. roll = wheel angle."""
    fr = {'d': (52, 54, 66, 255), 'b': (73, 76, 92, 255), 'l': (108, 112, 132, 255)}
    back.rect(23, 26, 26, 45, fr['b'])                    # backrest
    back.rect(23, 26, 24, 45, fr['d'])
    back.rect(23, 25, 26, 25, fr['l'])
    front.rect(24, 44, 40, 47, fr['b'])                   # seat
    front.rect(24, 47, 40, 47, fr['d'])
    front.rect(37, 48, 40, 55, fr['d'])                   # leg support
    front.rect(36, 55, 42, 56, fr['b'])                   # footrest
    # big wheel
    cx, cy, R = 29, 52, 7.5
    for ang in range(0, 360, 4):
        a = math.radians(ang)
        front.dot(int(cx + R * math.cos(a)), int(cy + R * math.sin(a)), fr['l'])
        front.dot(int(cx + (R - 1) * math.cos(a)), int(cy + (R - 1) * math.sin(a)), fr['b'])
    for s in range(3):                                    # spokes rotate with 'roll'
        a = roll + s * math.pi / 3 * 2
        front.capsule((cx - (R - 2) * math.cos(a), cy - (R - 2) * math.sin(a)),
                      (cx + (R - 2) * math.cos(a), cy + (R - 2) * math.sin(a)), 1.4, fr['d'])
    front.disc(cx, cy, 1.6, C['accent']['b'])
    # caster
    front.disc(43, 57, 2.6, fr['b'])
    front.disc(43, 57, 1.0, fr['d'])
    front.dot(44, 50, C['accent']['b'])                   # control panel light

# ---------------------------------------------------------------- figure -----
SHOE = {'d': (14, 12, 22, 255), 'b': (34, 32, 48, 255), 'l': (60, 58, 80, 255)}

def render_frame(char, pose, f_index):
    C = char['C']
    frame = Image.new('RGBA', (FRAME_W, FRAME_H), (0, 0, 0, 0))
    lean, drop = pose.get('lean', 0), pose.get('drop', 0)
    seated = char['id'] == 'hawking'
    parts = []

    # --- back arm ---
    pa = Part()
    sb = (29 + lean, 24 + drop + (2 if seated else 0))
    e, hnd = pose['bArm']
    draw_limb(pa, sb, e, hnd, 5.4, 4.8, C['coat'])
    pa.shade(C['coat'])
    hr = 2.6 if pose.get('fists') else 2.3
    pa.disc(hnd[0], hnd[1], hr, C['skin']['d'])
    parts.append(pa)

    if seated:
        chair_back, chair_front = Part(), Part()
        roll = [0, 0.35, 0.7, 1.05, 1.4, 1.75][f_index % 6] if 2 <= f_index <= 5 else 0.2
        draw_chair(chair_back, chair_front, C, roll)
        parts.append(chair_back)
        # bent seated legs
        pl = Part()
        pl.capsule((31, 42), (37, 46), 6.5, C['pants']['b'])
        pl.capsule((37, 46), (38, 53), 5.5, C['pants']['b'])
        pl.shade(C['pants'])
        pl.capsule((38, 53), (41, 54), 4.2, SHOE['b'])
        parts.append(pl)
    else:
        # --- back leg ---
        pl = Part()
        hb = (30 + lean * 0.2, 38 + drop)
        k, ft = pose['bLeg']
        draw_limb(pl, hb, k, ft, 6.2, 5.4, C['pants'])
        pl.shade(C['pants'])
        draw_shoe(pl, k, ft, SHOE, heel=char.get('female'))
        parts.append(pl)
        # --- front leg ---
        pl2 = Part()
        hf = (33 + lean * 0.2, 38 + drop)
        k2, ft2 = pose['fLeg']
        draw_limb(pl2, hf, k2, ft2, 6.8, 5.8, C['pants'])
        pl2.shade(C['pants'])
        draw_shoe(pl2, k2, ft2, SHOE, heel=char.get('female'))
        parts.append(pl2)

    # --- torso ---
    pt = Part()
    draw_torso(pt, C, lean, drop + (2 if seated else 0), char.get('female'), char.get('labcoat'))
    parts.append(pt)

    # --- skirt ---
    if char.get('female') and not seated:
        ps = Part()
        draw_skirt(ps, C, lean, drop)
        parts.append(ps)

    if seated:
        parts.append(chair_front)

    # --- head ---
    ph = Part()
    hx0 = 33 + lean + (-2 if pose.get('hurt') else 0)
    hy0 = 13 + drop + (2 if seated else 0)
    draw_face(ph, C, hx0, hy0, hurt=pose.get('hurt'))
    HEADS[char['id']](ph, C, hx0, hy0)
    parts.append(ph)

    # --- front arm ---
    pf = Part()
    sf = (34 + lean, 24 + drop + (2 if seated else 0))
    e2, hnd2 = pose['fArm']
    draw_limb(pf, sf, e2, hnd2, 5.8, 5.2, C['coat'])
    pf.shade(C['coat'])
    fr2 = 3.2 if pose.get('big_fist') else (2.8 if pose.get('fists') else 2.4)
    pf.disc(hnd2[0], hnd2[1], fr2, C['skin']['b'])
    pf.dot(int(hnd2[0]), int(hnd2[1] - 2), C['skin']['l'])
    parts.append(pf)

    compose(frame, parts)

    # --- special-charge glow (drawn over ink, unoutlined) ---
    if pose.get('glow'):
        gx, gy = pose['glow']
        ac = C['accent']
        glow = Part()
        glow.disc(gx, gy, 3.4 if pose['name'] == 'sp_charge' else 4.4, ac['b'])
        glow.disc(gx, gy, 1.6, ac['l'])
        for k in range(4):
            a = k * math.pi / 2 + 0.4
            r0 = 5 if pose['name'] == 'sp_charge' else 6.5
            glow.dot(int(gx + r0 * math.cos(a)), int(gy + r0 * math.sin(a)), ac['l'])
        frame.alpha_composite(glow.img)

    return frame

# ---------------------------------------------------------------- roster -----
ROSTER = [
    dict(id='einstein', skin='#e8b98c', hair='#e9e9ef', coat='#7d7d86', pants='#4a4a52', accent='#8fd6ff', labcoat=True),
    dict(id='tesla', skin='#e6c9a0', hair='#241d1a', coat='#38384a', pants='#26262f', accent='#b98bff'),
    dict(id='curie', skin='#e7b892', hair='#2a211c', coat='#3a3446', pants='#352c42', accent='#8dff9e', female=True),
    dict(id='newton', skin='#e8bd95', hair='#c9c4b8', coat='#5b3b2a', pants='#3a2519', accent='#ffd36b'),
    dict(id='darwin', skin='#e4b189', hair='#d8d2c4', coat='#3d4a3a', pants='#26301f', accent='#9be07a'),
    dict(id='hawking', skin='#e8bd95', hair='#8a8a92', coat='#2b2f3a', pants='#20242c', accent='#c48bff'),
    dict(id='ada', skin='#e9bd98', hair='#3a2a22', coat='#3b2d55', pants='#2a2038', accent='#ffd36b', female=True),
    dict(id='franklin', skin='#e7b892', hair='#2b211d', coat='#c9ccd6', pants='#3a3a44', accent='#ff5ea8', female=True, labcoat=True),
    dict(id='johnson', skin='#8a5a3c', hair='#241a16', coat='#3f5a7a', pants='#26313f', accent='#eaf2ff', female=True),
    dict(id='galileo', skin='#e3b089', hair='#b8b2a4', coat='#6a4a2c', pants='#3e2a18', accent='#ffcf6b'),
    dict(id='turing', skin='#e8bd95', hair='#4a3a2c', coat='#42505a', pants='#2b333a', accent='#8dff9e'),
    dict(id='archimedes', skin='#d99f74', hair='#e6e2d6', coat='#d8d2c0', pants='#b8b2a0', accent='#ffcf5a'),
]

def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sheets')
    os.makedirs(out, exist_ok=True)
    contact_rows = []
    for char in ROSTER:
        char['C'] = {k: ramp(char[k]) for k in ('skin', 'hair', 'coat', 'pants', 'accent')}
        sheet = Image.new('RGBA', (FRAME_W * N_FRAMES, FRAME_H), (0, 0, 0, 0))
        for i, pose in enumerate(POSES):
            sheet.paste(render_frame(char, pose, i), (i * FRAME_W, 0))
        sheet.save(os.path.join(out, f"{char['id']}.png"), optimize=True)
        contact_rows.append(sheet)
        print('generated', char['id'])
    # contact sheet at 2x on dark ground for review
    cs = Image.new('RGBA', (FRAME_W * N_FRAMES * 2, FRAME_H * len(contact_rows) * 2), (24, 22, 38, 255))
    for r, sheet in enumerate(contact_rows):
        cs.alpha_composite(sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST), (0, r * FRAME_H * 2))
    cs.save(os.path.join(out, '_contact.png'))
    print('contact sheet written')

if __name__ == '__main__':
    main()
