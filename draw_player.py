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
C_BODY    = (255,  0,   0)    # default ghost red
C_SCARED  = (  0,  0, 204)    # frightened blue
C_BLACK   = (  0,  0,   0)
C_WHITE   = (255, 255, 255)
C_PUPIL   = ( 26, 26, 255)    # #1a1aff  bright blue pupils
C_OUTLINE = ( 26, 10,  46)    # #1A0A2E  Sea of Stars soft dark purple

# ── Gameplay color — soft painterly desaturation ──────────────────────────────
def _gameplay_color(color: tuple) -> tuple:
    """Soften the ghost color: 80% original + 20% white — painterly, not arcade-harsh."""
    return tuple(min(255, int(c * 0.80 + 255 * 0.20)) for c in color)  # type: ignore[return-value]


# ── Base ghost dimensions (pixels) ────────────────────────────────────────────
_DOME_R = 17   # +20% wider/chunkier (was 14)
_BODY_H = 14
_BUMP_H =  5

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
    Build the complete ghost polygon: dome → sides → smooth 3-bump bottom.
    ts             = scale multiplier (character select).
    tentacle_drift = x-shift on all bottom points (speed streaming).
    wobble_in      = flatten bumps inward for shape-B idle.
    """
    pts: list[tuple[int, int]] = []

    # Dome: 14 points for a rounder arc
    N = 14
    for i in range(N + 1):
        rad = math.radians(180.0 - i * 180.0 / N)
        pts.append((
            cx + int(dome_r * math.cos(rad)),
            cy - int(dome_r * math.sin(rad)),
        ))

    body_bot = cy + body_h
    pts.append((cx + dome_r, body_bot))

    # Smooth 3-bump bottom via sampled sine wave (right → left)
    bh    = bump_h + (1 if anim else 0)
    if wobble_in > 0:
        bh = max(1, bh - wobble_in)
    td    = tentacle_drift
    n_pts = 24    # sample count for smooth curve
    for i in range(n_pts + 1):
        t  = i / n_pts                           # 0 = right side, 1 = left side
        bx = int(cx + dome_r - t * dome_r * 2) + td
        by = body_bot + int(bh * abs(math.sin(t * math.pi * 3)))
        pts.append((bx, by))

    pts.append((cx - dome_r, body_bot))
    return pts


def _tentacle_nub_positions(cx: int, body_bot: int, dome_r: int,
                             bump_h: int, tentacle_drift: int) -> list[tuple[int, int]]:
    """Return the (x, y) centres of the 3 tentacle tips for nub drawing."""
    bh = bump_h
    td = tentacle_drift
    return [
        (int(cx + dome_r * (1 - 2 * k / 3) - dome_r / 3) + td,
         body_bot + bh)
        for k in range(3)
    ]


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
               speed: float = 0.0,
               body_color: tuple = (255, 0, 0)) -> None:
    """
    Sea of Stars style expressive eyes with colored iris, dual glint, cheek blush.
    """
    body_top = dome_cy - dome_r
    ey       = body_top + 13
    ex_left  = cx - 10
    ex_right = cx + 10

    # Iris color: 50% body color + 50% white
    iris_col = tuple(min(255, int(c * 0.5 + 127)) for c in body_color)
    # Blush color: body color × 0.4 + white × 0.6
    blush_col = tuple(min(255, int(c * 0.40 + 153)) for c in body_color)

    def _blush(ey_local: int) -> None:
        """Always-on subtle cheek blush."""
        ck = pygame.Surface((58, 16), pygame.SRCALPHA)
        pygame.draw.circle(ck, (*blush_col, 60), ( 8, 8), 5)
        pygame.draw.circle(ck, (*blush_col, 60), (50, 8), 5)
        surf.blit(ck, (cx - 29, ey_local + 6))

    # ── Happy squint (land_squash > 3) ────────────────────────────────────
    if land_squash > 3:
        eye_w = 14
        for ex in (ex_left, ex_right):
            h_surf = pygame.Surface((eye_w, 8), pygame.SRCALPHA)
            full   = pygame.Surface((eye_w, 16), pygame.SRCALPHA)
            pygame.draw.ellipse(full, C_WHITE, (0, 0, eye_w, 16))
            h_surf.blit(full, (0, 0))
            surf.blit(h_surf, (ex - eye_w // 2, ey - 4))
        # Big rosy cheeks on happy
        ck2 = pygame.Surface((62, 18), pygame.SRCALPHA)
        pygame.draw.circle(ck2, (*blush_col, 110), ( 9, 9), 7)
        pygame.draw.circle(ck2, (*blush_col, 110), (53, 9), 7)
        surf.blit(ck2, (cx - 31, ey + 5))
        return

    # ── Idle blink (~every 3 s, 100 ms) ───────────────────────────────────
    if s == "idle" and (t_ms % 3000) < 100:
        for ex in (ex_left, ex_right):
            pygame.draw.rect(surf, C_WHITE, (ex - 6, ey - 1, 13, 3))
        _blush(ey)
        return

    # ── State flags ───────────────────────────────────────────────────────
    is_jump = (s == "jump" or vy < -3)
    is_fall = (s == "fall" or vy > 4)
    is_fast = (speed > 4 and not is_jump)

    # ── Eye dimensions ────────────────────────────────────────────────────
    if is_jump:
        ew, eh = 13, 18
    elif is_fast:
        ew, eh = 12, 11
    else:
        ew, eh = 13, 16   # base: 13×16

    # ── Pupil offset ─────────────────────────────────────────────────────
    if is_jump:
        pdx, pdy = 0, -5
    elif is_fall:
        pdx, pdy = 0,  5
    elif is_fast:
        pdx, pdy = f * 4, 0
    elif s == "idle":
        pdx = int(math.sin(t_ms * 0.002) * 2)
        pdy = 0
    else:
        pdx, pdy = f * 3, 0

    # ── White ovals + colored iris + dark pupil + dual glints ────────────
    for ex in (ex_left, ex_right):
        # White oval
        pygame.draw.ellipse(surf, C_WHITE,
                            (ex - ew // 2, ey - eh // 2, ew, eh))
        # Outline: soft dark purple, 2px
        pygame.draw.ellipse(surf, C_OUTLINE,
                            (ex - ew // 2, ey - eh // 2, ew, eh), 2)
        # Colored iris (r=7)
        pygame.draw.circle(surf, iris_col, (ex + pdx, ey + pdy), 7)
        # Dark pupil (r=4, #1A0A2E)
        pygame.draw.circle(surf, C_OUTLINE, (ex + pdx, ey + pdy), 4)
        # Large glint
        pygame.draw.circle(surf, C_WHITE,
                           (ex + pdx + 2, ey + pdy - 2), 2)
        # Small glint
        pygame.draw.circle(surf, C_WHITE,
                           (ex + pdx + 3, ey + pdy + 1), 1)

    # ── Always-on blush ───────────────────────────────────────────────────
    _blush(ey)

    # ── Jump: raised brows + sweat drop ───────────────────────────────────
    if is_jump:
        brow_y = ey - eh // 2 - 4
        pygame.draw.line(surf, C_OUTLINE,
                         (ex_left  - 6, brow_y - 2),
                         (ex_left  + 4, brow_y + 2), 2)
        pygame.draw.line(surf, C_OUTLINE,
                         (ex_right - 4, brow_y + 2),
                         (ex_right + 6, brow_y - 2), 2)
        sd_x = cx - f * (dome_r + 5)
        sd_y = dome_cy - dome_r // 2
        pygame.draw.circle(surf, (100, 180, 255), (sd_x, sd_y + 4), 3)
        pygame.draw.polygon(surf, (100, 180, 255), [
            (sd_x, sd_y - 4), (sd_x - 3, sd_y + 2), (sd_x + 3, sd_y + 2)
        ])

    # ── Fast run: soft curved brows (arc-based, less harsh) ───────────────
    elif is_fast:
        brow_y = ey - eh // 2 - 3
        # Left brow: gentle curve downward toward center
        bl = pygame.Rect(cx - 16, brow_y - 3, 11, 7)
        pygame.draw.arc(surf, C_OUTLINE, bl,
                        math.radians(200), math.radians(330), 2)
        # Right brow: mirror
        br_rect = pygame.Rect(cx + 5, brow_y - 3, 11, 7)
        pygame.draw.arc(surf, C_OUTLINE, br_rect,
                        math.radians(210), math.radians(340), 2)

    # ── Fall: worried mouth ────────────────────────────────────────────────
    if is_fall and not is_fast:
        mouth_rect = pygame.Rect(cx - 7, dome_cy + 9, 14, 7)
        pygame.draw.arc(surf, C_OUTLINE, mouth_rect,
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
    # Soft drop shadow offset +1
    shadow_pts = [(x + 1, y + 1) for x, y in pts]
    pygame.draw.polygon(surf, C_OUTLINE, shadow_pts)
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, C_OUTLINE, pts, 2)

    body_top  = dome_cy - dome_r
    ey        = body_top + max(4, int(13 * scale))
    ex_off    = max(3, int(10 * scale))
    ew        = max(4, int(13 * scale))
    eh        = max(5, int(16 * scale))
    iris_r    = max(3, int(7  * scale))
    pupil_r   = max(2, int(4  * scale))
    glint_r   = max(1, int(2  * scale))
    iris_col  = tuple(min(255, int(c * 0.5 + 127)) for c in color)

    for ex in (cx - ex_off, cx + ex_off):
        pygame.draw.ellipse(surf, C_WHITE,    (ex - ew // 2, ey - eh // 2, ew, eh))
        pygame.draw.ellipse(surf, C_OUTLINE,  (ex - ew // 2, ey - eh // 2, ew, eh), 2)
        pygame.draw.circle(surf, iris_col,    (ex, ey), iris_r)
        pygame.draw.circle(surf, C_OUTLINE,   (ex, ey), pupil_r)
        pygame.draw.circle(surf, C_WHITE,     (ex + glint_r, ey - glint_r), glint_r)
        pygame.draw.circle(surf, C_WHITE,     (ex + glint_r + 1, ey + 1), max(1, glint_r - 1))


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
        # Tentacles stream backward when running fast
        tentacle_drift = int(-f * min(speed * 0.8, 12))
        wobble_in      = 0
    elif s == "idle":
        # Gentle sway in idle
        tentacle_drift = int(math.sin(t_ms * 0.0015) * 4)
        wobble_in      = 3 if ((t_ms // 200) % 2 == 1) else 0
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

    # Soft drop shadow: dark shape +1px down-right, then body on top
    shadow_pts = [(x + 1, y + 1) for x, y in pts]
    pygame.draw.polygon(surf, C_OUTLINE, shadow_pts)
    pygame.draw.polygon(surf, body_col, pts)
    pygame.draw.polygon(surf, C_OUTLINE, pts, 2)

    # Tentacle nubs: small circles at the 3 bump tips
    nub_col = body_col
    nub_positions = _tentacle_nub_positions(
        cx, body_bot, dome_r, bump_h + (1 if anim else 0), tentacle_drift)
    for nx, ny in nub_positions:
        pygame.draw.circle(surf, nub_col, (nx, ny), 3)
        pygame.draw.circle(surf, C_OUTLINE, (nx, ny), 3, 1)

    # ── 6. Eyes / scared face ─────────────────────────────────────────────
    if scared:
        _draw_scared_face(surf, cx, dome_cy, dome_r)
    else:
        _draw_eyes(surf, cx, dome_cy, dome_r, f, s, vy,
                   land_squash, t_ms, speed,
                   body_color=player_color)

    # ── 7. Neon glow (bloom on top — alpha 40, barely tints eyes) ─────────
    glow_surf = pygame.Surface((64, 72), pygame.SRCALPHA)
    glow_pts  = _ghost_pts(32, 24, dome_r + 4, body_h + 4, bump_h + 4, anim,
                           tentacle_drift=tentacle_drift, wobble_in=wobble_in)
    glow_pts  = _apply_shear(glow_pts, shear_x,
                             24 + body_h + 4, dome_r + 4 + body_h + 4)
    pygame.draw.polygon(glow_surf, (*glow_col, 40), glow_pts)
    surf.blit(glow_surf, (cx - 32, dome_cy - 24))
