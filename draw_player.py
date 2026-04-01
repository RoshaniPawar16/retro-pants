"""
retro-pants — draw_player.py  (v7)

Key fixes:
  - Ellipse for head (round, chibi). Rects = minecraft blocks at this scale.
  - Hair drawn FIRST as a shifted ellipse, then skin face drawn ON TOP —
    skin naturally covers the lower hair, leaving only the crown visible.
  - Blue jacket so the body doesn't blend with brown hair/boots.
  - Proportions: huge head (chibi), compact body.

Integration unchanged:
  from draw_player import draw_fancy_player
"""

import pygame
import math

# palette
O  = (15,  8,   3)     # outline
H  = (48,  28,  8)     # hair dark
Hh = (105, 72,  28)    # hair highlight
S  = (238, 195, 154)   # skin
Ss = (200, 158, 112)   # skin shadow
EW = (255, 255, 255)   # eye white
EI = (35,  148, 136)   # teal iris
EP = (10,   48,  44)   # eye pupil
BL = (215, 105,  90)   # blush
CR = (230, 222, 200)   # cream collar
JA = (62,  88,  150)   # jacket blue
JS = (38,  56,  105)   # jacket shadow
JH = (95,  130, 195)   # jacket highlight
BE = (48,  28,  10)    # belt
BK = (190, 158,  52)   # buckle brass
PA = (70,  48,  26)    # pants
PS = (46,  30,  12)    # pants shadow
BO = (36,  20,   7)    # boot
BH = (62,  40,  18)    # boot highlight
BS = (20,  10,   3)    # boot sole


def draw_fancy_player(surf, player, cam_x):
    px    = int(player.x) - cam_x
    py    = int(player.y)
    f     = player.facing
    s     = player.state
    vx    = player.vx
    vy    = player.vy
    fr    = player.anim_frame
    ticks = pygame.time.get_ticks()

    fx = px + 11
    fy = py + 30

    # squash / stretch
    sq = getattr(player, 'land_squash', 0)
    if sq > 0:
        t = sq / 7.0
        hw, hh, bh = int(22 + 6*t), int(22 - 4*t), int(10 - 2*t)
    elif s == "jump" and vy < -3:
        hw, hh, bh = 18, 26, 9
    elif s == "fall" and vy > 4:
        hw, hh, bh = 24, 18, 12
    else:
        hw, hh, bh = 22, 22, 10   # big round head, compact body

    bob  = int(math.sin(ticks * 0.003) * 2) if abs(vx) < 0.5 else 0
    lean = int(f * min(abs(vx) * 0.5, 4)) if s in ("run","skid") and abs(vx) > 2 else 0

    # layout (bottom-up)
    boot_h = 7
    leg_h  = 5
    boot_y = fy + bob - boot_h
    leg_y  = boot_y - leg_h
    body_y = leg_y - bh
    # head centre
    hcx = fx + lean
    hcy = body_y - hh // 2 - 1

    # ── shadow ────────────────────────────────────────────────────────────────
    _aellipse(surf, (5, 3, 1, 45), fx - 15, fy - 2, 30, 4)

    # ── boots ─────────────────────────────────────────────────────────────────
    _boots(surf, fx, boot_y, boot_h, s, fr, bob, lean)

    # ── legs ──────────────────────────────────────────────────────────────────
    _legs(surf, fx, leg_y, leg_h, s, fr, bob, lean)

    # ── body ──────────────────────────────────────────────────────────────────
    _body(surf, fx, body_y, bh, lean)

    # ── HAIR first (ellipse shifted up) ───────────────────────────────────────
    # draw hair BEFORE skin so skin covers the lower part naturally
    _hair_base(surf, hcx, hcy, hw, hh, f, s, vx, ticks)

    # ── skin head (ellipse on top of hair — covers lower hair) ────────────────
    hx = hcx - hw // 2
    hy = hcy - hh // 2
    pygame.draw.ellipse(surf, O, (hx - 1, hy - 1, hw + 2, hh + 2))
    pygame.draw.ellipse(surf, S, (hx, hy, hw, hh))
    # left-side shading strip
    _aellipse(surf, (*Ss, 55), hx, hy, hw // 2, hh)
    pygame.draw.ellipse(surf, O, (hx, hy, hw, hh), 2)

    # ── cream collar ──────────────────────────────────────────────────────────
    cy = hy + hh - 4
    pygame.draw.ellipse(surf, O,  (hcx - 8, cy,     16, 8))
    pygame.draw.ellipse(surf, CR, (hcx - 7, cy + 1, 14, 6))

    # ── eyes (drawn after skin so they're on top) ──────────────────────────────
    _eyes(surf, hcx, hcy, hw, hh, f, s, vx, vy, player, ticks)

    # ── speed lines ───────────────────────────────────────────────────────────
    if abs(vx) > 4:
        _speed(surf, hcx, hcy, hh // 2, f, abs(vx))


def _hair_base(surf, cx, cy, hw, hh, f, s, vx, ticks):
    """
    Hair ellipse shifted UP so only the crown peeks above the skin ellipse.
    After this, the skin ellipse is drawn on top, covering the lower hair.
    """
    # shift the hair ellipse up by ~hh/3 so the crown peeks out
    shift = hh // 3
    hx = cx - (hw + 4) // 2
    hy = cy - hh // 2 - shift

    # shadow
    pygame.draw.ellipse(surf, O,  (hx + 1, hy + 2, hw + 4, hh))
    # fill
    pygame.draw.ellipse(surf, H,  (hx,     hy,     hw + 4, hh))
    # highlight streak
    pygame.draw.ellipse(surf, Hh, (cx + 1, hy + 2, hw // 4, hh // 4))
    pygame.draw.ellipse(surf, O,  (hx,     hy,     hw + 4, hh), 2)

    # front tuft (drawn above the skin ellipse — so it's after skin in caller,
    # but for the base we just note the position; tuft is drawn in _hair_tuft)
    _hair_tuft(surf, cx, hy + hh - shift, f, s, vx, ticks)


def _hair_tuft(surf, cx, base_y, f, s, vx, ticks):
    """Small front tuft sitting at the hairline."""
    speed = abs(vx)
    if s in ("run", "skid") and speed > 2:
        tx = cx + f * int(min(speed * 1.2, 7))
    else:
        tx = cx + int(math.sin(ticks * 0.0015) * 1.5)
    tuft = [(tx - 3, base_y), (tx, base_y - 7), (tx + 3, base_y)]
    pygame.draw.polygon(surf, O,  [(x+1, y+1) for x, y in tuft])
    pygame.draw.polygon(surf, Hh, tuft)
    pygame.draw.polygon(surf, O,  tuft, 1)


def _eyes(surf, cx, cy, hw, hh, f, s, vx, vy, player, ticks):
    speed = abs(vx)
    # eyes sit in the lower 60% of the face (below the hair crown)
    ey   = cy + hh // 8
    le_x = cx - hw // 5
    re_x = cx + hw // 5

    ew, eh = 6, 8

    sq = getattr(player, 'land_squash', 0)
    if sq > 3:
        for ex in (le_x, re_x):
            pygame.draw.ellipse(surf, EW, (ex - 4, ey - 2, 8, 6))
            pygame.draw.arc(surf, O, (ex - 4, ey - 2, 8, 6), 0, math.pi, 2)
        pygame.draw.arc(surf, O, (cx - 4, ey + 3, 8, 4), math.pi, 2*math.pi, 1)
        _blush(surf, le_x, re_x, ey)
        return

    if speed < 0.5 and (ticks // 16) % 220 < 5:
        for ex in (le_x, re_x):
            pygame.draw.ellipse(surf, EW, (ex - ew//2, ey - 1, ew, 3))
        return

    if s == "jump" and vy < -3:
        ew, eh = 6, 10; pdx, pdy = 0, -2
    elif s == "fall" and vy > 4:
        ew, eh = 7, 7;  pdx, pdy = 0, 2
    elif speed > 5:
        ew, eh = 8, 5;  pdx, pdy = f*3, 0
    elif speed > 2:
        pdx, pdy = f*1, 0
    else:
        pdx = int(math.sin(ticks * 0.0015) * 1.2)
        pdy = 0

    for ex in (le_x, re_x):
        pygame.draw.ellipse(surf, O,
                            (ex - ew//2 - 1, ey - eh//2 - 1, ew + 2, eh + 2))
        pygame.draw.ellipse(surf, EW,
                            (ex - ew//2, ey - eh//2, ew, eh))
        ix = max(ex - ew//2 + 2, min(ex + ew//2 - 2, ex + pdx))
        iy = max(ey - eh//2 + 2, min(ey + eh//2 - 2, ey + pdy))
        pygame.draw.circle(surf, EI, (ix, iy), 3)
        pygame.draw.circle(surf, EP, (ix, iy), 2)
        surf.set_at((ix + 1, iy - 1), EW)
        surf.set_at((ix + 2, iy - 1), EW)
        # top lash
        pygame.draw.arc(surf, O,
                        (ex - ew//2 - 1, ey - eh//2 - 1, ew + 2, eh + 2),
                        math.pi * 0.1, math.pi * 0.9, 2)

    brow_y = ey - eh//2 - 4
    if speed > 5 and s == "run":
        pygame.draw.line(surf, H, (le_x-4, brow_y-2), (le_x+3, brow_y), 2)
        pygame.draw.line(surf, H, (re_x-3, brow_y),   (re_x+4, brow_y-2), 2)
    elif s == "jump" and vy < -3:
        for ex in (le_x, re_x):
            pygame.draw.arc(surf, H, (ex-5, brow_y-4, 10, 6), math.pi, 2*math.pi, 2)
    else:
        pygame.draw.line(surf, H, (le_x-3, brow_y), (le_x+3, brow_y-1), 2)
        pygame.draw.line(surf, H, (re_x-3, brow_y-1), (re_x+3, brow_y), 2)

    _blush(surf, le_x, re_x, ey)

    if abs(vx) < 1 and s not in ("jump","fall","roll"):
        pygame.draw.arc(surf, O, (cx-4, ey+eh//2+1, 8, 4), math.pi, 2*math.pi, 1)


def _blush(surf, le_x, re_x, ey):
    _acircle(surf, (*BL, 90), le_x - 5, ey + 4, 3)
    _acircle(surf, (*BL, 90), re_x + 5, ey + 4, 3)


def _body(surf, fx, by, bh, lean):
    bx = fx - 9 + lean
    bw = 18
    pygame.draw.rect(surf, O,  (bx-1, by-1, bw+2, bh+2), border_radius=4)
    pygame.draw.rect(surf, JA, (bx,   by,   bw,   bh),   border_radius=4)
    pygame.draw.rect(surf, JS, (bx,   by+1, 4,    bh-2), border_radius=2)
    pygame.draw.rect(surf, JH, (bx+bw-5, by+1, 4, bh//3), border_radius=2)
    # belt
    belt_y = by + bh - 4
    pygame.draw.rect(surf, BE, (bx+1, belt_y, bw-2, 4))
    pygame.draw.rect(surf, O,  (fx+lean-3, belt_y-1, 6, 6))
    pygame.draw.rect(surf, BK, (fx+lean-2, belt_y,   4, 4))
    pygame.draw.rect(surf, O,  (bx-1, by-1, bw+2, bh+2), border_radius=4, width=2)


def _legs(surf, fx, ly, lh, s, fr, bob, lean):
    if s in ("run","skid"):
        pairs = [(-7,0,4,-2),(-6,0,4,0),(-7,-2,4,0),(-6,0,4,0)][fr%4]
    elif s == "jump": pairs = (-8,-3,5,-3)
    elif s == "fall": pairs = (-7, 2,4, 2)
    else:             pairs = (-7, 0,4, 0)
    lx1,dy1,lx2,dy2 = pairs
    for lxo, dy in ((lx1,dy1),(lx2,dy2)):
        lx = fx + lxo + lean - 3
        yl = ly + dy + bob
        pygame.draw.rect(surf, O,  (lx-1, yl-1, 8, lh+2))
        pygame.draw.rect(surf, PA, (lx,   yl,   8, lh))
        pygame.draw.rect(surf, PS, (lx,   yl,   2, lh))


def _boots(surf, fx, by, bh, s, fr, bob, lean):
    if s in ("run","skid"):
        pairs = [(-8,0,5,-3),(-7,0,4,0),(-8,-3,5,0),(-7,0,4,0)][fr%4]
    elif s == "jump": pairs = (-9,-4,6,-4)
    elif s == "fall": pairs = (-8, 3,5, 3)
    else:             pairs = (-8, 0,5, 0)
    bx1,dy1,bx2,dy2 = pairs
    for bxo, dy in ((bx1,dy1),(bx2,dy2)):
        bx = fx + bxo + lean - 4
        yl = by + dy + bob
        pygame.draw.rect(surf, BS, (bx-1, yl+bh,  12, 2))
        pygame.draw.rect(surf, O,  (bx-1, yl-1,   12, bh+1))
        pygame.draw.rect(surf, BO, (bx,   yl,     11, bh))
        pygame.draw.rect(surf, BH, (bx+2, yl+1,    4, 2))


def _speed(surf, cx, cy, ry, f, speed):
    n = 4 if speed < 7 else 6
    for i in range(n):
        yo  = int((i - n/2) * (ry * 1.2 / n))
        ln  = int(min(speed * 4, 45))
        lx  = cx - f * 10
        _aline(surf, (*JA, 80), (lx, cy+yo), (lx - f*ln, cy+yo), 2)


# ── alpha helpers ─────────────────────────────────────────────────────────────

def _aellipse(surf, col, x, y, w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, col, (0, 0, w, h))
    surf.blit(s, (x, y))


def _acircle(surf, col, cx, cy, r):
    s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
    pygame.draw.circle(s, col, (r+1, r+1), r)
    surf.blit(s, (cx-r-1, cy-r-1))


def _aline(surf, col, p1, p2, w):
    x1,y1=p1; x2,y2=p2
    mx=min(x1,x2)-w; my=min(y1,y2)-w
    sw=max(abs(x2-x1)+w*2,1); sh=max(abs(y2-y1)+w*2,1)
    s=pygame.Surface((sw,sh),pygame.SRCALPHA)
    pygame.draw.line(s,col,(x1-mx,y1-my),(x2-mx,y2-my),w)
    surf.blit(s,(mx,my))
