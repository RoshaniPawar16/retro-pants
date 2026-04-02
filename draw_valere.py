"""
retro-pants — draw_valere.py
Strict 40px height / 32px width / 55% head ratio
"""

import pygame
import math

# ── Palette ───────────────────────────────────────────────────────────────────
SKIN         = (255, 230, 200)
OUTLINE      = ( 35,  18,  60)
LUNAR_BLUE   = ( 45,  75, 180)
LUNAR_SILVER = (230, 240, 255)
SILVER_SH    = (170, 185, 220)
GOLD_TRIM    = (255, 210,  50)
STAFF_BROWN  = ( 90,  60,  50)
BOOT_DARK    = ( 55,  40, 100)
BOOT_HI      = ( 90,  72, 148)
PANTS_COL    = ( 40,  52, 120)
PANTS_SH     = ( 28,  36,  88)
EW           = (255, 255, 255)
EI           = (100, 150, 255)
EP           = ( 20,  20,  60)
BL           = (230, 140, 130)


def draw_fancy_player(surf, player, cam_x):
    px, py  = int(player.x) - cam_x, int(player.y)
    f, s    = player.facing, player.state
    vx, vy  = player.vx, player.vy
    fr      = player.anim_frame
    ticks   = pygame.time.get_ticks()

    fx, fy  = px + 11, py + 30
    hw, hh  = 24, 22   # head 22px = 55% of 40px
    bw, bh  = 20, 10

    bob = int(math.sin(ticks * 0.003) * 2) if abs(vx) < 0.5 else 0

    # strict layout (your spec — no lean, boots sit directly below body)
    body_y  = fy + bob - bh - 6
    head_cy = fy + bob - bh - hh // 2 - 4
    hx      = fx - hw // 2
    hy      = head_cy - hh // 2

    # ── shadow ────────────────────────────────────────────────────────────────
    _aellipse(surf, (10, 5, 20, 50), fx - 15, fy - 2, 30, 4)

    # ── back: ponytail + staff shaft ──────────────────────────────────────────
    _draw_ponytail(surf, fx, head_cy, f, vx, ticks)
    _draw_staff(surf, fx, head_cy, f, s, ticks, behind=True)

    # ── boots ─────────────────────────────────────────────────────────────────
    _draw_boots(surf, fx, fy + bob - 6, 7, s, fr, bob, 0)

    # ── body ──────────────────────────────────────────────────────────────────
    bx = fx - 10
    pygame.draw.rect(surf, OUTLINE,    (bx+1, body_y+1, bw,   bh),   border_radius=4)
    pygame.draw.rect(surf, LUNAR_BLUE, (bx,   body_y,   bw,   bh),   border_radius=4)
    pygame.draw.rect(surf, GOLD_TRIM,  (bx,   body_y + bh - 3, bw, 3))
    pygame.draw.rect(surf, OUTLINE,    (bx,   body_y,   bw,   bh),   border_radius=4, width=2)

    # ── skin head ─────────────────────────────────────────────────────────────
    pygame.draw.ellipse(surf, OUTLINE, (hx+1, hy+1, hw,   hh))
    pygame.draw.ellipse(surf, SKIN,    (hx,   hy,   hw,   hh))
    _aellipse(surf, (220, 190, 165, 50), hx, hy, hw // 2, hh)
    pygame.draw.ellipse(surf, OUTLINE, (hx,   hy,   hw,   hh), 2)

    # ── silver hair fringe (wider than head — breaks the hat look) ────────────
    hfx, hfy = hx - 3, hy - 4
    hfw, hfh = hw + 6, hh // 2 + 4
    pygame.draw.ellipse(surf, OUTLINE,      (hfx+1, hfy+1, hfw,    hfh))
    pygame.draw.ellipse(surf, LUNAR_SILVER, (hfx,   hfy,   hfw,    hfh))
    _aellipse(surf, (*SILVER_SH, 120),       hfx,   hfy,   hfw//2, hfh)
    pygame.draw.ellipse(surf, OUTLINE,      (hfx,   hfy,   hfw,    hfh), 2)
    # fringe arc — crisp hairline edge on the forehead
    pygame.draw.arc(surf, OUTLINE, (hx, hy, hw, hh), 0, math.pi, 2)

    # ── collar ────────────────────────────────────────────────────────────────
    col_y = hy + hh - 4
    pygame.draw.ellipse(surf, OUTLINE,    (fx-8, col_y,   16, 8))
    pygame.draw.ellipse(surf, LUNAR_BLUE, (fx-7, col_y+1, 14, 6))

    # ── eyes + front staff tips ───────────────────────────────────────────────
    _draw_eyes(surf, fx, head_cy, hw, hh, f, s, vx, vy, player, ticks)
    _draw_staff(surf, fx, head_cy, f, s, ticks, behind=False)


def _draw_ponytail(surf, cx, cy, f, vx, ticks):
    sway = math.sin(ticks * 0.004) * 3
    for i in range(3):
        px_ = int(cx - f * (14 + i*4) - vx * 0.5)
        py_ = int(cy - 4 + i*3 + sway)
        r   = 7 - i
        pygame.draw.circle(surf, OUTLINE,      (px_+1, py_+1), r)
        pygame.draw.circle(surf, LUNAR_SILVER, (px_,   py_),   r)


def _draw_staff(surf, cx, cy, f, s, ticks, behind: bool):
    angle = math.radians(45)
    if s == "jump":
        angle += math.sin(ticks * 0.01) * 0.5

    dx = math.cos(angle) * 18
    dy = math.sin(angle) * 18
    x1, y1 = int(cx - f*dx), int(cy + 4 - dy)
    x2, y2 = int(cx + f*dx), int(cy + 4 + dy)

    if behind:
        pygame.draw.line(surf, OUTLINE,     (x1, y1), (x2, y2), 5)
        pygame.draw.line(surf, STAFF_BROWN, (x1, y1), (x2, y2), 3)
    else:
        for tx, ty in [(x1, y1), (x2, y2)]:
            pygame.draw.circle(surf, GOLD_TRIM, (tx, ty), 3)
            pygame.draw.circle(surf, OUTLINE,   (tx, ty), 3, 1)


def _draw_eyes(surf, cx, cy, hw, hh, f, s, vx, vy, player, ticks):
    speed = abs(vx)
    ey   = cy + hh // 8
    le_x = cx - hw // 5
    re_x = cx + hw // 5
    ew, eh = 6, 8

    sq = getattr(player, 'land_squash', 0)
    if sq > 3:
        for ex in (le_x, re_x):
            pygame.draw.ellipse(surf, EW, (ex-4, ey-2, 8, 6))
            pygame.draw.arc(surf, OUTLINE, (ex-4, ey-2, 8, 6), 0, math.pi, 2)
        pygame.draw.arc(surf, OUTLINE, (cx-4, ey+3, 8, 4), math.pi, 2*math.pi, 1)
        _blush(surf, le_x, re_x, ey)
        return

    if speed < 0.5 and (ticks // 16) % 220 < 5:
        for ex in (le_x, re_x):
            pygame.draw.ellipse(surf, EW, (ex-ew//2, ey-1, ew, 3))
        return

    if s == "jump" and vy < -3:
        ew, eh = 6, 10; pdx, pdy = 0, -2
    elif s == "fall" and vy > 4:
        ew, eh = 7,  7; pdx, pdy = 0,  2
    elif speed > 5:
        ew, eh = 8,  5; pdx, pdy = f*3, 0
    elif speed > 2:
        pdx, pdy = f*1, 0
    else:
        pdx = int(math.sin(ticks * 0.0015) * 1.2)
        pdy = 0

    for ex in (le_x, re_x):
        pygame.draw.ellipse(surf, OUTLINE, (ex-ew//2-1, ey-eh//2-1, ew+2, eh+2))
        pygame.draw.ellipse(surf, EW,      (ex-ew//2,   ey-eh//2,   ew,   eh))
        ix = max(ex-ew//2+2, min(ex+ew//2-2, ex+pdx))
        iy = max(ey-eh//2+2, min(ey+eh//2-2, ey+pdy))
        pygame.draw.circle(surf, EI, (ix, iy), 3)
        pygame.draw.circle(surf, EP, (ix, iy), 2)
        surf.set_at((ix+1, iy-1), EW)
        surf.set_at((ix+2, iy-1), EW)
        pygame.draw.arc(surf, OUTLINE,
                        (ex-ew//2-1, ey-eh//2-1, ew+2, eh+2),
                        math.pi*0.1, math.pi*0.9, 2)

    brow_y = ey - eh//2 - 4
    if speed > 5 and s == "run":
        pygame.draw.line(surf, LUNAR_SILVER, (le_x-4, brow_y-2), (le_x+3, brow_y), 2)
        pygame.draw.line(surf, LUNAR_SILVER, (re_x-3, brow_y),   (re_x+4, brow_y-2), 2)
    else:
        pygame.draw.line(surf, LUNAR_SILVER, (le_x-3, brow_y),   (le_x+3, brow_y-1), 2)
        pygame.draw.line(surf, LUNAR_SILVER, (re_x-3, brow_y-1), (re_x+3, brow_y),   2)

    _blush(surf, le_x, re_x, ey)

    if abs(vx) < 1 and s not in ("jump", "fall", "roll"):
        pygame.draw.arc(surf, OUTLINE, (cx-4, ey+eh//2+1, 8, 4), math.pi, 2*math.pi, 1)


def _blush(surf, le_x, re_x, ey):
    _acircle(surf, (*BL, 90), le_x-5, ey+4, 3)
    _acircle(surf, (*BL, 90), re_x+5, ey+4, 3)



def _draw_boots(surf, fx, by, bh, s, fr, bob, lean):
    if s in ("run", "skid"):
        pairs = [(-8,0,5,-3),(-7,0,4,0),(-8,-3,5,0),(-7,0,4,0)][fr%4]
    elif s == "jump": pairs = (-9,-4,6,-4)
    elif s == "fall": pairs = (-8, 3,5, 3)
    else:             pairs = (-8, 0,5, 0)
    bx1,dy1,bx2,dy2 = pairs
    for bxo, dy in ((bx1,dy1),(bx2,dy2)):
        bx = fx + bxo + lean - 4
        yl = by + dy + bob
        pygame.draw.rect(surf, OUTLINE,   (bx-1, yl-1,   12, bh+2))
        pygame.draw.rect(surf, BOOT_DARK, (bx,   yl,     11, bh))
        pygame.draw.rect(surf, BOOT_HI,   (bx+2, yl+1,    4, 2))


# ── alpha helpers ─────────────────────────────────────────────────────────────

def _aellipse(surf, col, x, y, w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, col, (0, 0, w, h))
    surf.blit(s, (x, y))


def _acircle(surf, col, cx, cy, r):
    r = int(r)
    s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
    pygame.draw.circle(s, col, (r+1, r+1), r)
    surf.blit(s, (int(cx)-r-1, int(cy)-r-1))


def _aline(surf, col, p1, p2, w):
    x1,y1 = int(p1[0]),int(p1[1])
    x2,y2 = int(p2[0]),int(p2[1])
    w = int(w)
    mx=min(x1,x2)-w; my=min(y1,y2)-w
    sw=max(abs(x2-x1)+w*2,1); sh=max(abs(y2-y1)+w*2,1)
    s=pygame.Surface((sw,sh),pygame.SRCALPHA)
    pygame.draw.line(s,col,(x1-mx,y1-my),(x2-mx,y2-my),w)
    surf.blit(s,(mx,my))
