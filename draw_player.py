"""
retro-pants — draw_player.py  (v5 — RPG Adventurer, fixed)

Reference: Sea of Stars chibi — large skin face, dark hair ONLY on crown,
blue jacket, cream shirt collar, brown pants, dark boots, teal eyes.

Integration (unchanged):
  from draw_player import draw_fancy_player
"""

import pygame
import math

# ── Palette ───────────────────────────────────────────────────────────────────
OUTLINE     = (15,   8,   3)    # near-black brown outline
SKIN        = (238, 195, 154)   # warm peach — face dominates
SKIN_SH     = (205, 160, 115)   # face shadow (left side)
HAIR        = ( 48,  28,   8)   # dark brown
HAIR_MID    = ( 75,  48,  18)   # hair midtone
HAIR_HI     = (115,  78,  35)   # highlight streak
EYE_WHITE   = (255, 255, 255)
EYE_IRIS    = ( 30, 148, 136)   # teal
EYE_PUPIL   = (  8,  45,  42)
EYE_GLINT   = (255, 255, 255)
BLUSH       = (220, 115,  95)
SHIRT       = (235, 228, 210)   # cream shirt (collar + cuffs)
JACKET      = ( 60,  85, 145)   # blue jacket — breaks the brown monotony
JACKET_SH   = ( 40,  58, 105)   # jacket shadow
JACKET_HI   = ( 90, 125, 190)   # jacket highlight
BELT        = ( 50,  30,  10)
BUCKLE      = (195, 162,  55)   # brass
PANTS       = ( 72,  50,  28)   # dark brown pants
PANTS_SH    = ( 50,  34,  16)
BOOT        = ( 38,  22,   8)
BOOT_HI     = ( 65,  42,  20)
BOOT_SOLE   = ( 25,  14,   4)


def draw_fancy_player(surf, player, cam_x):
    px    = int(player.x) - cam_x
    py    = int(player.y)
    f     = player.facing
    s     = player.state
    vx    = player.vx
    vy    = player.vy
    fr    = player.anim_frame
    ticks = pygame.time.get_ticks()

    # Anchor: feet center
    fx = px + 11
    fy = py + 30

    # ── Squash / stretch ──────────────────────────────────────────────────────
    sq = getattr(player, 'land_squash', 0)
    if sq > 0:
        t = sq / 7.0
        head_w, head_h, body_h = int(22 + 6*t), int(20 - 3*t), int(13 - 3*t)
    elif s == "jump" and vy < -3:
        head_w, head_h, body_h = 20, 23, 10
    elif s == "fall" and vy > 4:
        head_w, head_h, body_h = 24, 18, 14
    else:
        head_w, head_h, body_h = 22, 20, 13

    bob  = int(math.sin(ticks * 0.003) * 2) if abs(vx) < 0.5 else 0
    lean = 0
    if s in ("run", "skid") and abs(vx) > 2:
        lean = int(f * min(abs(vx) * 0.6, 5))

    # ── Positions (bottom-up) ─────────────────────────────────────────────────
    boot_y  = fy + bob - 8
    body_y  = boot_y - body_h - 6   # 6px gap = legs
    body_x  = fx - 9 + lean
    head_cx = fx + lean
    head_cy = body_y - head_h // 2

    hx = head_cx - head_w // 2
    hy = head_cy - head_h // 2

    # ── Shadow ────────────────────────────────────────────────────────────────
    _aellipse(surf, (5, 3, 1, 50), fx - 15, fy - 2, 30, 5)

    # ── Boots ─────────────────────────────────────────────────────────────────
    _draw_boots(surf, fx, boot_y, f, s, fr, bob, lean)

    # ── Legs (pants stubs) ────────────────────────────────────────────────────
    _draw_legs(surf, fx, boot_y, body_y + body_h, s, fr, bob, lean)

    # ── Body (blue jacket) ────────────────────────────────────────────────────
    _draw_body(surf, body_x, body_y, body_h, lean, head_cx)

    # ── Head: skin ────────────────────────────────────────────────────────────
    # Drop shadow
    pygame.draw.ellipse(surf, OUTLINE, (hx + 2, hy + 2, head_w, head_h))
    # Skin fill
    pygame.draw.ellipse(surf, SKIN,    (hx,     hy,     head_w, head_h))
    # Left-side face shadow
    _aellipse(surf, (*SKIN_SH, 60), hx, hy, head_w // 2, head_h)
    # Outline
    pygame.draw.ellipse(surf, OUTLINE, (hx, hy, head_w, head_h), 2)

    # ── Hair: crown only ──────────────────────────────────────────────────────
    _draw_hair(surf, head_cx, hx, hy, head_w, f, s, vx, ticks)

    # ── Shirt collar (cream) ──────────────────────────────────────────────────
    collar_y = hy + head_h - 5
    pygame.draw.ellipse(surf, OUTLINE, (head_cx - 7, collar_y,     14, 8))
    pygame.draw.ellipse(surf, SHIRT,   (head_cx - 6, collar_y + 1, 12, 6))

    # ── Eyes ──────────────────────────────────────────────────────────────────
    _draw_eyes(surf, head_cx, head_cy, head_w, head_h,
               f, s, vx, vy, player, ticks)


def _draw_boots(surf, fx, boot_y, f, s, fr, bob, lean):
    if s in ("run", "skid"):
        off = [
            [(-7, 0), (5, -3)],
            [(-6, 0), (4,  0)],
            [(-7,-3), (5,  0)],
            [(-6, 0), (4,  0)],
        ][fr % 4]
    elif s == "jump":
        off = [(-8, -4), (6, -4)]
    elif s == "fall":
        off = [(-7,  3), (5,  3)]
    else:
        off = [(-7,  0), (5,  0)]

    for bx_off, by_off in off:
        bx = fx + bx_off + lean - 4
        by = boot_y + by_off + bob
        pygame.draw.rect(surf, BOOT_SOLE, (bx - 1, by + 6, 12, 3), border_radius=2)
        pygame.draw.rect(surf, OUTLINE,   (bx + 1, by + 1, 10, 8), border_radius=3)
        pygame.draw.rect(surf, BOOT,      (bx,     by,     10, 8), border_radius=3)
        pygame.draw.rect(surf, BOOT_HI,   (bx + 2, by + 1,  4, 2), border_radius=1)
        pygame.draw.rect(surf, OUTLINE,   (bx,     by,     10, 8), border_radius=3, width=1)


def _draw_legs(surf, fx, boot_y, body_bottom, s, fr, bob, lean):
    """Short pants stubs between body and boots."""
    leg_h = max(boot_y - body_bottom, 4)

    if s in ("run", "skid"):
        off = [
            [(-6, 0), (4, -2)],
            [(-5, 0), (3,  0)],
            [(-6,-2), (4,  0)],
            [(-5, 0), (3,  0)],
        ][fr % 4]
    else:
        off = [(-6, 0), (4, 0)]

    for lx_off, ly_off in off:
        lx = fx + lx_off + lean - 3
        ly = body_bottom + ly_off + bob
        pygame.draw.rect(surf, OUTLINE,  (lx + 1, ly + 1, 8, leg_h), border_radius=2)
        pygame.draw.rect(surf, PANTS,    (lx,     ly,     8, leg_h), border_radius=2)
        pygame.draw.rect(surf, PANTS_SH, (lx,     ly + 2, 3, leg_h - 3), border_radius=1)
        pygame.draw.rect(surf, OUTLINE,  (lx,     ly,     8, leg_h), border_radius=2, width=1)


def _draw_body(surf, body_x, body_y, body_h, lean, cx):
    """Blue jacket with cream shirt visible at sides, leather belt."""
    bw = 18
    # Shadow
    pygame.draw.rect(surf, OUTLINE,   (body_x + 2, body_y + 2, bw,     body_h),     border_radius=4)
    # Jacket fill
    pygame.draw.rect(surf, JACKET,    (body_x,     body_y,     bw,     body_h),     border_radius=4)
    # Left shadow
    pygame.draw.rect(surf, JACKET_SH, (body_x,     body_y + 2, bw // 3, body_h - 4), border_radius=2)
    # Right highlight
    pygame.draw.rect(surf, JACKET_HI, (body_x + bw // 2, body_y + 1, 5, body_h // 3), border_radius=2)
    # Cream shirt visible at left and right edges (underlayer peek)
    pygame.draw.rect(surf, SHIRT,     (body_x - 1, body_y + 2, 3, body_h - 4), border_radius=1)
    pygame.draw.rect(surf, SHIRT,     (body_x + bw - 2, body_y + 2, 3, body_h - 4), border_radius=1)
    # Outline
    pygame.draw.rect(surf, OUTLINE,   (body_x,     body_y,     bw,     body_h),     border_radius=4, width=2)
    # Belt
    belt_y = body_y + body_h - 4
    pygame.draw.rect(surf, BELT,      (body_x + 1, belt_y, bw - 2, 4))
    # Buckle
    bk_x = cx - 3
    pygame.draw.rect(surf, OUTLINE,   (bk_x,     belt_y - 1, 6, 6))
    pygame.draw.rect(surf, BUCKLE,    (bk_x + 1, belt_y,     4, 4))


def _draw_hair(surf, cx, hx, hy, hw, f, s, vx, ticks):
    """
    Hair sits ONLY on the crown — top ~7px of the head.
    The skin face must dominate below it.
    """
    # Crown cap: a fat rounded rect covering just the top of the head
    cap_x = hx - 2
    cap_y = hy - 3
    cap_w = hw + 4
    cap_h = 11   # SMALL — only the crown, not half the head

    # Shadow
    pygame.draw.rect(surf, OUTLINE, (cap_x + 1, cap_y + 1, cap_w, cap_h), border_radius=6)
    # Base fill
    pygame.draw.rect(surf, HAIR,    (cap_x,     cap_y,     cap_w, cap_h), border_radius=6)
    # Midtone band
    pygame.draw.rect(surf, HAIR_MID,(cap_x + 3, cap_y + 2, cap_w - 6, 4), border_radius=2)
    # Highlight streak
    pygame.draw.rect(surf, HAIR_HI, (cx + 1,   cap_y + 1, 4, 3), border_radius=1)
    # Outline arc on top only
    pygame.draw.rect(surf, OUTLINE, (cap_x,     cap_y,     cap_w, cap_h), border_radius=6, width=2)

    # Thin ear-side pieces — just 2px wide, only 4px tall, barely visible
    # Left
    pygame.draw.rect(surf, HAIR,   (hx - 1, hy + 6, 3, 5), border_radius=1)
    pygame.draw.rect(surf, OUTLINE,(hx - 1, hy + 6, 3, 5), border_radius=1, width=1)
    # Right
    pygame.draw.rect(surf, HAIR,   (hx + hw - 2, hy + 6, 3, 5), border_radius=1)
    pygame.draw.rect(surf, OUTLINE,(hx + hw - 2, hy + 6, 3, 5), border_radius=1, width=1)

    # One small front tuft
    speed = abs(vx)
    if s in ("run", "skid") and speed > 2:
        tx = cx + f * int(min(speed * 1.2, 7))
    else:
        tx = cx + int(math.sin(ticks * 0.0015) * 1.5)

    tuft = [
        (tx - 3, cap_y + cap_h - 1),
        (tx,     cap_y + cap_h - 8),
        (tx + 3, cap_y + cap_h - 1),
    ]
    pygame.draw.polygon(surf, OUTLINE,  [(x+1, y+1) for x, y in tuft])
    pygame.draw.polygon(surf, HAIR_MID, tuft)
    pygame.draw.polygon(surf, OUTLINE,  tuft, 1)


def _draw_eyes(surf, cx, cy, hw, hh, f, s, vx, vy, player, ticks):
    speed = abs(vx)
    le_x = cx - 5
    re_x = cx + 5
    e_y  = cy

    ew, eh = 7, 9

    # Happy squint on landing
    sq = getattr(player, 'land_squash', 0)
    if sq > 3:
        for ex in (le_x, re_x):
            pygame.draw.ellipse(surf, EYE_WHITE, (ex - 4, e_y - 2, 9, 6))
            pygame.draw.arc(surf, OUTLINE, (ex - 4, e_y - 2, 9, 6), 0, math.pi, 2)
        pygame.draw.arc(surf, OUTLINE, (cx - 4, e_y + 3, 8, 4), math.pi, 2*math.pi, 2)
        _blush(surf, le_x, re_x, e_y, 6, 170)
        return

    if s == "jump" and vy < -3:
        ew, eh = 7, 11
        pdx, pdy = 0, -2
    elif s == "fall" and vy > 4:
        ew, eh = 8, 8
        pdx, pdy = 0, 2
    elif speed > 5:
        ew, eh = 9, 6
        pdx, pdy = f * 3, 0
    elif speed > 2:
        pdx, pdy = f * 2, 0
    else:
        pdx = int(math.sin(ticks * 0.0015) * 1.5)
        pdy = 0
        if (ticks // 16) % 220 < 5:
            for ex in (le_x, re_x):
                pygame.draw.ellipse(surf, EYE_WHITE, (ex - ew//2, e_y - 2, ew, 3))
            return

    for ex in (le_x, re_x):
        pygame.draw.ellipse(surf, OUTLINE,
                            (ex - ew//2 - 1, e_y - eh//2 - 1, ew + 2, eh + 2))
        pygame.draw.ellipse(surf, EYE_WHITE,
                            (ex - ew//2,     e_y - eh//2,     ew,     eh))
        ix = max(ex - ew//2 + 2, min(ex + ew//2 - 2, ex + pdx))
        iy = max(e_y - eh//2 + 2, min(e_y + eh//2 - 2, e_y + pdy))
        pygame.draw.circle(surf, EYE_IRIS,  (ix, iy), 3)
        pygame.draw.circle(surf, EYE_PUPIL, (ix, iy), 2)
        pygame.draw.circle(surf, EYE_GLINT, (ix + 2, iy - 2), 2)
        pygame.draw.circle(surf, EYE_GLINT, (ix + 3, iy + 1), 1)
        # Top lash
        pygame.draw.arc(surf, OUTLINE,
                        (ex - ew//2 - 1, e_y - eh//2 - 1, ew + 2, eh + 2),
                        math.pi * 0.1, math.pi * 0.9, 2)

    # Eyebrows — dark brown
    brow_y = e_y - eh // 2 - 4
    if speed > 5 and s == "run":
        pygame.draw.line(surf, HAIR, (le_x - 4, brow_y - 2), (le_x + 3, brow_y), 2)
        pygame.draw.line(surf, HAIR, (re_x - 3, brow_y),     (re_x + 4, brow_y - 2), 2)
    elif s == "jump" and vy < -3:
        for ex in (le_x, re_x):
            pygame.draw.arc(surf, HAIR, (ex - 5, brow_y - 4, 10, 6), math.pi, 2*math.pi, 2)
    elif s == "fall" and vy > 5:
        for ex in (le_x, re_x):
            pygame.draw.arc(surf, HAIR, (ex - 5, brow_y - 1, 10, 5), 0, math.pi, 2)
    else:
        for ex in (le_x, re_x):
            pygame.draw.line(surf, HAIR, (ex - 4, brow_y), (ex + 4, brow_y - 1), 2)

    _blush(surf, le_x, re_x, e_y, 4, 50)

    if abs(vx) < 1 and s not in ("jump", "fall", "roll"):
        pygame.draw.arc(surf, OUTLINE,
                        (cx - 4, e_y + eh // 2, 8, 4), math.pi, 2*math.pi, 1)


def _blush(surf, le_x, re_x, e_y, r, a):
    for ex in (le_x, re_x):
        off = -8 if ex < (le_x + re_x) // 2 else 8
        _acircle(surf, (*BLUSH, a), ex + off, e_y + 5, r)


# ── Alpha helpers ─────────────────────────────────────────────────────────────

def _aellipse(surf, col, x, y, w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, col, (0, 0, w, h))
    surf.blit(s, (x, y))


def _acircle(surf, col, cx, cy, r):
    s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
    pygame.draw.circle(s, col, (r+1, r+1), r)
    surf.blit(s, (cx-r-1, cy-r-1))
