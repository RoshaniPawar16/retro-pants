"""
retro-pants — draw_player.py  (v4 — RPG Adventurer, Sea of Stars chibi)

Reference: dark structured hair, warm peach skin, tan tunic over cream shirt,
brown pants, dark leather boots, large teal eyes. ~44px tall total.

Integration (unchanged):
  from draw_player import draw_fancy_player

  Player.__init__:
      self.pos_history = []
      self.land_squash = 0

  Player.update() end:
      self.pos_history.insert(0, (int(self.x), int(self.y)))
      if len(self.pos_history) > 8: self.pos_history.pop()
      if self.land_squash > 0: self.land_squash -= 1

  Player._resolve_y() after on_ground=True:
      if self.vy > 4: self.land_squash = 7

  Player.draw():
      def draw(self, surf, cam_x):
          draw_fancy_player(surf, self, cam_x)
"""

import pygame
import math

# ── Palette ───────────────────────────────────────────────────────────────────
OUTLINE     = (20,  12,   5)    # very dark brown — never pure black
SKIN        = (240, 200, 165)   # warm peach
SKIN_SHADE  = (210, 168, 130)   # cheek shadow
HAIR        = ( 55,  32,  12)   # dark brown hair
HAIR_MID    = ( 80,  50,  20)   # hair midtone
HAIR_HI     = (110,  72,  30)   # hair highlight streak
EYE_WHITE   = (255, 255, 255)
EYE_IRIS    = ( 35, 155, 140)   # teal iris
EYE_PUPIL   = ( 10,  50,  45)   # deep teal pupil
EYE_GLINT   = (255, 255, 255)
BLUSH       = (230, 130, 110)
TUNIC       = (180, 145,  90)   # tan/brown tunic
TUNIC_DARK  = (140, 105,  60)   # tunic shadow
TUNIC_HI    = (215, 185, 130)   # tunic highlight
SHIRT       = (235, 225, 200)   # cream undershirt (visible at collar/cuffs)
BELT        = ( 65,  40,  18)   # dark leather belt
BELT_BUCKLE = (200, 170,  60)   # brass buckle
PANTS       = ( 95,  68,  38)   # medium brown pants
PANTS_DARK  = ( 68,  48,  25)   # pants shadow
BOOT        = ( 50,  30,  12)   # dark leather boots
BOOT_SOLE   = ( 35,  20,   8)   # sole edge
BOOT_HI     = ( 80,  52,  25)   # boot highlight


def draw_fancy_player(surf, player, cam_x):
    px    = int(player.x) - cam_x
    py    = int(player.y)
    f     = player.facing
    s     = player.state
    vx    = player.vx
    vy    = player.vy
    fr    = player.anim_frame
    ticks = pygame.time.get_ticks()

    # Character anchor — feet center
    fx = px + 11
    fy = py + 30

    # ── Squash / stretch ──────────────────────────────────────────────────────
    sq = getattr(player, 'land_squash', 0)
    if sq > 0:
        t = sq / 7.0
        head_w, head_h, body_h = int(22 + 6*t), int(20 - 3*t), int(14 - 3*t)
    elif s == "jump" and vy < -3:
        head_w, head_h, body_h = 20, 23, 11
    elif s == "fall" and vy > 4:
        head_w, head_h, body_h = 24, 18, 15
    else:
        head_w, head_h, body_h = 22, 20, 14

    # Idle bob
    bob  = int(math.sin(ticks * 0.003) * 2) if abs(vx) < 0.5 else 0
    # Lean — subtle forward tilt when running
    lean = 0
    if s in ("run", "skid") and abs(vx) > 2:
        lean = int(f * min(abs(vx) * 0.6, 5))

    # ── Layout (bottom up) ────────────────────────────────────────────────────
    boot_y  = fy + bob - 8
    body_y  = boot_y - body_h
    body_x  = fx - 9 + lean
    head_cx = fx + lean
    head_cy = body_y - head_h // 2

    # ── Shadow ────────────────────────────────────────────────────────────────
    sw = 30 if sq == 0 else 38
    _aellipse(surf, (5, 3, 1, 55), fx - sw//2, fy - 2, sw, 5)

    # ── Boots ─────────────────────────────────────────────────────────────────
    _draw_boots(surf, fx, boot_y, f, s, fr, bob, lean)

    # ── Legs / pants ──────────────────────────────────────────────────────────
    _draw_legs(surf, fx, boot_y, body_y, f, s, fr, bob, lean)

    # ── Body: tunic ───────────────────────────────────────────────────────────
    _draw_body(surf, body_x, body_y, body_h, lean, head_cx)

    # ── Head ──────────────────────────────────────────────────────────────────
    hx = head_cx - head_w // 2
    hy = head_cy - head_h // 2

    # Drop shadow
    pygame.draw.ellipse(surf, OUTLINE, (hx+2, hy+2, head_w, head_h))
    # Skin
    pygame.draw.ellipse(surf, SKIN,    (hx,   hy,   head_w, head_h))
    # Side shading (left side for depth)
    shade_surf = pygame.Surface((head_w // 2, head_h), pygame.SRCALPHA)
    full_surf  = pygame.Surface((head_w, head_h), pygame.SRCALPHA)
    pygame.draw.ellipse(full_surf, (*SKIN_SHADE, 70), (0, 0, head_w, head_h))
    shade_surf.blit(full_surf, (0, 0))
    surf.blit(shade_surf, (hx, hy))
    # Outline
    pygame.draw.ellipse(surf, OUTLINE, (hx, hy, head_w, head_h), 2)

    # ── Hair ──────────────────────────────────────────────────────────────────
    _draw_hair(surf, head_cx, hx, hy, head_w, head_h, f, s, vx, ticks)

    # ── Collar: cream shirt visible above tunic ────────────────────────────────
    collar_y = head_cy + head_h // 2 - 2
    pygame.draw.ellipse(surf, OUTLINE, (head_cx - 7, collar_y,     14, 7))
    pygame.draw.ellipse(surf, SHIRT,   (head_cx - 6, collar_y + 1, 12, 5))

    # ── Eyes ──────────────────────────────────────────────────────────────────
    _draw_eyes(surf, head_cx, head_cy, head_w, head_h,
               f, s, vx, vy, player, ticks)


def _draw_boots(surf, fx, boot_y, f, s, fr, bob, lean):
    """Dark leather boots — chunky, squared toe."""
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
        # Sole edge
        pygame.draw.rect(surf, BOOT_SOLE, (bx - 1, by + 6, 12, 3), border_radius=2)
        # Boot shadow
        pygame.draw.rect(surf, OUTLINE,   (bx + 1, by + 1, 10, 8), border_radius=3)
        # Boot fill
        pygame.draw.rect(surf, BOOT,      (bx,     by,     10, 8), border_radius=3)
        # Boot highlight
        pygame.draw.rect(surf, BOOT_HI,   (bx + 2, by + 1,  4, 2), border_radius=1)
        pygame.draw.rect(surf, OUTLINE,   (bx,     by,     10, 8), border_radius=3, width=1)


def _draw_legs(surf, fx, boot_y, body_y, f, s, fr, bob, lean):
    """Short chunky pants between body and boots."""
    leg_h = max(body_y - boot_y + 2, 4)
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
        ly = boot_y + ly_off + bob - leg_h
        # Shadow
        pygame.draw.rect(surf, OUTLINE,    (lx + 1, ly + 1, 8, leg_h + 2), border_radius=2)
        # Pants fill
        pygame.draw.rect(surf, PANTS,      (lx,     ly,     8, leg_h + 2), border_radius=2)
        # Inner shadow on pants
        pygame.draw.rect(surf, PANTS_DARK, (lx,     ly + 2, 3, leg_h - 2), border_radius=1)
        pygame.draw.rect(surf, OUTLINE,    (lx,     ly,     8, leg_h + 2), border_radius=2, width=1)


def _draw_body(surf, body_x, body_y, body_h, lean, cx):
    """Tan tunic with cream shirt at edges, dark belt at waist."""
    bw = 18

    # Shadow
    pygame.draw.rect(surf, OUTLINE,    (body_x + 2, body_y + 2, bw,     body_h),     border_radius=4)
    # Main tunic
    pygame.draw.rect(surf, TUNIC,      (body_x,     body_y,     bw,     body_h),     border_radius=4)
    # Left-side shadow strip on tunic
    pygame.draw.rect(surf, TUNIC_DARK, (body_x,     body_y + 2, bw // 3, body_h - 4), border_radius=2)
    # Highlight on right shoulder area
    pygame.draw.rect(surf, TUNIC_HI,   (body_x + bw // 2, body_y + 1, bw // 3, body_h // 3), border_radius=2)
    # Outline
    pygame.draw.rect(surf, OUTLINE,    (body_x,     body_y,     bw,     body_h),     border_radius=4, width=2)

    # Belt — 3px stripe across middle of body
    belt_y = body_y + body_h // 2 - 1
    pygame.draw.rect(surf, BELT,       (body_x + 1, belt_y, bw - 2, 3))
    # Belt buckle — small brass square at center
    bk_x = cx - 3
    pygame.draw.rect(surf, OUTLINE,    (bk_x,       belt_y - 1, 6, 5))
    pygame.draw.rect(surf, BELT_BUCKLE,(bk_x + 1,   belt_y,     4, 3))


def _draw_hair(surf, cx, hx, hy, hw, hh, f, s, vx, ticks):
    """
    Structured dark-brown hair:
      - Full cap covering top + back of head
      - Side pieces framing the face
      - A small highlight streak
      - One short tuft at front for character
    """
    # ── Full hair cap (covers top half of head ellipse) ───────────────────────
    cap_rect = (hx - 1, hy - 1, hw + 2, hh // 2 + 6)
    # Shadow cap slightly offset
    shadow_cap = pygame.Surface((cap_rect[2], cap_rect[3] + 3), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_cap, (*OUTLINE, 200),
                        (0, 0, cap_rect[2], cap_rect[3] + 3))
    surf.blit(shadow_cap, (cap_rect[0] + 1, cap_rect[1] + 1))
    # Main cap fill
    cap_surf = pygame.Surface((cap_rect[2], cap_rect[3] + 3), pygame.SRCALPHA)
    pygame.draw.ellipse(cap_surf, (*HAIR, 255),
                        (0, 0, cap_rect[2], cap_rect[3] + 3))
    surf.blit(cap_surf, (cap_rect[0], cap_rect[1]))

    # Midtone band across cap
    mid_surf = pygame.Surface((hw - 4, 5), pygame.SRCALPHA)
    pygame.draw.rect(mid_surf, (*HAIR_MID, 180), (0, 0, hw - 4, 5), border_radius=2)
    surf.blit(mid_surf, (hx + 2, hy + 3))

    # Highlight streak (slightly right of center, angled)
    hi_pts = [
        (cx + 2, hy + 1),
        (cx + 7, hy + 4),
        (cx + 5, hy + 5),
        (cx,     hy + 2),
    ]
    pygame.draw.polygon(surf, HAIR_HI, hi_pts)

    # ── Side pieces — frame the face ─────────────────────────────────────────
    # Left side piece
    pygame.draw.rect(surf, OUTLINE,
                     (hx - 1, hy + hh // 2 - 4, 5, 9), border_radius=2)
    pygame.draw.rect(surf, HAIR,
                     (hx,     hy + hh // 2 - 3, 4, 8), border_radius=2)

    # Right side piece (shorter — more of the face visible)
    pygame.draw.rect(surf, OUTLINE,
                     (hx + hw - 5, hy + hh // 2 - 4, 5, 7), border_radius=2)
    pygame.draw.rect(surf, HAIR,
                     (hx + hw - 5, hy + hh // 2 - 3, 4, 6), border_radius=2)

    # ── Front tuft — one small spike at forehead ──────────────────────────────
    speed = abs(vx)
    # Tuft leans back when running
    if s in ("run", "skid") and speed > 2:
        tx = cx + f * int(min(speed * 1.5, 8))
    else:
        tx = cx + int(math.sin(ticks * 0.0015) * 1.5)

    tuft_pts = [
        (tx - 3, hy + 3),
        (tx,     hy - 6),
        (tx + 3, hy + 3),
    ]
    pygame.draw.polygon(surf, OUTLINE,  [(x+1, y+1) for x, y in tuft_pts])
    pygame.draw.polygon(surf, HAIR_MID, tuft_pts)
    pygame.draw.polygon(surf, OUTLINE,  tuft_pts, 1)

    # Cap outline on top
    pygame.draw.arc(surf, OUTLINE,
                    (hx - 1, hy - 1, hw + 2, hh),
                    math.pi, 2 * math.pi, 2)


def _draw_eyes(surf, cx, cy, hw, hh, f, s, vx, vy, player, ticks):
    speed = abs(vx)
    le_x = cx - 5
    re_x = cx + 5
    e_y  = cy - 1

    ew, eh = 7, 9   # base: tall anime eye

    # Happy squint on land
    sq = getattr(player, 'land_squash', 0)
    if sq > 3:
        for ex in (le_x, re_x):
            pygame.draw.ellipse(surf, EYE_WHITE, (ex - 4, e_y - 2, 9, 7))
            pygame.draw.arc(surf, OUTLINE, (ex - 4, e_y - 2, 9, 7), 0, math.pi, 2)
        pygame.draw.arc(surf, OUTLINE, (cx - 4, e_y + 4, 8, 4), math.pi, 2 * math.pi, 2)
        _blush(surf, le_x, re_x, e_y, 6, 170)
        return

    # State-based shape
    if s == "jump" and vy < -3:
        ew, eh = 7, 11
        pdx, pdy = 0, -2
    elif s == "fall" and vy > 4:
        ew, eh = 8, 8
        pdx, pdy = 0, 2
    elif speed > 5:
        ew, eh = 9, 6   # fierce squint
        pdx, pdy = f * 3, 0
    elif speed > 2:
        pdx, pdy = f * 2, 0
    else:
        pdx = int(math.sin(ticks * 0.0015) * 1.5)
        pdy = 0
        # Blink
        if (ticks // 16) % 220 < 5:
            for ex in (le_x, re_x):
                pygame.draw.ellipse(surf, EYE_WHITE, (ex - ew // 2, e_y - 2, ew, 3))
            return

    for ex in (le_x, re_x):
        # Outline shell
        pygame.draw.ellipse(surf, OUTLINE,
                            (ex - ew // 2 - 1, e_y - eh // 2 - 1, ew + 2, eh + 2))
        # White
        pygame.draw.ellipse(surf, EYE_WHITE,
                            (ex - ew // 2, e_y - eh // 2, ew, eh))
        # Iris
        ix = max(ex - ew // 2 + 2, min(ex + ew // 2 - 2, ex + pdx))
        iy = max(e_y - eh // 2 + 2, min(e_y + eh // 2 - 2, e_y + pdy))
        pygame.draw.circle(surf, EYE_IRIS,  (ix, iy), 3)
        pygame.draw.circle(surf, EYE_PUPIL, (ix, iy), 2)
        # Two glints — makes eyes feel alive
        pygame.draw.circle(surf, EYE_GLINT, (ix + 2, iy - 2), 2)
        pygame.draw.circle(surf, EYE_GLINT, (ix + 3, iy + 1), 1)
        # Top lash — thick arc
        pygame.draw.arc(surf, OUTLINE,
                        (ex - ew // 2 - 1, e_y - eh // 2 - 1, ew + 2, eh + 2),
                        math.pi * 0.15, math.pi * 0.85, 2)

    # Brows — dark brown, expressive
    brow_y = e_y - eh // 2 - 4
    if speed > 5 and s == "run":
        pygame.draw.line(surf, HAIR, (le_x - 4, brow_y - 2), (le_x + 3, brow_y), 2)
        pygame.draw.line(surf, HAIR, (re_x - 3, brow_y),     (re_x + 4, brow_y - 2), 2)
    elif s == "jump" and vy < -3:
        for ex in (le_x, re_x):
            pygame.draw.arc(surf, HAIR,
                            (ex - 5, brow_y - 4, 10, 6),
                            math.pi, 2 * math.pi, 2)
    elif s == "fall" and vy > 5:
        for ex in (le_x, re_x):
            pygame.draw.arc(surf, HAIR,
                            (ex - 5, brow_y - 1, 10, 5), 0, math.pi, 2)
    else:
        # Neutral — slight natural arch
        for ex in (le_x, re_x):
            pygame.draw.line(surf, HAIR,
                             (ex - 4, brow_y), (ex + 4, brow_y - 1), 2)

    _blush(surf, le_x, re_x, e_y, 4, 50)

    # Idle smile
    if abs(vx) < 1 and s not in ("jump", "fall", "roll"):
        pygame.draw.arc(surf, OUTLINE,
                        (cx - 4, e_y + eh // 2, 8, 4), math.pi, 2 * math.pi, 1)


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
    s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
    pygame.draw.circle(s, col, (r + 1, r + 1), r)
    surf.blit(s, (cx - r - 1, cy - r - 1))
