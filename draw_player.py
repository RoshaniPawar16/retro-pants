"""
STAR KID character renderer for retro-pants.
Drop-in replacement — same public API: draw_fancy_player(surf, player, cam_x)

Reads from player: .x .y .vx .vy .facing .state .anim_frame
                   .land_squash  .pos_history  .color
"""

import pygame
import math

# ── Fixed body colors ──────────────────────────────────────────────────────────
C_BODY    = (232, 224, 240)   # #E8E0F0  soft warm white / lavender
C_SHADE   = (200, 192, 220)   # #C8C0DC  head left-side crescent shading
C_LEGS    = (208, 200, 232)   # #D0C8E8  leg fill
C_FEET    = ( 42,  26,  94)   # #2A1A5E  foot fill
C_IRIS    = ( 42,  26,  94)   # #2A1A5E  deep indigo iris
C_PUPIL   = ( 10,   4,  16)   # #0A0410  near-black pupil
C_OUTLINE = ( 26,  10,  46)   # #1A0A2E  Sea of Stars dark purple
C_BLUSH   = (255, 176, 192)   # #FFB0C0  landing blush


# ── Eyes ───────────────────────────────────────────────────────────────────────

def _draw_star_eyes(surf: pygame.Surface,
                    cx: int, cy: int,
                    hw: int, hh: int,
                    f: int, s: str,
                    vy: float,
                    land_squash: int,
                    t_ms: int,
                    speed: float) -> None:
    """Sea of Stars style expressive eyes on the head circle."""
    is_jump = (s == "jump" or vy < -3)
    is_fall = (s == "fall" or vy > 4)
    is_fast = speed > 6 and not is_jump
    is_run  = speed > 2 and not is_jump and not is_fall

    ey   = cy - 2
    ex_l = cx - 6
    ex_r = cx + 6

    # Landing: happy squint (lower half of eye oval only)
    if land_squash > 3:
        for ex in (ex_l, ex_r):
            sq = pygame.Surface((14, 12), pygame.SRCALPHA)
            pygame.draw.ellipse(sq, (255, 255, 255, 255), (0, 0, 14, 12))
            surf.blit(sq, (ex - 7, ey - 3))
        return

    # Blink
    if s == "idle" and (t_ms % 3000) < 100:
        for ex in (ex_l, ex_r):
            pygame.draw.rect(surf, (255, 255, 255), (ex - 5, ey - 1, 10, 3))
        return

    # Eye dimensions per state
    if is_jump:
        ew, eh = 11, 14
    elif is_fast:
        ew, eh = 12, 7
    elif is_run:
        ew, eh = 12, 9
    else:
        ew, eh = 10, 12

    # Pupil offsets
    if is_jump:
        pdx, pdy = 0, -3
    elif is_fall:
        pdx, pdy = 0, 3
    elif is_fast or is_run:
        pdx, pdy = f * 4, 0
    elif s == "idle":
        pdx = int(math.sin(t_ms * 0.002) * 1.5)
        pdy = 0
    else:
        pdx, pdy = 0, 0

    for ex in (ex_l, ex_r):
        pygame.draw.ellipse(surf, (255, 255, 255),
                            (ex - ew // 2, ey - eh // 2, ew, eh))
        pygame.draw.ellipse(surf, C_OUTLINE,
                            (ex - ew // 2, ey - eh // 2, ew, eh), 2)
        pygame.draw.circle(surf, C_IRIS,  (ex + pdx, ey + pdy), 5)
        pygame.draw.circle(surf, C_PUPIL, (ex + pdx, ey + pdy), 3)
        pygame.draw.circle(surf, (255, 255, 255), (ex + pdx + 2, ey + pdy - 2), 2)
        pygame.draw.circle(surf, (255, 255, 255), (ex + pdx + 3, ey + pdy + 1), 1)
        # Eyelash arc above eye
        el_rect = pygame.Rect(ex - ew // 2 - 1, ey - eh // 2 - 5, ew + 2, 8)
        pygame.draw.arc(surf, C_OUTLINE, el_rect,
                        math.radians(30), math.radians(150), 2)


# ── Star tips ─────────────────────────────────────────────────────────────────

def _draw_star_tips(surf: pygame.Surface,
                    cx: int, cy: int, hh: int,
                    f: int,
                    is_jump: bool, is_running: bool,
                    is_fast: bool, is_landing: bool,
                    land_squash: int) -> None:
    """Two pointed star-tip ears at the crown of the head."""
    for side in (-1, 1):
        tx = cx + side * 7

        if is_landing and land_squash > 0:
            # Flatten sideways during squash
            pts = [
                (tx - side * 2, cy - hh),
                (tx + side * 5, cy - hh - 2),
                (tx - side * 2, cy - hh - 4),
            ]
        elif is_fast:
            # Fully flat, streaming back
            pts = [
                (tx,          cy - hh),
                (tx - f * 6,  cy - hh - 2),
                (tx,          cy - hh - 4),
            ]
        elif is_running:
            # Tilted back ~30 degrees
            pts = [
                (tx,          cy - hh),
                (tx - f * 3,  cy - hh - 8),
                (tx - f * 1,  cy - hh),
            ]
        elif is_jump:
            # Pointing straight up (excited)
            pts = [
                (tx - 2, cy - hh),
                (tx,     cy - hh - 9),
                (tx + 2, cy - hh),
            ]
        else:
            # Normal
            pts = [
                (tx - 2, cy - hh),
                (tx,     cy - hh - 8),
                (tx + 2, cy - hh),
            ]

        pygame.draw.polygon(surf, C_BODY, pts)
        pygame.draw.polygon(surf, C_OUTLINE, pts, 2)


# ── Expression ────────────────────────────────────────────────────────────────

def _draw_expression(surf: pygame.Surface,
                     cx: int, cy: int,
                     hh: int,
                     f: int, s: str,
                     vy: float,
                     is_jump: bool, is_fall: bool,
                     is_landing: bool,
                     is_running: bool, is_fast: bool,
                     t_ms: int) -> None:
    """Mouth, brows, and landing blush."""
    mouth_y = cy + hh - 4

    if is_landing:
        bk = pygame.Surface((40, 16), pygame.SRCALPHA)
        pygame.draw.circle(bk, (*C_BLUSH, 100), ( 7, 8), 6)
        pygame.draw.circle(bk, (*C_BLUSH, 100), (33, 8), 6)
        surf.blit(bk, (cx - 20, cy + 2))
        return

    if is_running or is_fast:
        pygame.draw.line(surf, C_OUTLINE,
                         (cx - 4, mouth_y), (cx + 4, mouth_y), 2)
        return

    if is_fall:
        frown_r = pygame.Rect(cx - 5, mouth_y - 2, 10, 7)
        pygame.draw.arc(surf, C_OUTLINE, frown_r, math.pi, 2 * math.pi, 2)
        for side in (-1, 1):
            bx  = cx + side * 6
            bry = cy - 4
            pygame.draw.line(surf, C_OUTLINE,
                             (bx, bry - 2), (bx - side * 4, bry + 1), 2)
        return

    if is_jump:
        for side in (-1, 1):
            bx  = cx + side * 6
            bry = cy - 5
            pygame.draw.line(surf, C_OUTLINE,
                             (bx - 3, bry + 2), (bx + 3, bry - 2), 2)
        return

    # Idle gentle smile
    smile_r = pygame.Rect(cx - 5, mouth_y - 3, 10, 7)
    pygame.draw.arc(surf, C_OUTLINE, smile_r,
                    math.pi + 0.3, 2 * math.pi - 0.3, 2)


# ── Speed lines ───────────────────────────────────────────────────────────────

def _draw_speed_lines(surf: pygame.Surface,
                      cx: int, cy: int, hh: int,
                      f: int,
                      player_color: tuple,
                      t_ms: int) -> None:
    """Four horizontal speed lines trailing behind at full speed."""
    line_len = 35
    char_top = cy - hh - 5
    char_h   = hh * 2 + 18   # head + body + legs height span

    sp_w = line_len + 10
    sp_h = char_h + 10
    sp   = pygame.Surface((sp_w, sp_h), pygame.SRCALPHA)

    for i in range(4):
        ly  = int((i + 0.5) * char_h / 4) + 5
        seg = line_len // 3
        for alpha, width, x0, x1 in (
            (100, 2, sp_w - seg,     sp_w),
            ( 60, 1, sp_w - seg * 2, sp_w - seg),
            ( 25, 1, 0,              sp_w - seg * 2),
        ):
            pygame.draw.line(sp, (*player_color, alpha),
                             (x0, ly), (x1, ly), width)

    if f == 1:
        surf.blit(sp, (cx - hh - sp_w, char_top - 5))
    else:
        surf.blit(pygame.transform.flip(sp, True, False),
                  (cx + hh, char_top - 5))


# ── Scarf trailing tail ───────────────────────────────────────────────────────

def _draw_scarf_tail(surf: pygame.Surface,
                     cx: int, neck_y: int,
                     pos_history: list,
                     player_color: tuple,
                     cam_x: int,
                     is_jump: bool) -> None:
    """Draw the scarf trailing through recent pos_history positions."""
    if not pos_history:
        return

    tail_pts = [(cx, neck_y)]
    for hx, hy in list(pos_history)[:5]:
        rx = int(hx) - cam_x + 12
        # neck_y equivalent for that historical position
        ry = int(hy) + 44 - 8 - 10 - 13 + 13
        tail_pts.append((rx, ry))

    if len(tail_pts) < 2:
        return

    sc = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
    for i in range(len(tail_pts) - 1):
        alpha = max(20, 200 - i * 36)
        width = max(1, 4 - i)
        pygame.draw.line(sc, (*player_color, alpha),
                         tail_pts[i], tail_pts[i + 1], width)
    surf.blit(sc, (0, 0))


# ── Core Star Kid draw ────────────────────────────────────────────────────────

def _draw_star_kid(surf: pygame.Surface,
                   cx: int, head_cy: int,
                   f: int, s: str,
                   fr: int, vx: float, vy: float,
                   land_squash: int,
                   player_color: tuple,
                   t_ms: int) -> None:
    """
    Draw Star Kid in draw-order layers. cx/head_cy is the un-bobbed head centre.
    """
    speed      = abs(vx)
    is_jump    = (s == "jump" or vy < -3)
    is_fall    = (s == "fall" or vy > 4)
    is_running = speed > 2 and not is_jump and not is_fall
    is_fast    = speed > 6 and not is_jump and not is_fall
    is_landing = land_squash > 0

    # Squash / stretch
    if is_landing:
        t_sq   = land_squash / 6.0
        head_w = 13 + int(t_sq * 4)
        head_h = 13 - int(t_sq * 3)
        leg_h  = max(4, 8 - int(t_sq * 4))
    else:
        head_w = head_h = 13
        leg_h  = 8

    # Idle bob (2 px)
    bob = int(math.sin(t_ms * 0.003) * 2) if s == "idle" else 0

    # Running lean: shift head forward
    hcx = cx + (f * 3 if is_running else 0)
    hcy = head_cy + bob

    body_top    = hcy + head_h - 2   # slight overlap with head bottom
    body_bottom = body_top + 10

    # ── 1. Shadow ──────────────────────────────────────────────────────────
    sh_w = 26 if is_landing else 20
    sh_h = 3  if is_landing else 5
    sh_s = pygame.Surface((sh_w + 2, sh_h + 2), pygame.SRCALPHA)
    pygame.draw.ellipse(sh_s, (10, 4, 16, 50), (0, 0, sh_w, sh_h))
    surf.blit(sh_s, (hcx - sh_w // 2, body_bottom + leg_h - 1))

    # ── 2. Body ────────────────────────────────────────────────────────────
    bx = hcx - 7
    pygame.draw.rect(surf, C_BODY,    (bx, body_top, 14, 10), border_radius=3)
    pygame.draw.rect(surf, C_OUTLINE, (bx, body_top, 14, 10), 2, border_radius=3)

    # ── 3. Legs + feet ─────────────────────────────────────────────────────
    walk_frame = (fr // 4) % 2

    for side in (-1, 1):
        leg_cx = hcx + side * 4

        if is_jump:
            lx = leg_cx + side * 3
            ly = body_bottom - 5
        elif is_fall:
            lx = leg_cx
            ly = body_bottom + 4
        elif is_landing:
            lx = leg_cx
            ly = body_bottom
        elif is_running:
            forward = (side == 1 and walk_frame == 0) or (side == -1 and walk_frame == 1)
            lx = leg_cx + (f * 3 if forward else -f * 1)
            ly = body_bottom - (2 if forward else 0)
        else:
            lx = leg_cx
            ly = body_bottom

        pygame.draw.rect(surf, C_LEGS,
                         (lx - 3, ly, 6, leg_h), border_radius=3)
        pygame.draw.rect(surf, C_OUTLINE,
                         (lx - 3, ly, 6, leg_h), 2, border_radius=3)
        pygame.draw.ellipse(surf, C_FEET, (lx - 4, ly + leg_h - 2, 8, 4))

    # ── 4. Head ────────────────────────────────────────────────────────────
    pygame.draw.ellipse(surf, C_BODY,
                        (hcx - head_w, hcy - head_h, head_w * 2, head_h * 2))

    # Shading crescent: darker half-ellipse on left of head
    sh = pygame.Surface((head_w * 2, head_h * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (*C_SHADE, 80),
                        (0, head_h // 2, head_w, head_h))
    surf.blit(sh, (hcx - head_w, hcy - head_h))

    pygame.draw.ellipse(surf, C_OUTLINE,
                        (hcx - head_w, hcy - head_h, head_w * 2, head_h * 2), 2)

    # ── 5. Scarf neck wrap ─────────────────────────────────────────────────
    scarf_y = hcy + head_h - 3
    sc_s = pygame.Surface((20, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(sc_s, (*player_color, 255), (0, 0, 20, 8))
    pygame.draw.ellipse(sc_s, (*C_OUTLINE, 255),    (0, 0, 20, 8), 2)
    surf.blit(sc_s, (hcx - 10, scarf_y))

    # ── 6. Eyes ────────────────────────────────────────────────────────────
    _draw_star_eyes(surf, hcx, hcy, head_w, head_h,
                    f, s, vy, land_squash, t_ms, speed)

    # ── 7. Star tips ───────────────────────────────────────────────────────
    _draw_star_tips(surf, hcx, hcy, head_h,
                    f, is_jump, is_running, is_fast, is_landing, land_squash)

    # ── 8. Expression ──────────────────────────────────────────────────────
    _draw_expression(surf, hcx, hcy, head_h,
                     f, s, vy,
                     is_jump, is_fall, is_landing,
                     is_running, is_fast, t_ms)

    # ── 9. Arm nubs (running / jumping) ────────────────────────────────────
    if is_running or is_jump:
        arm_y = hcy + head_h + 2
        if is_jump:
            for side in (-1, 1):
                ax = hcx + side * (head_w + 2)
                pygame.draw.rect(surf, C_BODY,
                                 (ax - 2, arm_y, 5, 4), border_radius=2)
                pygame.draw.rect(surf, C_OUTLINE,
                                 (ax - 2, arm_y, 5, 4), 1, border_radius=2)
        else:
            ax_fwd  = hcx + f * (head_w + 2)
            ax_back = hcx - f * (head_w + 1)
            for ax, dy in ((ax_fwd, -1), (ax_back, 1)):
                pygame.draw.rect(surf, C_BODY,
                                 (ax - 2, arm_y + dy, 5, 4), border_radius=2)
                pygame.draw.rect(surf, C_OUTLINE,
                                 (ax - 2, arm_y + dy, 5, 4), 1, border_radius=2)

    # ── 10. Speed lines ────────────────────────────────────────────────────
    if is_fast:
        _draw_speed_lines(surf, hcx, hcy, head_h, f, player_color, t_ms)


# ── Rolling renderer ───────────────────────────────────────────────────────────

def _draw_rolling(surf: pygame.Surface,
                  world_x: int, py: int,
                  cam_x: int,
                  player_color: tuple,
                  t_ms: int) -> None:
    """
    Render Star Kid spinning during a roll.
    Draws to a 64×64 offscreen surface then rotates and blits.
    """
    size = 64
    cx = size // 2
    cy = size // 2 - 4
    tmp = pygame.Surface((size, size), pygame.SRCALPHA)

    # Head
    pygame.draw.circle(tmp, C_BODY, (cx, cy), 13)
    sh = pygame.Surface((26, 26), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (*C_SHADE, 80), (0, 6, 13, 13))
    tmp.blit(sh, (cx - 13, cy - 13))
    pygame.draw.circle(tmp, C_OUTLINE, (cx, cy), 13, 2)

    # Body
    pygame.draw.rect(tmp, C_BODY,    (cx - 7, cy + 11, 14, 10), border_radius=3)
    pygame.draw.rect(tmp, C_OUTLINE, (cx - 7, cy + 11, 14, 10), 2, border_radius=3)

    # Legs
    for side in (-1, 1):
        lx = cx + side * 4
        pygame.draw.rect(tmp, C_LEGS,
                         (lx - 3, cy + 21, 6, 8), border_radius=3)
        pygame.draw.rect(tmp, C_OUTLINE,
                         (lx - 3, cy + 21, 6, 8), 2, border_radius=3)
        pygame.draw.ellipse(tmp, C_FEET, (lx - 4, cy + 27, 8, 4))

    # Scarf
    sc_s = pygame.Surface((20, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(sc_s, (*player_color, 255), (0, 0, 20, 8))
    pygame.draw.ellipse(sc_s, (*C_OUTLINE, 255),    (0, 0, 20, 8), 2)
    tmp.blit(sc_s, (cx - 10, cy + 10))

    # Swirl eyes (approximated by two concentric circles)
    for ex in (cx - 6, cx + 6):
        ey = cy - 2
        pygame.draw.circle(tmp, C_OUTLINE, (ex, ey), 4, 2)
        pygame.draw.circle(tmp, C_OUTLINE, (ex, ey), 2, 1)

    # Star tips (rotate with body — draw upright, rotation handles angle)
    for side in (-1, 1):
        tx = cx + side * 7
        pts = [(tx - 2, cy - 13), (tx, cy - 21), (tx + 2, cy - 13)]
        pygame.draw.polygon(tmp, C_BODY, pts)
        pygame.draw.polygon(tmp, C_OUTLINE, pts, 2)

    angle   = (t_ms // 4) % 360
    rotated = pygame.transform.rotate(tmp, -angle)
    rw, rh  = rotated.get_size()

    draw_x = world_x - cam_x + 12 - rw // 2
    draw_y = py + 8 - rh // 2
    surf.blit(rotated, (draw_x, draw_y))


# ── Preview (character select screen) ────────────────────────────────────────

def draw_star_kid_preview(surf: pygame.Surface,
                          cx: int, cy: int,
                          color: tuple,
                          scale: float = 1.0,
                          anim: int = 0) -> None:
    """Draw a static, scaled Star Kid centred at (cx, cy). Used on select screen."""
    r  = max(4, int(13 * scale))
    bw = max(6, int(14 * scale))
    bh = max(4, int(10 * scale))
    lg = max(3, int(8  * scale))

    head_cy  = cy - bh - lg + r
    body_top = head_cy + r - 2

    # Head
    pygame.draw.circle(surf, C_BODY,    (cx, head_cy), r)
    pygame.draw.circle(surf, C_OUTLINE, (cx, head_cy), r, 2)

    # Body
    pygame.draw.rect(surf, C_BODY,
                     (cx - bw // 2, body_top, bw, bh), border_radius=3)
    pygame.draw.rect(surf, C_OUTLINE,
                     (cx - bw // 2, body_top, bw, bh), 2, border_radius=3)

    # Legs + feet
    for side in (-1, 1):
        lx = cx + side * int(4 * scale)
        pygame.draw.rect(surf, C_LEGS,
                         (lx - int(3 * scale), body_top + bh,
                          int(6 * scale), lg), border_radius=2)
        pygame.draw.rect(surf, C_OUTLINE,
                         (lx - int(3 * scale), body_top + bh,
                          int(6 * scale), lg), 2, border_radius=2)
        pygame.draw.ellipse(surf, C_FEET,
                            (lx - int(4 * scale), body_top + bh + lg - int(2 * scale),
                             int(8 * scale), int(4 * scale)))

    # Scarf
    sc_s = pygame.Surface((int(20 * scale) + 2, 12), pygame.SRCALPHA)
    sw   = int(20 * scale)
    sh_  = int(8  * scale)
    pygame.draw.ellipse(sc_s, (*color, 255),    (0, 0, sw, sh_))
    pygame.draw.ellipse(sc_s, (*C_OUTLINE, 255), (0, 0, sw, sh_), 2)
    surf.blit(sc_s, (cx - sw // 2, head_cy + r - int(3 * scale)))

    # Eyes
    for ex in (cx - int(6 * scale), cx + int(6 * scale)):
        ey = head_cy - int(2 * scale)
        ew = max(4, int(10 * scale))
        eh = max(5, int(12 * scale))
        pygame.draw.ellipse(surf, (255, 255, 255),
                            (ex - ew // 2, ey - eh // 2, ew, eh))
        pygame.draw.ellipse(surf, C_OUTLINE,
                            (ex - ew // 2, ey - eh // 2, ew, eh), 2)
        pygame.draw.circle(surf, C_IRIS,  (ex, ey), max(3, int(5 * scale)))
        pygame.draw.circle(surf, C_PUPIL, (ex, ey), max(2, int(3 * scale)))
        gr = max(1, int(2 * scale))
        pygame.draw.circle(surf, (255, 255, 255), (ex + gr, ey - gr), gr)

    # Star tips
    for side in (-1, 1):
        tx = cx + side * int(7 * scale)
        th = int(8 * scale)
        pts = [
            (tx - int(2 * scale), head_cy - r),
            (tx,                  head_cy - r - th),
            (tx + int(2 * scale), head_cy - r),
        ]
        pygame.draw.polygon(surf, C_BODY, pts)
        pygame.draw.polygon(surf, C_OUTLINE, pts, 2)

    # Idle smile
    smile_r = pygame.Rect(cx - int(5 * scale),
                          head_cy + r - int(6 * scale),
                          int(10 * scale), int(7 * scale))
    pygame.draw.arc(surf, C_OUTLINE, smile_r,
                    math.pi + 0.3, 2 * math.pi - 0.3, 2)


# ── Main entry point ──────────────────────────────────────────────────────────

def draw_fancy_player(surf: pygame.Surface,
                      player: object,
                      cam_x: int) -> None:
    """
    Render the player as Star Kid — a small celestial creature with a flowing scarf.
    Called every frame by Player.draw(surf, cam_x) in main.py.
    """
    px = int(player.x) - cam_x    # type: ignore[attr-defined]
    py = int(player.y)             # type: ignore[attr-defined]
    f  = player.facing             # type: ignore[attr-defined]
    s  = player.state              # type: ignore[attr-defined]
    fr = player.anim_frame         # type: ignore[attr-defined]
    vx = player.vx                 # type: ignore[attr-defined]
    vy = player.vy                 # type: ignore[attr-defined]

    land_squash  = getattr(player, 'land_squash',  0)
    pos_history  = getattr(player, 'pos_history',  [])
    player_color = getattr(player, 'color',        (180, 100, 220))
    t_ms         = pygame.time.get_ticks()

    # Rolling: separate rotated-surface renderer
    if s == "roll":
        _draw_rolling(surf, int(player.x), py, cam_x, player_color, t_ms)
        return

    # Head centre: px/py is sprite top-left; character is 24px wide, 44px tall
    # Layout from feet up: legs(8) + body(10) + head_radius(13) = 31px
    cx      = px + 12
    feet_y  = py + 44
    head_cy = feet_y - 8 - 10 - 13   # un-bobbed head centre y
    neck_y  = head_cy + 13            # bottom of head circle = scarf neck

    # Scarf trailing tail — drawn behind everything
    is_jump = (s == "jump" or vy < -3)
    _draw_scarf_tail(surf, cx, neck_y, pos_history, player_color, cam_x, is_jump)

    # Character
    _draw_star_kid(surf, cx, head_cy,
                   f, s, fr, vx, vy,
                   land_squash, player_color, t_ms)
