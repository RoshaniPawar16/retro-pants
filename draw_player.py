"""
Pac-Man ghost character renderer for retro-pants.
Drop-in replacement — same public API: draw_fancy_player(surf, player, cam_x)

Reads from player: .x .y .vx .vy .facing .state .anim_frame
                   .land_squash  .pos_history  .color  (all added by main.py)
"""

import pygame
import math

# ── Colors ────────────────────────────────────────────────────────────────────
C_BODY   = (255,  0,   0)    # #FF0000  default ghost red
C_SCARED = (  0,  0, 204)    # #0000CC  frightened blue
C_BLACK  = (  0,  0,   0)
C_WHITE  = (255, 255, 255)
C_PUPIL  = ( 34, 34,  153)   # #222299  deep blue pupils

# ── Base ghost dimensions (pixels) ────────────────────────────────────────────
_DOME_R = 14    # dome radius  = half body width (total width = 28px)
_BODY_H = 14    # rectangular body height below dome flat edge
_BUMP_H =  6    # depth of tentacle bumps below body bottom
                # total unscaled height = 14 + 14 + 6 = 34px

_TRAIL_ALPHAS = (80, 50, 25, 10)
_TRAIL_SURF_W = 52   # bounding surface width for trail ghosts
_TRAIL_SURF_H = 52   # bounding surface height for trail ghosts


# ── Ghost shape ───────────────────────────────────────────────────────────────

def _ghost_pts(cx: int, cy: int,
               dome_r: int, body_h: int, bump_h: int,
               anim: int, ts: float = 1.0) -> list[tuple[int, int]]:
    """
    Build the complete ghost polygon: dome → rect sides → zigzag bottom.
    cx/cy = dome centre (x, y) in surface coordinates.
    anim  = 0 or 1; bumps extend 1px deeper on phase 1 (floating feel).
    ts    = tentacle scale multiplier (default 1.0 for gameplay; use scale for previews).
    """
    pts: list[tuple[int, int]] = []

    # Semicircle dome — 11 points arcing left → top → right
    N = 10
    for i in range(N + 1):
        rad = math.radians(180.0 - i * 18.0)
        pts.append((
            cx + int(dome_r * math.cos(rad)),
            cy - int(dome_r * math.sin(rad)),
        ))

    # Right side straight down to body-bottom
    body_bot = cy + body_h
    pts.append((cx + dome_r, body_bot))

    # Zigzag tentacles — 3 bumps, right → left (scaled by ts)
    t10 = max(1, int(10 * ts))
    t5  = max(1, int(5  * ts))
    bh  = bump_h + (1 if anim else 0)
    pts += [
        (cx + t10, body_bot + bh),
        (cx + t5,  body_bot),
        (cx,       body_bot + bh),
        (cx - t5,  body_bot),
        (cx - t10, body_bot + bh),
    ]

    # Left side back up to dome start (polygon auto-closes)
    pts.append((cx - dome_r, body_bot))

    return pts


# ── Eye helpers ───────────────────────────────────────────────────────────────

def _draw_eyes(surf: pygame.Surface,
               cx: int, dome_cy: int, dome_r: int,
               f: int, s: str,
               vy: float = 0.0,
               land_squash: int = 0,
               t_ms: int = 0) -> None:
    """
    Two large expressive oval eyes with directional deep-blue pupils.
    Eyes sit in the upper portion of the ghost dome.
    """
    body_top = dome_cy - dome_r
    ey       = body_top + 10    # eye centre y — upper portion of dome
    ex_left  = cx - 8
    ex_right = cx + 8

    # ── Happy squint: just landed ──────────────────────────────────────────
    if land_squash > 0:
        for ex in (ex_left, ex_right):
            # White fill behind arc
            pygame.draw.ellipse(surf, C_WHITE, (ex - 5, ey - 3, 10, 8))
            # Upward arc (happy squint)
            pygame.draw.arc(surf, C_BLACK,
                            pygame.Rect(ex - 5, ey - 3, 10, 8),
                            0, math.pi, 2)
        return

    # ── Eye dimensions ────────────────────────────────────────────────────
    is_jump = (s == "jump")
    ew = 10
    eh = 16 if is_jump else 13

    # ── Pupil shift ───────────────────────────────────────────────────────
    if is_jump or vy < -4:
        pdx, pdy = 0, -3
    elif s == "fall" or vy > 5:
        pdx, pdy = 0,  3
    elif s == "idle":
        pdx = int(math.sin(t_ms / 800.0) * 2)
        pdy = 0
    else:
        pdx, pdy = f * 3, 0

    for ex in (ex_left, ex_right):
        # White oval
        pygame.draw.ellipse(surf, C_WHITE,
                            (ex - ew // 2, ey - eh // 2, ew, eh))
        # Black outline (~1.5px → use 2)
        pygame.draw.ellipse(surf, C_BLACK,
                            (ex - ew // 2, ey - eh // 2, ew, eh), 2)
        # Blue pupil — filled circle radius 5
        pygame.draw.circle(surf, C_PUPIL, (ex + pdx, ey + pdy), 5)
        # White glint — top-right of pupil, radius 2
        pygame.draw.circle(surf, C_WHITE, (ex + pdx + 2, ey + pdy - 2), 2)

    # ── Eyebrows on jump ─────────────────────────────────────────────────
    if is_jump:
        brow_y = ey - eh // 2 - 4
        # Left brow angles upward toward centre  /
        pygame.draw.line(surf, C_BLACK,
                         (ex_left - 5,  brow_y + 2),
                         (ex_left + 5,  brow_y - 2), 2)
        # Right brow mirrors  \
        pygame.draw.line(surf, C_BLACK,
                         (ex_right - 5, brow_y - 2),
                         (ex_right + 5, brow_y + 2), 2)


def _draw_scared_face(surf: pygame.Surface,
                      cx: int, dome_cy: int, dome_r: int) -> None:
    """
    Frightened ghost face: squiggly white eye lines + zigzag white mouth.
    """
    t = pygame.time.get_ticks()

    # Squiggly white line for each eye
    body_top = dome_cy - dome_r
    for ex in (cx - 8, cx + 8):
        ey = body_top + 10
        wave: list[tuple[int, int]] = []
        for k in range(5):
            wx = ex - 4 + k * 2
            wy = ey + int(math.sin(k * math.pi + t / 200.0) * 2)
            wave.append((wx, wy))
        pygame.draw.lines(surf, C_WHITE, False, wave, 2)

    # Zigzag mouth — spans most of the dome width
    mouth_y = dome_cy + 5
    step    = max(1, (dome_r * 2 - 4) // 6)
    mouth: list[tuple[int, int]] = []
    for k in range(7):
        mx = cx - dome_r + 2 + k * step
        my = mouth_y + (3 if k % 2 == 0 else -3)
        mouth.append((mx, my))
    if len(mouth) >= 2:
        pygame.draw.lines(surf, C_WHITE, False, mouth, 2)


# ── Ghost preview (for character select screen) ───────────────────────────────

def draw_ghost_preview(surf: pygame.Surface,
                       cx: int, cy: int,
                       color: tuple,
                       scale: float = 1.0,
                       anim: int = 0) -> None:
    """
    Draw a static ghost centered at (cx, cy) at the given scale.
    Used by the character selection screen in main.py.
    """
    dome_r = max(2, int(_DOME_R * scale))
    body_h = max(2, int(_BODY_H * scale))
    bump_h = max(1, int(_BUMP_H * scale))

    # Vertically centre the ghost at cy
    total_h = dome_r + body_h + bump_h
    dome_cy = cy - total_h // 2 + dome_r

    pts = _ghost_pts(cx, dome_cy, dome_r, body_h, bump_h, anim, ts=scale)
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, C_BLACK, pts, 2)

    # Eyes (scaled)
    body_top = dome_cy - dome_r
    ey       = body_top + max(4, int(10 * scale))
    ex_off   = max(3, int(8  * scale))
    ew       = max(4, int(10 * scale))
    eh       = max(5, int(13 * scale))
    pr       = max(2, int(5  * scale))
    glint_r  = max(1, int(2  * scale))

    for ex in (cx - ex_off, cx + ex_off):
        pygame.draw.ellipse(surf, C_WHITE, (ex - ew // 2, ey - eh // 2, ew, eh))
        pygame.draw.ellipse(surf, C_BLACK, (ex - ew // 2, ey - eh // 2, ew, eh), 2)
        pygame.draw.circle(surf, C_PUPIL, (ex, ey), pr)
        pygame.draw.circle(surf, C_WHITE,
                           (ex + glint_r, ey - glint_r), glint_r)


# ── Main entry point ──────────────────────────────────────────────────────────

def draw_fancy_player(surf: pygame.Surface,
                      player: object,
                      cam_x: int) -> None:
    """
    Render the player as a Pac-Man ghost.
    Called every frame by Player.draw(surf, cam_x) in main.py.
    """
    px = int(player.x) - cam_x   # type: ignore[attr-defined]
    py = int(player.y)            # type: ignore[attr-defined]
    f  = player.facing            # type: ignore[attr-defined]
    s  = player.state             # type: ignore[attr-defined]
    fr = player.anim_frame        # type: ignore[attr-defined]
    vx = player.vx                # type: ignore[attr-defined]
    vy = player.vy                # type: ignore[attr-defined]

    cx     = px + 11    # horizontal centre of 22px hitbox
    feet_y = py + 30    # bottom of 30px hitbox

    speed        = abs(vx)
    land_squash  = getattr(player, 'land_squash',  0)
    pos_history  = getattr(player, 'pos_history',  [])
    player_color = getattr(player, 'color',        C_BODY)
    t_ms         = pygame.time.get_ticks()
    scared       = (s == "roll")

    # ── Squash / stretch ────────────────────────────────────────────────────
    dome_r = _DOME_R
    body_h = _BODY_H
    bump_h = _BUMP_H

    if s == "jump" and vy < -2:
        dome_r -= 1          # narrower
        body_h += 4          # stretch tall
    elif land_squash > 0:
        t = land_squash / 6.0
        dome_r += int(t * 3)
        body_h  = max(4, body_h - int(t * 3))   # squash wide + short
    elif speed > 4 and s in ("run", "skid"):
        dome_r += 1          # wobble: slightly wider when sprinting
        body_h -= 1

    # Float bob when idle
    bob = int(math.sin(t_ms / 300.0)) if s == "idle" else 0

    # Dome centre y: tentacle tips land at feet_y
    dome_cy = feet_y - bump_h - body_h + bob

    # Tentacle animation phase — toggles every 2 anim-frames
    anim = (fr // 2) % 2

    body_col = C_SCARED if scared else player_color

    # ── 1. Shadow ─────────────────────────────────────────────────────────
    sh_w = 24 + (int(land_squash * 2) if land_squash > 0 else 0)
    sh_s = pygame.Surface((sh_w, 6), pygame.SRCALPHA)
    pygame.draw.ellipse(sh_s, (0, 0, 0, 60), (0, 0, sh_w, 6))
    surf.blit(sh_s, (cx - sh_w // 2, feet_y - 2))

    # ── 2. Ghost trail (faint smaller outlines at past positions) ──────────
    tr_dome_r = max(2, int(_DOME_R * 0.6))
    tr_body_h = max(2, int(_BODY_H * 0.6))
    tr_bump_h = max(1, int(_BUMP_H * 0.6))
    t_half    = _TRAIL_SURF_W // 2
    t_top_pad = tr_dome_r + 3

    for i, (hx, hy) in enumerate(pos_history[:4]):
        alpha   = _TRAIL_ALPHAS[i]
        rx      = hx - cam_x + 11
        ry_dome = (hy + 30) - _BUMP_H - _BODY_H

        t_surf = pygame.Surface((_TRAIL_SURF_W, _TRAIL_SURF_H), pygame.SRCALPHA)
        t_pts  = _ghost_pts(t_half, t_top_pad,
                            tr_dome_r, tr_body_h, tr_bump_h, anim)
        pygame.draw.polygon(t_surf, (*player_color, alpha), t_pts)
        surf.blit(t_surf, (rx - t_half, ry_dome - t_top_pad))

    # ── 3. Ghost body ─────────────────────────────────────────────────────
    pts = _ghost_pts(cx, dome_cy, dome_r, body_h, bump_h, anim)
    pygame.draw.polygon(surf, body_col, pts)
    pygame.draw.polygon(surf, C_BLACK,  pts, 2)

    # ── 4. Eyes / scared face ─────────────────────────────────────────────
    if scared:
        _draw_scared_face(surf, cx, dome_cy, dome_r)
    else:
        _draw_eyes(surf, cx, dome_cy, dome_r, f, s, vy, land_squash, t_ms)
