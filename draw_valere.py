"""
retro-pants — draw_valere.py (Sea of Stars - Valere, Lunar Monk)

  Total Height: ~40px | Width: ~32px
  Head Ratio: 55% (22px)
  Palette: High-contrast Lunar Blue, Silver, Gold
  Silhouette: Wider-than-head hair breaks the vertical stack
"""

import pygame
import math

# ── Palette ───────────────────────────────────────────────────────────────────
SKIN        = (255, 230, 200)
OUTLINE     = ( 35,  18,  60)   # dark purple
LUNAR_BLUE  = ( 50,  80, 200)
LUNAR_SILVER= (220, 235, 255)
GOLD        = (255, 210,  50)
STAFF_WOOD  = ( 95,  65,  50)
BOOT_INDIGO = ( 60,  45, 110)
BOOT_HI     = ( 95,  75, 155)
PANTS_COL   = ( 45,  55, 120)
PANTS_SH    = ( 30,  38,  88)
EW          = (255, 255, 255)
EI          = (100, 150, 255)
EP          = ( 20,  20,  60)
BL          = (230, 140, 130)


def draw_fancy_player(surf, player, cam_x):
    """Entry point called by main.py."""
    px, py  = int(player.x) - cam_x, int(player.y)
    f,  s   = player.facing, player.state
    vx, vy  = player.vx, player.vy
    fr      = player.anim_frame
    ticks   = pygame.time.get_ticks()

    fx, fy  = px + 11, py + 30
    hw, hh  = 24, 22
    bw, bh  = 20, 10

    bob  = int(math.sin(ticks * 0.003) * 2) if abs(vx) < 0.5 else 0
    lean = int(f * min(abs(vx) * 0.7, 6)) if abs(vx) > 2 else 0

    # bottom-up layout
    boot_h = 7
    leg_h  = 5
    boot_y = fy + bob - boot_h
    leg_y  = boot_y - leg_h
    body_y = leg_y - bh
    head_cx = fx + lean
    head_cy = body_y - hh // 2 - 1
    hx      = head_cx - hw // 2
    hy      = head_cy - hh // 2

    # ── ground shadow ─────────────────────────────────────────────────────────
    _aellipse(surf, (10, 5, 20, 50), fx - 15, fy - 2, 30, 4)

    # ── back layer: staff + ponytail ──────────────────────────────────────────
    _draw_bo_staff(surf, head_cx, head_cy, f, s, ticks, behind=True)
    _draw_lunar_ponytail(surf, head_cx, head_cy, f, vx, ticks)

    # ── boots ─────────────────────────────────────────────────────────────────
    _draw_boots(surf, fx, boot_y, boot_h, s, fr, bob, lean)

    # ── legs ──────────────────────────────────────────────────────────────────
    _draw_legs(surf, fx, leg_y, leg_h, s, fr, bob, lean)

    # ── body: tunic + silver vest + gold sash ────────────────────────────────
    bx = fx - 10 + lean
    pygame.draw.rect(surf, OUTLINE,      (bx+1, body_y+1, bw,   bh),   border_radius=4)
    pygame.draw.rect(surf, LUNAR_BLUE,   (bx,   body_y,   bw,   bh),   border_radius=4)
    pygame.draw.rect(surf, LUNAR_SILVER, (bx+4, body_y+1, 12, bh//2),  border_radius=2)
    pygame.draw.rect(surf, GOLD,         (bx,   body_y + bh - 4, bw, 3))
    pygame.draw.rect(surf, OUTLINE,      (bx,   body_y,   bw,   bh),   border_radius=4, width=2)

    # ── skin head ─────────────────────────────────────────────────────────────
    pygame.draw.ellipse(surf, OUTLINE, (hx+1, hy+1, hw,   hh))
    pygame.draw.ellipse(surf, SKIN,    (hx,   hy,   hw,   hh))
    _aellipse(surf, (220, 190, 165, 50), hx, hy, hw//2, hh)   # side shadow
    pygame.draw.ellipse(surf, OUTLINE, (hx,   hy,   hw,   hh), 2)

    # ── silver hair fringe (wider than head — breaks the snowman) ─────────────
    hair_w = hw + 8
    hair_h = hh // 2 + 6
    hair_x = head_cx - hair_w // 2
    hair_y = hy - 5
    pygame.draw.ellipse(surf, OUTLINE,      (hair_x+1, hair_y+1, hair_w, hair_h))
    pygame.draw.ellipse(surf, LUNAR_SILVER, (hair_x,   hair_y,   hair_w, hair_h))
    # shadow half (volume)
    _aellipse(surf, (180, 195, 230, 130), hair_x, hair_y, hair_w//2, hair_h)
    pygame.draw.ellipse(surf, OUTLINE,      (hair_x,   hair_y,   hair_w, hair_h), 2)
    # fringe arc — stamps a crisp edge where hair meets forehead
    pygame.draw.arc(surf, OUTLINE, (hx, hy, hw, hh), 0, math.pi, 2)

    # ── collar ────────────────────────────────────────────────────────────────
    cy = hy + hh - 4
    pygame.draw.ellipse(surf, OUTLINE,    (head_cx-8, cy,   16, 8))
    pygame.draw.ellipse(surf, LUNAR_BLUE, (head_cx-7, cy+1, 14, 6))

    # ── eyes ──────────────────────────────────────────────────────────────────
    _draw_eyes(surf, head_cx, head_cy, hw, hh, f, s, vx, vy, player, ticks)

    # ── front: staff gold tips ────────────────────────────────────────────────
    _draw_bo_staff(surf, head_cx, head_cy, f, s, ticks, behind=False)


def _draw_lunar_ponytail(surf, cx, cy, f, vx, ticks):
    """Three circles trailing behind the head, sway with bob."""
    sway = math.sin(ticks * 0.004) * 4
    for i in range(3):
        px_ = int(cx - f * (14 + i*4) - vx * 0.6)
        py_ = int(cy - 4 + i*4 + sway)
        r   = 7 - i
        _acircle(surf, OUTLINE,       px_+1, py_+1, r)
        _acircle(surf, LUNAR_SILVER,  px_,   py_,   r)


def _draw_bo_staff(surf, cx, cy, f, s, ticks, behind: bool):
    """Diagonal staff — shaft behind body, gold tips in front."""
    angle = math.radians(45)
    if s == "jump":
        angle += math.sin(ticks * 0.01) * 0.5

    length = 38
    dx = math.cos(angle) * (length / 2)
    dy = math.sin(angle) * (length / 2)
    px_ = cx + f * 4
    py_ = cy + hh_approx(cy) // 2 - 4   # near hip

    x1, y1 = int(px_ - f*dx), int(py_ - dy)
    x2, y2 = int(px_ + f*dx), int(py_ + dy)

    if behind:
        _aline(surf, (*OUTLINE, 255),    (x1, y1), (x2, y2), 5)
        _aline(surf, (*STAFF_WOOD, 255), (x1, y1), (x2, y2), 3)
    else:
        for tx, ty in [(x1, y1), (x2, y2)]:
            _acircle(surf, (150, 200, 255, 150), tx, ty, 5)
            _acircle(surf, GOLD,                 tx, ty, 3)
            pygame.draw.circle(surf, OUTLINE, (tx, ty), 3, 1)


def hh_approx(cy):
    """Staff pivot helper — returns a fixed estimate of hh."""
    return 22


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


def _draw_legs(surf, fx, ly, lh, s, fr, bob, lean):
    if s in ("run", "skid"):
        pairs = [(-7,0,4,-2),(-6,0,4,0),(-7,-2,4,0),(-6,0,4,0)][fr%4]
    elif s == "jump": pairs = (-8,-3,5,-3)
    elif s == "fall": pairs = (-7, 2,4, 2)
    else:             pairs = (-7, 0,4, 0)
    lx1,dy1,lx2,dy2 = pairs
    for lxo, dy in ((lx1,dy1),(lx2,dy2)):
        lx = fx + lxo + lean - 3
        yl = ly + dy + bob
        pygame.draw.rect(surf, OUTLINE,   (lx-1, yl-1, 8, lh+2))
        pygame.draw.rect(surf, PANTS_COL, (lx,   yl,   8, lh))
        pygame.draw.rect(surf, PANTS_SH,  (lx,   yl,   2, lh))


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
        pygame.draw.rect(surf, OUTLINE,     (bx-1, yl-1,   12, bh+2))
        pygame.draw.rect(surf, BOOT_INDIGO, (bx,   yl,     11, bh))
        pygame.draw.rect(surf, BOOT_HI,     (bx+2, yl+1,    4, 2))


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
