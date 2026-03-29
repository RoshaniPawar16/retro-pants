"""
Pac-Man ghost character renderer for retro-pants.
Drop-in replacement — same public API: draw_fancy_player(surf, player, cam_x)

Reads from player: .x .y .vx .vy .facing .state .anim_frame
                   .land_squash  .pos_history  .color
"""

import pygame
import math
import random

# ── Colors ────────────────────────────────────────────────────────────────────
C_BODY   = (255,  0,   0)    # default ghost red
C_SCARED = (  0,  0, 204)    # frightened blue
C_BLACK  = (  0,  0,   0)
C_WHITE  = (255, 255, 255)
C_PUPIL  = ( 26, 26, 255)    # #1a1aff  bright blue pupils

# ── Gameplay color boost ───────────────────────────────────────────────────────
_COLOR_BOOST: dict[tuple, tuple] = {
    (255,  51,  51): (255,  34,  34),   # Blinky
    (255, 130, 190): (255, 110, 180),   # Pinky
    (  0, 207, 207): (  0, 234, 234),   # Inky
    (255, 184,  71): (255, 170,   0),   # Clyde
}


def _gameplay_color(color: tuple) -> tuple:
    """Return a CRT-compensated version of the ghost body color."""
    if color in _COLOR_BOOST:
        return _COLOR_BOOST[color]
    return tuple(min(255, c + 25) for c in color)  # type: ignore[return-value]


# ── Base ghost dimensions (pixels) ────────────────────────────────────────────
_DOME_R = 14
_BODY_H = 14
_BUMP_H =  6

_TRAIL_ALPHAS = (80, 50, 25, 10)
_TRAIL_SURF_W = 52
_TRAIL_SURF_H = 52


# ── Ghost shape ───────────────────────────────────────────────────────────────

def _ghost_pts(cx: int, cy: int,
               dome_r: int, body_h: int, bump_h: int,
               anim: int,
               ts: float = 1.0,
               tentacle_drift: int = 0,
               wobble_in: int = 0) -> list[tuple[int, int]]:
    """
    Build the complete ghost polygon: dome → rect sides → zigzag bottom.
    ts             = tentacle scale multiplier (1.0 for gameplay).
    tentacle_drift = x offset applied to all tentacle tips (streaming backward).
    wobble_in      = inward tip offset for shape-B idle wobble.
    """
    pts: list[tuple[int, int]] = []

    N = 10
    for i in range(N + 1):
        rad = math.radians(180.0 - i * 18.0)
        pts.append((
            cx + int(dome_r * math.cos(rad)),
            cy - int(dome_r * math.sin(rad)),
        ))

    body_bot = cy + body_h
    pts.append((cx + dome_r, body_bot))

    t10 = max(1, int(10 * ts))
    t5  = max(1, int(5  * ts))
    bh  = bump_h + (1 if anim else 0)
    td  = tentacle_drift
    wi  = wobble_in
    pts += [
        (cx + t10 + td - wi, body_bot + bh),
        (cx + t5  + td,      body_bot),
        (cx       + td,      body_bot + bh),
        (cx - t5  + td,      body_bot),
        (cx - t10 + td + wi, body_bot + bh),
    ]
    pts.append((cx - dome_r, body_bot))
    return pts


def _apply_shear(pts: list[tuple[int, int]],
                 shear_x: int,
                 anchor_y: int,
                 total_range: int) -> list[tuple[int, int]]:
    """
    Linear shear: points at anchor_y are unchanged; top shifts by shear_x.
    Simulates the ghost leaning forward when running.
    """
    if shear_x == 0 or total_range <= 0:
        return pts
    return [
        (x + int(shear_x * max(0, anchor_y - y) / total_range), y)
        for x, y in pts
    ]


# ── Eye helpers ───────────────────────────────────────────────────────────────

def _draw_eyes(surf: pygame.Surface,
               cx: int, dome_cy: int, dome_r: int,
               f: int, s: str,
               vy: float = 0.0,
               land_squash: int = 0,
               t_ms: int = 0,
               speed: float = 0.0) -> None:
    """
    Two large expressive eyes. Expression changes by state.
    Draw order: body → _draw_eyes → glow.
    """
    body_top = dome_cy - dome_r
    ey       = body_top + 12      # eye centre y — upper third of ghost
    ex_left  = cx - 9
    ex_right = cx + 9

    # ── Happy squint: just landed (land_squash > 3) ────────────────────────
    if land_squash > 3:
        eye_w = 12
        for ex in (ex_left, ex_right):
            # Filled top-half oval approximated via clipped SRCALPHA surface
            h_surf = pygame.Surface((eye_w, 7), pygame.SRCALPHA)
            full   = pygame.Surface((eye_w, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(full, C_WHITE, (0, 0, eye_w, 14))
            h_surf.blit(full, (0, 0))   # only top 7px visible
            surf.blit(h_surf, (ex - eye_w // 2, ey - 4))
        # Rosy cheeks
        ck = pygame.Surface((52, 14), pygame.SRCALPHA)
        pygame.draw.circle(ck, (255, 153, 153, 80), ( 7, 7), 5)
        pygame.draw.circle(ck, (255, 153, 153, 80), (45, 7), 5)
        surf.blit(ck, (cx - 26, ey + 5))
        return

    # ── Idle blink (~every 3 s, lasts 100 ms) ─────────────────────────────
    if s == "idle" and (t_ms % 3000) < 100:
        for ex in (ex_left, ex_right):
            pygame.draw.rect(surf, C_WHITE, (ex - 5, ey - 1, 11, 2))
        return

    # ── State flags ───────────────────────────────────────────────────────
    is_jump = (s == "jump" or vy < -3)
    is_fall = (s == "fall" or vy > 4)
    is_fast = (speed > 4 and not is_jump)

    # ── Eye dimensions ────────────────────────────────────────────────────
    if is_jump:
        ew, eh = 13, 17
    elif is_fast:
        ew, eh = 11, 11     # squashed — intense running look
    else:
        ew, eh = 11, 14

    # ── Pupil offset ─────────────────────────────────────────────────────
    if is_jump:
        pdx, pdy = 0, -5
    elif is_fall:
        pdx, pdy = 0,  5
    elif is_fast:
        pdx, pdy = f * 5, 0
    elif s == "idle":
        pdx = int(math.sin(t_ms * 0.002) * 2)
        pdy = 0
    else:
        pdx, pdy = f * 4, 0

    # ── White ovals + pupils ──────────────────────────────────────────────
    for ex in (ex_left, ex_right):
        pygame.draw.ellipse(surf, C_WHITE,
                            (ex - ew // 2, ey - eh // 2, ew, eh))
        pygame.draw.ellipse(surf, C_BLACK,
                            (ex - ew // 2, ey - eh // 2, ew, eh), 2)
        pygame.draw.circle(surf, C_PUPIL, (ex + pdx, ey + pdy), 6)
        pygame.draw.circle(surf, C_WHITE, (ex + pdx + 2, ey + pdy - 2), 2)

    # ── Jump: raised brows (outward) + sweat drop ─────────────────────────
    if is_jump:
        brow_y = ey - eh // 2 - 4
        # Left brow: \ (outer corner higher)
        pygame.draw.line(surf, C_BLACK,
                         (ex_left  - 6, brow_y - 2),
                         (ex_left  + 4, brow_y + 2), 2)
        # Right brow: / (outer corner higher)
        pygame.draw.line(surf, C_BLACK,
                         (ex_right - 4, brow_y + 2),
                         (ex_right + 6, brow_y - 2), 2)
        # Sweat drop on side opposite to facing direction
        sd_x = cx - f * (dome_r + 5)
        sd_y = dome_cy - dome_r // 2
        pygame.draw.circle(surf, (100, 180, 255), (sd_x, sd_y + 4), 3)
        pygame.draw.polygon(surf, (100, 180, 255), [
            (sd_x, sd_y - 4), (sd_x - 3, sd_y + 2), (sd_x + 3, sd_y + 2)
        ])

    # ── Fast run: angry angled brows (downward toward centre) ─────────────
    elif is_fast:
        brow_y = ey - eh // 2 - 3
        pygame.draw.line(surf, C_BLACK,
                         (cx - 14, brow_y - 2), (cx -  6, brow_y + 2), 3)
        pygame.draw.line(surf, C_BLACK,
                         (cx +  6, brow_y + 2), (cx + 14, brow_y - 2), 3)

    # ── Fall: small worried mouth ─────────────────────────────────────────
    if is_fall and not is_fast:
        mouth_rect = pygame.Rect(cx - 7, dome_cy + 8, 14, 7)
        pygame.draw.arc(surf, C_BLACK, mouth_rect,
                        math.pi, 2 * math.pi, 2)


def _draw_scared_face(surf: pygame.Surface,
                      cx: int, dome_cy: int, dome_r: int) -> None:
    """Frightened ghost: wavy white eye lines + 5-point zigzag mouth."""
    t        = pygame.time.get_ticks()
    body_top = dome_cy - dome_r

    for ex in (cx - 9, cx + 9):
        ey   = body_top + 12
        wave = [(ex - 4 + k * 2,
                 ey + int(math.sin(k * math.pi + t / 200.0) * 3))
                for k in range(5)]
        pygame.draw.lines(surf, C_WHITE, False, wave, 2)

    mouth_y = dome_cy + 5
    step    = max(1, (dome_r * 2 - 4) // 4)
    mouth   = [(cx - dome_r + 2 + k * step,
                mouth_y + (3 if k % 2 == 0 else -3))
               for k in range(5)]
    if len(mouth) >= 2:
        pygame.draw.lines(surf, C_WHITE, False, mouth, 2)


# ── Ghost preview (character select screen) ───────────────────────────────────

def draw_ghost_preview(surf: pygame.Surface,
                       cx: int, cy: int,
                       color: tuple,
                       scale: float = 1.0,
                       anim: int = 0) -> None:
    """Draw a static, scaled ghost centred at (cx, cy). Used on select screen."""
    dome_r = max(2, int(_DOME_R * scale))
    body_h = max(2, int(_BODY_H * scale))
    bump_h = max(1, int(_BUMP_H * scale))

    total_h = dome_r + body_h + bump_h
    dome_cy = cy - total_h // 2 + dome_r

    pts = _ghost_pts(cx, dome_cy, dome_r, body_h, bump_h, anim, ts=scale)
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, C_BLACK, pts, 2)

    body_top = dome_cy - dome_r
    ey       = body_top + max(4, int(12 * scale))
    ex_off   = max(3, int(9  * scale))
    ew       = max(4, int(11 * scale))
    eh       = max(5, int(14 * scale))
    pr       = max(2, int(6  * scale))
    glint_r  = max(1, int(2  * scale))

    for ex in (cx - ex_off, cx + ex_off):
        pygame.draw.ellipse(surf, C_WHITE, (ex - ew // 2, ey - eh // 2, ew, eh))
        pygame.draw.ellipse(surf, C_BLACK, (ex - ew // 2, ey - eh // 2, ew, eh), 2)
        pygame.draw.circle(surf, C_PUPIL, (ex, ey), pr)
        pygame.draw.circle(surf, C_WHITE, (ex + glint_r, ey - glint_r), glint_r)


# ── Main entry point ──────────────────────────────────────────────────────────

def draw_fancy_player(surf: pygame.Surface,
                      player: object,
                      cam_x: int) -> None:
    """
    Render the player as an expressive Pac-Man ghost with motion effects.
    Called every frame by Player.draw(surf, cam_x) in main.py.
    """
    px = int(player.x) - cam_x   # type: ignore[attr-defined]
    py = int(player.y)            # type: ignore[attr-defined]
    f  = player.facing            # type: ignore[attr-defined]
    s  = player.state             # type: ignore[attr-defined]
    fr = player.anim_frame        # type: ignore[attr-defined]
    vx = player.vx                # type: ignore[attr-defined]
    vy = player.vy                # type: ignore[attr-defined]

    cx     = px + 11
    feet_y = py + 30

    speed        = abs(vx)
    land_squash  = getattr(player, 'land_squash',  0)
    pos_history  = getattr(player, 'pos_history',  [])
    player_color = getattr(player, 'color',        C_BODY)
    bright_color = _gameplay_color(player_color)
    t_ms         = pygame.time.get_ticks()
    scared       = (s == "roll")

    # ── Squash / stretch ────────────────────────────────────────────────────
    dome_r = _DOME_R
    body_h = _BODY_H
    bump_h = _BUMP_H

    if s == "jump" and vy < -2:
        dome_r -= 1
        body_h += 4
    elif land_squash > 0:
        t = land_squash / 6.0
        dome_r += int(t * 3)
        body_h  = max(4, body_h - int(t * 3))
    elif speed > 4 and s in ("run", "skid"):
        dome_r += 1
        body_h -= 1

    # ── Idle float: 3 px vertical bob + 1 px horizontal sway ───────────────
    if s == "idle":
        bob  = int(math.sin(t_ms * 0.003) * 3)
        cx  += int(math.sin(t_ms * 0.002) * 1)
    else:
        bob = 0

    # ── Dome centre ──────────────────────────────────────────────────────────
    dome_cy     = feet_y - bump_h - body_h + bob
    body_bot    = dome_cy + body_h
    total_range = dome_r + body_h

    # ── Tentacle animation ───────────────────────────────────────────────────
    anim = (fr // 2) % 2

    if speed > 5:
        # Tentacles stream backward
        tentacle_drift = int(-f * min(speed * 0.8, 12))
        wobble_in      = 0
    else:
        tentacle_drift = 0
        wobble_in      = 3 if ((t_ms // 200) % 2 == 1) else 0

    # ── Body lean: shear top forward when running ────────────────────────────
    if s in ("jump",) or land_squash > 0:
        shear_x = 0
    else:
        shear_x = int(min(speed * 1.8, 14)) * f

    body_col = C_SCARED if scared else bright_color
    glow_col = C_SCARED if scared else bright_color

    # ── 1. Shadow ─────────────────────────────────────────────────────────
    sh_w = 24 + (int(land_squash * 2) if land_squash > 0 else 0)
    sh_s = pygame.Surface((sh_w, 6), pygame.SRCALPHA)
    pygame.draw.ellipse(sh_s, (0, 0, 0, 60), (0, 0, sh_w, 6))
    surf.blit(sh_s, (cx - sh_w // 2, feet_y - 2))

    # ── 2. Motion blur trail (speed > 5) ──────────────────────────────────
    if speed > 5:
        for off, alpha in ((8, 50), (16, 30), (24, 15)):
            mb = pygame.Surface((64, 72), pygame.SRCALPHA)
            mb_pts = _ghost_pts(32, 24, dome_r, body_h, bump_h, anim,
                                tentacle_drift=tentacle_drift)
            mb_pts = _apply_shear(mb_pts, shear_x, 24 + body_h, total_range)
            pygame.draw.polygon(mb, (*body_col, alpha), mb_pts)
            surf.blit(mb, (cx - f * off - 32, dome_cy - 24))

    # ── 3. Ghost trail (pos_history) ────────────────────────────────────────
    tr_dome_r = max(2, int(_DOME_R * 0.6))
    tr_body_h = max(2, int(_BODY_H * 0.6))
    tr_bump_h = max(1, int(_BUMP_H * 0.6))
    t_half    = _TRAIL_SURF_W // 2
    t_top_pad = tr_dome_r + 3

    for i, (hx, hy) in enumerate(pos_history[:4]):
        alpha   = _TRAIL_ALPHAS[i]
        rx      = hx - cam_x + 11
        ry_dome = (hy + 30) - _BUMP_H - _BODY_H
        t_surf  = pygame.Surface((_TRAIL_SURF_W, _TRAIL_SURF_H), pygame.SRCALPHA)
        t_pts   = _ghost_pts(t_half, t_top_pad,
                             tr_dome_r, tr_body_h, tr_bump_h, anim)
        pygame.draw.polygon(t_surf, (*bright_color, alpha), t_pts)
        surf.blit(t_surf, (rx - t_half, ry_dome - t_top_pad))

    # ── 4. Speed lines (speed > 3) ────────────────────────────────────────
    if speed > 3:
        line_len   = int(max(15, min(speed * 6, 55)))
        extra_len  = 70 if speed > 7 else 0
        total_len  = line_len + extra_len
        ghost_top  = dome_cy - dome_r
        ghost_h_rng = dome_r + body_h

        sp_w = total_len + 20
        sp_h = ghost_h_rng + 24
        sp   = pygame.Surface((sp_w, sp_h), pygame.SRCALPHA)

        # Stable random per 2-frame tick so lines don't flicker
        rng = random.Random(t_ms // 33)

        # White extra lines drawn first (furthest back)
        if speed > 7:
            for idx in (1, 4):
                ly = int((idx + 0.5) * ghost_h_rng / 6) + 12 + rng.randint(-6, 6)
                pygame.draw.line(sp, (255, 255, 255, 60),
                                 (0, ly), (sp_w, ly), 1)

        # Colored lines: 3 alpha segments — right edge = ghost side
        for i in range(6):
            ly  = int((i + 0.5) * ghost_h_rng / 6) + 12 + rng.randint(-4, 4)
            seg = line_len // 3
            for a, w, x0, x1 in (
                (120, 2, sp_w - seg,     sp_w),
                ( 70, 1, sp_w - seg * 2, sp_w - seg),
                ( 30, 1, sp_w - seg * 3, sp_w - seg * 2),
            ):
                pygame.draw.line(sp, (*body_col, a), (x0, ly), (x1, ly), w)

        if f == 1:   # facing right → lines trail left
            surf.blit(sp, (cx - dome_r - sp_w, ghost_top - 12))
        else:        # facing left → flip and trail right
            surf.blit(pygame.transform.flip(sp, True, False),
                      (cx + dome_r, ghost_top - 12))

    # ── 5. Ghost body ─────────────────────────────────────────────────────
    pts = _ghost_pts(cx, dome_cy, dome_r, body_h, bump_h, anim,
                     tentacle_drift=tentacle_drift, wobble_in=wobble_in)
    pts = _apply_shear(pts, shear_x, body_bot, total_range)
    pygame.draw.polygon(surf, body_col, pts)
    pygame.draw.polygon(surf, C_BLACK,  pts, 2)

    # ── 6. Eyes / scared face ─────────────────────────────────────────────
    if scared:
        _draw_scared_face(surf, cx, dome_cy, dome_r)
    else:
        _draw_eyes(surf, cx, dome_cy, dome_r, f, s, vy,
                   land_squash, t_ms, speed)

    # ── 7. Neon glow (bloom on top — alpha 40, barely tints eyes) ─────────
    glow_surf = pygame.Surface((64, 72), pygame.SRCALPHA)
    glow_pts  = _ghost_pts(32, 24, dome_r + 4, body_h + 4, bump_h + 4, anim,
                           tentacle_drift=tentacle_drift, wobble_in=wobble_in)
    glow_pts  = _apply_shear(glow_pts, shear_x,
                             24 + body_h + 4, dome_r + 4 + body_h + 4)
    pygame.draw.polygon(glow_surf, (*glow_col, 40), glow_pts)
    surf.blit(glow_surf, (cx - 32, dome_cy - 24))
