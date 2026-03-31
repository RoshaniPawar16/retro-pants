"""retro-pants  —  arcade platformer with CRT visual treatment."""

import pygame
import sys
import math
import random
from draw_player import draw_fancy_player, draw_star_kid_preview as draw_ghost_preview

# ── Display ──────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 960, 540
FPS           = 60
TILE          = 32

# ── Palette ───────────────────────────────────────────────────────────────────
COL_BG            = ( 13,   8,  32)   # #0D0820 — Sea of Stars deep sky
COL_GROUND        = ( 27,  16,  64)   # kept for compat (now unused in drawing)
COL_GROUND_EDGE   = (233,  69,  96)   # kept for compat
COL_PLATFORM      = ( 45,  27, 105)   # kept for compat
COL_PLATFORM_DARK = ( 27,  16,  64)   # kept for compat
COL_BODY          = (240, 232, 210)   # warm cream
COL_OUTLINE       = ( 10,  10,  10)
COL_SCARF         = (255, 107, 107)   # #FF6B6B
COL_STAR_W        = (255, 255, 255)
COL_STAR_B        = (170, 170, 255)
COL_STAR_R        = (255, 107, 107)
COL_HUD_LABEL     = (233,  69,  96)
COL_HUD_VALUE     = (255, 255, 255)
COL_TITLE_SHADOW  = (233,  69,  96)

# ── Sea of Stars tile palette ─────────────────────────────────────────────────
COL_G_BASE = ( 27,  16,  64)   # #1B1040 deep indigo base
COL_G_CAP  = ( 78, 205, 196)   # #4ECDC4 teal lit edge
COL_G_MID  = ( 45,  27, 105)   # #2D1B69 second layer
COL_G_DARK = ( 13,   8,  32)   # #0D0820 side shadow
COL_G_BOT  = ( 10,   6,  24)   # #0A0618 bottom edge
COL_P_CAP  = (255, 209, 102)   # #FFD166 amber platform highlight
COL_P_MID  = ( 45,  27, 105)   # #2D1B69
COL_P_BASE = ( 27,  16,  64)   # #1B1040

# ── Ghost options (character select) ──────────────────────────────────────────
GHOST_OPTIONS = [
    {"color": (255,  51,  51), "name": "BLINKY"},
    {"color": (255, 130, 190), "name": "PINKY"},
    {"color": (  0, 207, 207), "name": "INKY"},
    {"color": (255, 184,  71), "name": "CLYDE"},
    {"color": ( 80, 110, 255), "name": "SUE"},
    {"color": (160,  55, 220), "name": "SPECTER"},
]

# ── Physics (UNCHANGED) ───────────────────────────────────────────────────────
ACCEL         = 0.9
FRICTION      = 0.80
AIR_FRICTION  = 0.92
MAX_SPEED     = 9.0
JUMP_FORCE    = -15.0
GRAVITY       = 0.65
MAX_FALL      = 18.0
COYOTE_FRAMES = 10
JUMP_BUFFER   = 8
ROLL_SPEED    = 12.0

# ── Particle constants ────────────────────────────────────────────────────────
DUST_SPEED_THRESHOLD = 4.0
DUST_PER_FRAME_MAX   = 2
DUST_LIFE_MIN        = 15
DUST_LIFE_MAX        = 25
IMPACT_VY_THRESHOLD  = 6.0
SHAKE_VY_THRESHOLD   = 8.0
SHAKE_FRAMES         = 8
SHAKE_MAGNITUDE      = 5

# ── Scarf trail length ────────────────────────────────────────────────────────
SCARF_HISTORY = 5

# ── Level map (100 columns, 6 sections) ──────────────────────────────────────
# 0=air  G=solid ground  P=pass-through platform
# Section 1 (cols 0-32):  warmup — solid ground, gentle hops
# Section 2 (cols 33-40): speed corridor + 4-tile gap (cols 33-36)
# Section 3 (cols 41-54): ascending platform chain — no floor, 3 P steps
# Section 4 (cols 55-63): 7-tile big gap (cols 57-63) + P safety net at row 12
# Section 5 (cols 64-84): rhythm gaps — 3 small pits with landings
# Section 6 (cols 85-99): victory stretch — open solid run
_g = "G" * 33 + " " * 4 + "G" * 4 + " " * 14 + "G" * 2 + " " * 7 + "G" * 6 + " " * 3 + "G" * 3 + " " * 3 + "G" * 3 + " " * 3 + "G" * 15
LEVEL = [
    " " * 100,                                                                    # 0  sky
    " " * 100,                                                                    # 1
    " " * 100,                                                                    # 2
    " " * 52 + "P" + " " * 47,                                                   # 3  scattered decorative platforms
    " " * 20 + "P" + " " * 44 + "P" + " " * 34,                                 # 4
    " " * 35 + "P" + " " * 36 + "P" + " " * 27,                                 # 5
    " " * 15 + "P" + " " * 34 + "P" + " " * 49,                                 # 6
    " " * 62 + "P" + " " * 17 + "P" + " " * 19,                                 # 7
    " " * 27 + "PPP" + " " * 70,                                                 # 8
    " " * 8  + "PPP" + " " * 79 + "PPP" + " " * 7,                              # 9  high hops s1 + s6
    " " * 4  + "PPP" + " " * 15 + "PPP" + " " * 75,                             # 10 s1 low hops
    " " * 10 + "PPP" + " " * 38 + "PPP" + " " * 46,                             # 11 s1 high + s3 top step
    " " * 46 + "PPP" + " " * 10 + "PPP" + " " * 9  + "PPP" + " " * 26,         # 12 s3 mid + s4 safety net + s5 optional
    " " * 7  + "PPP" + " " * 8  + "PPP" + " " * 21 + "PPP" + " " * 55,         # 13 s1 near-floor + s3 bottom step
    _g,                                                                           # 14 main ground with gaps
    _g,                                                                           # 15
    _g,                                                                           # 16
]

# ── Coin positions (pixel x, pixel y) aligned to new 100-col level ────────────
_T = TILE
COIN_POSITIONS: list[tuple[float, float]] = [
    # Section 1 — warmup ground run (6 coins)
    ( 1*_T+16, 14*_T-30),  # early ground
    ( 8*_T+16, 13*_T-25),  # above row-13 platform at col 8
    (14*_T+16, 14*_T-30),  # mid section 1
    (19*_T+16, 13*_T-25),  # above row-13 platform at col 19
    (25*_T+16, 14*_T-30),  # late section 1
    ( 9*_T+16,  9*_T-30),  # high reward above row-9 platform (col 9)
    # Section 2 — floating over 4-tile gap (2 coins)
    (33*_T+16, 14*_T-58),  # edge of gap
    (35*_T+16, 14*_T-93),  # mid-air peak (requires arc jump)
    # Section 3 — ascending platform chain (3 coins)
    (43*_T+16, 13*_T-25),  # above step 1 (row 13)
    (47*_T+16, 12*_T-25),  # above step 2 (row 12)
    (52*_T+16, 11*_T-25),  # above step 3 (row 11) — highest
    # Section 4 — big gap + safety net (2 coins)
    (59*_T+16, 14*_T-58),  # floating in gap
    (60*_T+16, 12*_T-25),  # above safety-net platform
    # Section 5 — rhythm gaps (6 coins)
    (71*_T+16, 14*_T-58),  # over gap 1
    (72*_T+16, 12*_T-25),  # above optional platform (row 12)
    (74*_T+16, 14*_T-30),  # landing after gap 1
    (77*_T+16, 14*_T-58),  # over gap 2
    (80*_T+16, 14*_T-30),  # landing after gap 2
    (83*_T+16, 14*_T-58),  # over gap 3
    # Section 6 — victory stretch (6 coins)
    (87*_T+16, 14*_T-30),
    (89*_T+16, 14*_T-30),
    (91*_T+16, 14*_T-30),
    (93*_T+16, 14*_T-30),
    (95*_T+16, 14*_T-30),
    (97*_T+16, 14*_T-30),
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def build_tiles(level: list[str]) -> list[tuple[pygame.Rect, bool]]:
    """Return list of (rect, solid) from level string array."""
    tiles = []
    for row_i, row in enumerate(level):
        for col_i, ch in enumerate(row):
            rect = pygame.Rect(col_i * TILE, row_i * TILE, TILE, TILE)
            if ch == 'G':
                tiles.append((rect, True))
            elif ch == 'P':
                tiles.append((rect, False))
    return tiles


def lerp_color(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ── Stars ─────────────────────────────────────────────────────────────────────
random.seed(42)

_star_colors = [COL_STAR_W, COL_STAR_B, COL_STAR_R]
STARS: list[dict] = []
for _ in range(140):
    STARS.append({
        "x":        random.randint(0, 4000),
        "y":        random.randint(0, HEIGHT // 2),
        "size":     random.choice([1, 1, 2, 2, 3]),
        "color":    random.choice(_star_colors),
        "period":   random.randint(40, 80),
        "phase":    random.randint(0, 79),
    })


def draw_stars(surf: pygame.Surface, cam_x: int, frame: int) -> None:
    """Draw twinkling stars with parallax."""
    for s in STARS:
        rx = int((s["x"] - cam_x * 0.15)) % WIDTH
        alpha_t = 0.5 + 0.5 * math.sin(
            2 * math.pi * (frame + s["phase"]) / s["period"]
        )
        brightness = int(180 + 75 * alpha_t)
        base = s["color"]
        col = (
            min(255, int(base[0] * brightness / 255)),
            min(255, int(base[1] * brightness / 255)),
            min(255, int(base[2] * brightness / 255)),
        )
        pygame.draw.circle(surf, col, (rx, s["y"]), s["size"])


# ── Tile surfaces (pre-rendered at startup, filled by _build_tile_surfaces) ───
_TILE_G_CAP:   "pygame.Surface | None" = None  # 32×32 ground with teal top cap
_TILE_G_FILL:  "pygame.Surface | None" = None  # 32×32 ground inner (no cap)
_TILE_P_BASE:  "pygame.Surface | None" = None  # 32×10 platform base (no amber)
_TILE_SHADOW4: "pygame.Surface | None" = None  # 32×4  SRCALPHA drop shadow
_TILE_SHADOW3: "pygame.Surface | None" = None  # 32×3  SRCALPHA drop shadow
_TILE_GLOW_G:  "pygame.Surface | None" = None  # 32×12 SRCALPHA ground bloom
_TILE_GLOW_P:  "pygame.Surface | None" = None  # 36×14 SRCALPHA platform bloom


def _build_tile_surfaces() -> None:
    """Pre-render all tile face and glow surfaces. Call once after pygame.init()."""
    global _TILE_G_CAP, _TILE_G_FILL, _TILE_P_BASE
    global _TILE_SHADOW4, _TILE_SHADOW3, _TILE_GLOW_G, _TILE_GLOW_P

    def _ground(cap: bool) -> pygame.Surface:
        s = pygame.Surface((TILE, TILE))
        s.fill(COL_G_BASE)
        if cap:
            pygame.draw.rect(s, COL_G_CAP, (0, 0, TILE, 5))          # teal highlight
            pygame.draw.rect(s, COL_G_MID, (0, 5, TILE, 4))          # mid purple
        return s

    _TILE_G_CAP  = _ground(True)
    _TILE_G_FILL = _ground(False)

    # Platform base: mid purple + dark base, amber cap drawn per-frame for pulse
    _TILE_P_BASE = pygame.Surface((TILE, 10))
    _TILE_P_BASE.fill(COL_P_MID)
    pygame.draw.rect(_TILE_P_BASE, COL_P_BASE, (0, 7, TILE, 3))

    # SRCALPHA drop shadows (blit below tile)
    _TILE_SHADOW4 = pygame.Surface((TILE, 4), pygame.SRCALPHA)
    _TILE_SHADOW4.fill((*COL_G_BOT, 120))
    _TILE_SHADOW3 = pygame.Surface((TILE, 3), pygame.SRCALPHA)
    _TILE_SHADOW3.fill((*COL_G_BOT, 100))

    # SRCALPHA bloom glows
    _TILE_GLOW_G = pygame.Surface((TILE, 12), pygame.SRCALPHA)
    _TILE_GLOW_G.fill((*COL_G_CAP, 15))
    _TILE_GLOW_P = pygame.Surface((TILE + 4, 14), pygame.SRCALPHA)
    _TILE_GLOW_P.fill((*COL_P_CAP, 30))


# ── Tile drawing ──────────────────────────────────────────────────────────────
def draw_tiles(surf: pygame.Surface, tiles: list, cam_x: int, cam_y: int,
               t_ms: int = 0, shimmer: "dict | None" = None) -> None:
    """Draw ground and platform tiles — Sea of Stars layered style."""
    for rect, solid in tiles:
        rx = rect.x - cam_x
        ry = rect.y - cam_y
        if rx > WIDTH + TILE or rx + TILE < 0:
            continue

        if solid:
            row_i = rect.y // TILE
            col_i = rect.x // TILE
            # Air-above check: only expose teal cap on tiles with open sky above
            air_above = (
                row_i == 0
                or col_i >= len(LEVEL[row_i - 1])
                or LEVEL[row_i - 1][col_i] == " "
            )

            # Upward teal bloom (ground luminescence)
            if air_above and _TILE_GLOW_G is not None:
                surf.blit(_TILE_GLOW_G, (rx, ry - 12))

            # Drop shadow below tile
            if _TILE_SHADOW4 is not None:
                surf.blit(_TILE_SHADOW4, (rx, ry + TILE))

            # Tile face
            face = _TILE_G_CAP if (air_above and _TILE_G_CAP) else _TILE_G_FILL
            if face is not None:
                surf.blit(face, (rx, ry))

            # Shimmer flash: briefly whiten the teal cap on a random tile
            if (air_above and shimmer and shimmer["timer"] > 0
                    and shimmer["col"] == col_i and shimmer["row"] == row_i):
                t = shimmer["timer"] / 6.0
                scol = (
                    int(COL_G_CAP[0] + (255 - COL_G_CAP[0]) * t),
                    int(COL_G_CAP[1] + (255 - COL_G_CAP[1]) * t),
                    int(COL_G_CAP[2] + (255 - COL_G_CAP[2]) * t),
                )
                pygame.draw.rect(surf, scol, (rx, ry, TILE, 5))

        else:
            # Pass-through platform — thin 10px visual at tile_top + 4
            ry_vis = ry + 4

            # Amber bloom below platform
            if _TILE_GLOW_P is not None:
                surf.blit(_TILE_GLOW_P, (rx - 2, ry_vis + 7))

            # Drop shadow below
            if _TILE_SHADOW3 is not None:
                surf.blit(_TILE_SHADOW3, (rx, ry_vis + 10))

            # Platform base
            if _TILE_P_BASE is not None:
                surf.blit(_TILE_P_BASE, (rx, ry_vis))

            # Pulsed amber cap (sin-driven between dim and full bright)
            pulse_t   = 0.5 + 0.5 * math.sin(t_ms * 0.002 + rect.x * 0.1)
            pulse_amt = 180 + int(75 * pulse_t)
            pygame.draw.rect(surf,
                             (min(255, 255 * pulse_amt // 255),
                              min(255, 209 * pulse_amt // 255),
                              min(255, 102 * pulse_amt // 255)),
                             (rx, ry_vis, TILE, 3))


# ── Particle system ───────────────────────────────────────────────────────────
class ParticleSystem:
    """Manages dust and impact particles; no external assets."""

    _dust_colors = [COL_G_CAP, COL_G_CAP, COL_STAR_B]   # teal dust matches ground glow

    def __init__(self) -> None:
        self.particles: list[dict] = []

    def spawn_dust(self, px: float, py: float, facing: int) -> None:
        """Spawn 1-2 dust particles at player feet."""
        count = random.randint(1, DUST_PER_FRAME_MAX)
        for _ in range(count):
            life = random.randint(DUST_LIFE_MIN, DUST_LIFE_MAX)
            self.particles.append({
                "x":        px + random.uniform(-4, 4),
                "y":        py + random.uniform(-2, 2),
                "vx":       -facing * random.uniform(0.3, 1.2),
                "vy":       random.uniform(-0.8, -0.2),
                "life":     life,
                "max_life": life,
                "color":    random.choice(self._dust_colors),
                "size":     random.choice([2, 2, 3]),
            })

    def spawn_impact(self, px: float, py: float) -> None:
        """Burst of 8-12 particles in a downward semicircle on hard landing."""
        count = random.randint(8, 12)
        for i in range(count):
            angle = math.pi + (i / count) * math.pi   # semicircle downward
            speed = random.uniform(2.0, 5.0)
            life = random.randint(10, 15)
            sz = random.choice([3, 3, 4])
            self.particles.append({
                "x":        px,
                "y":        py,
                "vx":       math.cos(angle) * speed,
                "vy":       math.sin(angle) * speed,
                "life":     life,
                "max_life": life,
                "color":    random.choice(self._dust_colors),
                "size":     sz,
            })

    def update(self) -> None:
        """Advance all particles one frame; remove dead ones."""
        alive = []
        for p in self.particles:
            p["x"]    += p["vx"]
            p["y"]    += p["vy"]
            p["vy"]   += 0.05   # slight gravity on particles
            p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, surf: pygame.Surface, cam_x: int, cam_y: int) -> None:
        """Draw all live particles, fading alpha over lifetime."""
        for p in self.particles:
            t = p["life"] / p["max_life"]
            alpha = int(t * 220)
            rx = int(p["x"]) - cam_x
            ry = int(p["y"]) - cam_y
            sz = p["size"]
            col = p["color"]
            tmp = pygame.Surface((sz, sz), pygame.SRCALPHA)
            tmp.fill((*col, alpha))
            surf.blit(tmp, (rx - sz // 2, ry - sz // 2))

    def spawn_coin_collect(self, px: float, py: float) -> None:
        """Burst of 6 gold particles on coin pickup."""
        for i in range(6):
            angle = i * math.tau / 6
            speed = random.uniform(2.0, 4.0)
            life  = random.randint(15, 25)
            self.particles.append({
                "x": px, "y": py,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 1.0,
                "life": life, "max_life": life,
                "color": (255, 215, 0),
                "size": random.choice([3, 3, 4]),
            })


# ── Camera ────────────────────────────────────────────────────────────────────
class Camera:
    """Smooth-follow camera with screen-shake support."""

    def __init__(self) -> None:
        self.x: float = 0.0
        self.y: float = 0.0
        self._shake_frames: int = 0
        self._shake_mag: float = 0.0
        self.offset_x: int = 0
        self.offset_y: int = 0
        self.flash_timer: int = 0

    def trigger_shake(self, magnitude: float = SHAKE_MAGNITUDE,
                      frames: int = SHAKE_FRAMES) -> None:
        self._shake_frames = frames
        self._shake_mag    = magnitude

    def update(self, target_x: float) -> None:
        target = target_x - WIDTH // 3
        self.x += (target - self.x) * 0.12
        self.x = max(0.0, self.x)
        self.y = 0.0

        if self.flash_timer > 0:
            self.flash_timer -= 1

        if self._shake_frames > 0:
            decay = self._shake_frames / SHAKE_FRAMES
            mag   = self._shake_mag * decay
            self.offset_x = int(random.uniform(-mag, mag))
            self.offset_y = int(random.uniform(-mag, mag))
            self._shake_frames -= 1
        else:
            self.offset_x = 0
            self.offset_y = 0

    @property
    def cx(self) -> int:
        return int(self.x) + self.offset_x

    @property
    def cy(self) -> int:
        return int(self.y) + self.offset_y


# ── Coin ──────────────────────────────────────────────────────────────────────
class Coin:
    """Collectible coin: gold circle with bob + spin animation."""

    RADIUS    = 6
    _COL_GOLD  = (255, 215,   0)
    _COL_SHINE = (255, 240, 160)

    def __init__(self, x: float, y: float) -> None:
        self.x          = x
        self.y          = y
        self.collected  = False
        self.bob_offset = random.uniform(0, math.tau)
        self.spin_phase = random.uniform(0, math.tau)
        self._glow: "pygame.Surface | None" = None

    def update(self, player: "Player", particles: ParticleSystem) -> int:
        """Check collection. Returns 100 if just collected this frame, else 0."""
        if self.collected:
            return 0
        dx = abs((player.x + player.W / 2) - self.x)
        dy = abs((player.y + player.H / 2) - self.y)
        if dx < 10 and dy < 10:
            self.collected = True
            particles.spawn_coin_collect(self.x, self.y)
            return 100
        return 0

    def draw(self, surf: pygame.Surface, cam_x: int, cam_y: int,
             t_ms: int) -> None:
        if self.collected:
            return
        rx = int(self.x) - cam_x
        ry = int(self.y) - cam_y
        if rx < -20 or rx > WIDTH + 20:
            return

        r  = self.RADIUS
        by = ry + int(math.sin(t_ms * 0.003 + self.bob_offset) * 4)

        # Soft gold bloom
        if self._glow is None:
            self._glow = pygame.Surface((28, 28), pygame.SRCALPHA)
            pygame.draw.circle(self._glow, (255, 224, 102, 35), (14, 14), 14)
        surf.blit(self._glow, (rx - 14, by - 14))

        # Gold fill
        pygame.draw.circle(surf, self._COL_GOLD, (rx, by), r)

        # Spin overlay: horizontal ellipse cycling width 0→full→0
        spin_w = int(abs(math.sin(t_ms * math.pi / 500.0 + self.spin_phase)) * r * 2)
        if spin_w > 1:
            pygame.draw.ellipse(surf, self._COL_SHINE,
                                (rx - spin_w // 2, by - r // 2, spin_w, r))

        # Black outline
        pygame.draw.circle(surf, (0, 0, 0), (rx, by), r, 2)

        # Shine dot (top-left)
        pygame.draw.circle(surf, self._COL_SHINE, (rx - 2, by - 2), 3)


# ── Enemy ─────────────────────────────────────────────────────────────────────
class Enemy:
    """Patrolling spiky blob. Stomp from above for 200 pts; side contact respawns player."""

    RADIUS    = 10
    SPEED     = 1.5
    _COL_BODY = (180,  30,  30)
    _COL_DARK = ( 80,   0,   0)
    _COL_EYE  = (255, 255, 255)

    def __init__(self, x: float, y: float,
                 patrol_x1: float, patrol_x2: float) -> None:
        self.x         = x
        self.y         = y
        self.vx        = self.SPEED
        self.vy        = 0.0
        self.patrol_x1 = patrol_x1
        self.patrol_x2 = patrol_x2
        self.alive     = True
        self.facing    = 1
        self._glow: "pygame.Surface | None" = None

    @property
    def rect(self) -> pygame.Rect:
        r = self.RADIUS
        return pygame.Rect(int(self.x) - r, int(self.y) - r, r * 2, r * 2)

    def update(self, tiles: list) -> None:
        """Patrol + gravity + solid tile collision."""
        if not self.alive:
            return
        # Horizontal patrol
        self.x += self.vx
        if self.x <= self.patrol_x1:
            self.x = self.patrol_x1; self.vx = self.SPEED;  self.facing =  1
        elif self.x >= self.patrol_x2:
            self.x = self.patrol_x2; self.vx = -self.SPEED; self.facing = -1
        # Gravity
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.y += self.vy
        # Solid tile collision (vertical only — patrol keeps horizontal in bounds)
        r = self.rect
        for tile, solid in tiles:
            if solid and r.colliderect(tile):
                if self.vy >= 0:
                    self.y  = tile.top - self.RADIUS
                    self.vy = 0
                else:
                    self.y  = tile.bottom + self.RADIUS
                    self.vy = 0
                r = self.rect

    def check_player(self, player: "Player", particles: "ParticleSystem",
                     camera: "Camera", float_texts: list) -> int:
        """
        Collision with player. Returns score gained (200 for stomp, 0 otherwise).
        Mutates player.vy on stomp; respawns player + sets camera.flash_timer on hurt.
        """
        if not self.alive:
            return 0
        if not player.rect.colliderect(self.rect):
            return 0
        # Stomp: player falling, feet at or above enemy centre
        stomping = (
            player.vy > 2
            and player.rect.bottom <= self.y + self.RADIUS * 0.6
        )
        if stomping:
            self.alive = False
            player.vy  = -10.0
            particles.spawn_impact(self.x, self.y)
            float_texts.append({
                "x": self.x, "y": self.y - 20,
                "alpha": 255.0, "dy": -0.75, "text": "+200",
            })
            return 200
        # Side / under hit → respawn
        player.x, player.y   = 80.0, 100.0
        player.vx, player.vy = 0.0,  0.0
        camera.flash_timer    = 20
        return 0

    def draw(self, surf: pygame.Surface, cam_x: int, cam_y: int) -> None:
        if not self.alive:
            return
        rx = int(self.x) - cam_x
        ry = int(self.y) - cam_y
        if rx < -40 or rx > WIDTH + 40:
            return
        r  = self.RADIUS
        s  = 1.3   # draw 30% larger than hitbox
        sr = int(r * s)

        # Soft red bloom (scaled)
        br = int(22 * s)
        if self._glow is None:
            self._glow = pygame.Surface((br * 2, br * 2), pygame.SRCALPHA)
            pygame.draw.circle(self._glow, (204, 34, 0, 20), (br, br), br)
        surf.blit(self._glow, (rx - br, ry - br))

        # 8 spikes (scaled)
        spike_len = int((r + 6) * s)
        for i in range(8):
            ang  = i * math.pi / 4
            tip  = (int(rx + math.cos(ang) * spike_len),
                    int(ry + math.sin(ang) * spike_len))
            bl   = (int(rx + math.cos(ang - 0.3) * sr),
                    int(ry + math.sin(ang - 0.3) * sr))
            brp  = (int(rx + math.cos(ang + 0.3) * sr),
                    int(ry + math.sin(ang + 0.3) * sr))
            pygame.draw.polygon(surf, self._COL_DARK, [tip, bl, brp])

        # Body (scaled)
        pygame.draw.circle(surf, self._COL_BODY, (rx, ry), sr)
        pygame.draw.circle(surf, self._COL_DARK,  (rx, ry), sr, 2)

        # Angry eyes (scaled offsets)
        eo = int(4 * s)
        er = int(3 * s)
        for ex_off in (-eo, eo):
            pygame.draw.circle(surf, self._COL_EYE, (rx + ex_off, ry - int(2 * s)), er)
            pygame.draw.circle(surf, (0, 0, 0),      (rx + ex_off, ry - int(s)),    max(1, er - 2))

        # Angry brows (scaled)
        pygame.draw.line(surf, self._COL_DARK,
                         (rx - int(7 * s), ry - int(6 * s)),
                         (rx - int(2 * s), ry - int(4 * s)), 2)
        pygame.draw.line(surf, self._COL_DARK,
                         (rx + int(2 * s), ry - int(4 * s)),
                         (rx + int(7 * s), ry - int(6 * s)), 2)


# ── Parallax background ───────────────────────────────────────────────────────
class ParallaxBackground:
    """Sea of Stars night scene: mountains + spires, tree line, fog wisps, foreground hills."""

    # Palette
    _FAR   = ( 13,   8,  32)   # #0D0820
    _L1    = ( 17,  13,  46)   # #110D2E distant peaks
    _L2    = ( 26,  16,  64)   # #1A1040 front hills / moon base
    _L3    = ( 36,  21,  80)   # #241550 tree silhouette
    _L4    = ( 45,  27,  94)   # #2D1B5E fog / tree highlight
    _TEAL  = ( 78, 205, 196)   # #4ECDC4 bioluminescent accent
    _CORAL = (255, 107, 107)   # #FF6B6B moon tint

    def __init__(self) -> None:
        self._fog_offset: float = 0.0
        self._mtn_surf  = self._build_mountains()
        self._tree_surf = self._build_trees()
        self._fog       = self._build_fog()
        self._fore_pts  = self._build_fore_hills()
        self._moon_surf = self._build_moon()

    # ── Layer builders ──────────────────────────────────────────────────

    def _build_mountains(self) -> pygame.Surface:
        """3×WIDTH jagged peaks + castle spires (two hill passes)."""
        W3   = WIDTH * 3
        surf = pygame.Surface((W3, HEIGHT), pygame.SRCALPHA)
        rng  = random.Random(11)

        # Back mountain range
        pts = [(0, HEIGHT)]
        x   = 0
        while x < W3:
            pts.append((x, HEIGHT - rng.randint(80, 140)))
            x += rng.randint(50, 120)
        pts.append((W3, HEIGHT))
        pygame.draw.polygon(surf, self._L1, pts)

        # Castle spires (4) with crenellated tops
        for _ in range(4):
            sx = rng.randint(0, W3)
            sh = rng.randint(90, 155)
            sw = rng.randint(12, 24)
            sy = HEIGHT - sh
            pygame.draw.rect(surf, self._FAR, (sx, sy, sw, sh))
            notch_w = max(3, sw // 3)
            for ci in range(3):
                pygame.draw.rect(surf, self._FAR,
                                 (sx + ci * (sw // 3), sy - 9, notch_w, 9))

        # Front hill layer (rounder, lower)
        pts2 = [(0, HEIGHT)]
        x    = 0
        while x < W3:
            pts2.append((x, HEIGHT - rng.randint(60, 100)))
            x += rng.randint(60, 140)
        pts2.append((W3, HEIGHT))
        pygame.draw.polygon(surf, self._L2, pts2)

        return surf

    def _build_moon(self) -> pygame.Surface:
        """Static moon — soft lavender, r=38, with inner glow halo."""
        r    = 38
        size = (r + 6) * 2
        cx   = size // 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        # Inner glow halo (slightly larger, very faint)
        pygame.draw.circle(surf, (196, 168, 224, 20), (cx, cx), r + 4)
        # Moon body: #C4A8E0 lavender
        pygame.draw.circle(surf, (196, 168, 224, 255), (cx, cx), r)
        return surf

    def _build_trees(self) -> pygame.Surface:
        """2×WIDTH organic round-canopy tree silhouettes with bioluminescent tips."""
        W2     = WIDTH * 2
        surf   = pygame.Surface((W2, HEIGHT), pygame.SRCALPHA)
        rng    = random.Random(17)
        base_y = HEIGHT - 22

        for _ in range(15):
            tx    = rng.randint(0, W2)
            c_r   = rng.randint(10, 16)   # main canopy radius
            has_top = rng.random() < 0.55
            c_r2  = rng.randint(6, 10) if has_top else 0

            # Trunk: 4px wide, 12px tall, colour #1A1040
            pygame.draw.rect(surf, self._L2,
                             (tx - 2, base_y - 12, 4, 12))

            # Main canopy circle
            canopy_cy = base_y - 12 - c_r + 3
            pygame.draw.circle(surf, self._L2, (tx, canopy_cy), c_r)

            # Optional second smaller circle on top
            if has_top:
                top_cy = canopy_cy - c_r - c_r2 + 4
                pygame.draw.circle(surf, self._L2, (tx, top_cy), c_r2)
                tip_y = top_cy - c_r2
            else:
                tip_y = canopy_cy - c_r

            # Bioluminescent tip
            glow = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*self._TEAL, 180), (4, 4), 2)
            surf.blit(glow, (tx - 4, tip_y - 2))

        return surf

    def _build_fog(self) -> list[dict]:
        """7 pre-rendered fog wisp surfaces; x drifts each frame."""
        rng   = random.Random(23)
        wisps = []
        for _ in range(7):
            w = rng.randint(80, 160)
            h = rng.randint(8, 14)
            a = rng.randint(25, 40)
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            s.fill((*self._L4, a))
            wisps.append({
                "surf": s,
                "x":    rng.uniform(0, WIDTH * 2),
                "y":    rng.randint(HEIGHT // 2 - 40, HEIGHT - 90),
            })
        return wisps

    def _build_fore_hills(self) -> list:
        """Rounded foreground silhouette (2×WIDTH + margin)."""
        rng = random.Random(29)
        pts = [(0, HEIGHT)]
        x   = 0
        while x <= WIDTH * 2 + 100:
            pts.append((x, HEIGHT - rng.randint(30, 50)))
            x += rng.randint(60, 150)
        pts.append((WIDTH * 2 + 100, HEIGHT))
        return pts

    # ── Update & draw ────────────────────────────────────────────────────

    def update(self) -> None:
        self._fog_offset += 0.2
        for w in self._fog:
            w["x"] -= 0.2
            if w["x"] + w["surf"].get_width() < 0:
                w["x"] += WIDTH * 2

    def draw(self, surf: pygame.Surface, cam_x: int) -> None:
        # Moon — static, no parallax
        surf.blit(self._moon_surf, (WIDTH // 3, HEIGHT // 6))
        # Mountains (0.05× scroll)
        self._blit_wrap(surf, self._mtn_surf, cam_x, 0.05, WIDTH * 3)
        # Trees (0.15× scroll)
        self._blit_wrap(surf, self._tree_surf, cam_x, 0.15, WIDTH * 2)
        # Fog (0.4× scroll + drift)
        self._draw_fog(surf, cam_x)
        # Foreground hills (0.7× scroll)
        self._draw_fore_hills(surf, cam_x)

    def _blit_wrap(self, surf: pygame.Surface, layer: pygame.Surface,
                   cam_x: int, speed: float, total_w: int) -> None:
        scroll = int(cam_x * speed) % total_w
        blit_w = min(WIDTH, total_w - scroll)
        surf.blit(layer, (0, 0), (scroll, 0, blit_w, HEIGHT))
        if blit_w < WIDTH:
            surf.blit(layer, (blit_w, 0), (0, 0, WIDTH - blit_w, HEIGHT))

    def _draw_fog(self, surf: pygame.Surface, cam_x: int) -> None:
        base_scroll = int(cam_x * 0.4)
        for w in self._fog:
            rx = int(w["x"] - base_scroll) % (WIDTH * 2)
            if rx > WIDTH + w["surf"].get_width():
                continue
            surf.blit(w["surf"], (rx, int(w["y"])))

    def _draw_fore_hills(self, surf: pygame.Surface, cam_x: int) -> None:
        shift = cam_x * 0.7
        wrap  = WIDTH * 2 + 100
        moved = [((int(x) - int(shift)) % wrap, int(y))
                 for x, y in self._fore_pts]
        if len(moved) >= 3:
            pygame.draw.polygon(surf, (27, 16, 64), moved)


# ── CRT overlay ───────────────────────────────────────────────────────────────
class CRTOverlay:
    """Pre-rendered CRT scanlines + vignette blit each frame."""

    def __init__(self) -> None:
        self._scanlines = self._build_scanlines()
        self._vignette  = self._build_vignette()

    def _build_scanlines(self) -> pygame.Surface:
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 2):
            pygame.draw.line(surf, (0, 0, 0, 25), (0, y), (WIDTH, y))
        return surf

    def _build_vignette(self) -> pygame.Surface:
        """Corner-edge darkening only — 10% of each edge, quadratic falloff."""
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ew = WIDTH  // 10
        eh = HEIGHT // 10
        for i in range(ew):
            a = int(90 * ((ew - i) / ew) ** 2)
            pygame.draw.line(surf, (0, 0, 0, a), (i,           0), (i,           HEIGHT))
            pygame.draw.line(surf, (0, 0, 0, a), (WIDTH - 1 - i, 0), (WIDTH - 1 - i, HEIGHT))
        for i in range(eh):
            a = int(90 * ((eh - i) / eh) ** 2)
            pygame.draw.line(surf, (0, 0, 0, a), (0, i),            (WIDTH, i))
            pygame.draw.line(surf, (0, 0, 0, a), (0, HEIGHT - 1 - i), (WIDTH, HEIGHT - 1 - i))
        return surf

    def draw(self, surf: pygame.Surface, game_surf: pygame.Surface) -> None:
        """Blit chromatic aberration, then scanlines and vignette."""
        # Chromatic aberration: tinted copies offset ±1px
        ab_surf = game_surf.copy()

        red_tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        red_tint.fill((40, 0, 0, 15))
        ab_surf.blit(red_tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        surf.blit(ab_surf, (-1, 0), special_flags=pygame.BLEND_RGBA_ADD)

        blue_tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        blue_tint.fill((0, 0, 40, 15))
        ab_surf2 = game_surf.copy()
        ab_surf2.blit(blue_tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        surf.blit(ab_surf2, (1, 0), special_flags=pygame.BLEND_RGBA_ADD)

        surf.blit(self._scanlines, (0, 0))
        surf.blit(self._vignette,  (0, 0))


# ── HUD ───────────────────────────────────────────────────────────────────────
def draw_hud(surf: pygame.Surface, player: "Player",
             font_sm: pygame.font.Font, font_title: pygame.font.Font,
             frame: int, score: int = 0,
             coins_collected: int = 0, total_coins: int = 0) -> None:
    """Arcade-style HUD: score top-left, title centre, speed bar top-right."""
    # Score (top-left)
    surf.blit(font_sm.render("SCORE", True, COL_HUD_LABEL),  (12,  8))
    surf.blit(font_sm.render(str(score), True, COL_HUD_VALUE), (12, 22))
    surf.blit(font_sm.render(f"coins: {coins_collected} / {total_coins}",
                             True, (136, 136, 136)), (12, 36))

    # Title (centre)
    title = "RETRO PANTS"
    shadow = font_title.render(title, True, COL_TITLE_SHADOW)
    text   = font_title.render(title, True, COL_HUD_VALUE)
    tx = WIDTH // 2 - text.get_width() // 2
    surf.blit(shadow, (tx + 1, 9))
    surf.blit(text,   (tx,     8))

    # Speed bar (top-right)
    bar_w  = 80
    bar_h  = 8
    bar_x  = WIDTH - bar_w - 16
    bar_y  = 10
    speed  = abs(player.vx)
    fill   = int(bar_w * speed / MAX_SPEED)
    lbl    = font_sm.render("SPD", True, COL_HUD_LABEL)
    surf.blit(lbl, (bar_x - lbl.get_width() - 4, bar_y - 1))
    pygame.draw.rect(surf, (20, 14, 50),   (bar_x, bar_y, bar_w, bar_h))
    pygame.draw.rect(surf, COL_G_CAP,      (bar_x, bar_y, fill, bar_h))   # teal fill
    pygame.draw.rect(surf, COL_HUD_LABEL,  (bar_x, bar_y, bar_w, bar_h), 1)

    # State icon (below bar)
    ix, iy = bar_x + bar_w // 2, bar_y + bar_h + 10
    s = player.state
    if s == "run":
        # right-pointing arrow
        pygame.draw.polygon(surf, COL_HUD_LABEL,
                            [(ix - 5, iy - 4), (ix + 5, iy), (ix - 5, iy + 4)])
    elif s in ("jump", "fall"):
        # up-arrow
        dy = -1 if s == "jump" else 1
        pygame.draw.polygon(surf, COL_HUD_LABEL,
                            [(ix, iy - 5 * dy), (ix - 4, iy + 3 * dy),
                             (ix + 4, iy + 3 * dy)])
    elif s == "roll":
        pygame.draw.circle(surf, COL_HUD_LABEL, (ix, iy), 5, 2)
    else:  # idle
        pygame.draw.circle(surf, COL_HUD_LABEL, (ix, iy), 3)

    # Controls (bottom-left)
    ctrl = font_sm.render("← → move  |  Z/SPACE jump  |  ↓ roll", True, (70, 65, 90))
    surf.blit(ctrl, (12, HEIGHT - 20))


# ── Player ────────────────────────────────────────────────────────────────────
class Player:
    """
    Hand-drawn pixel-art character with scarf trail, expressive eyes,
    squash/stretch, and 4-frame leg animation.
    """

    W, H = 22, 30

    def __init__(self, x: float, y: float,
                 color: tuple = (255, 0, 0)) -> None:
        self.x        = x
        self.y        = y
        self.color    = color
        self.vx       = 0.0
        self.vy       = 0.0
        self.on_ground  = False
        self.prev_vy    = 0.0       # vy before landing — used for particles/shake
        self.facing     = 1
        self.coyote     = 0
        self.jump_buf   = 0
        self.rolling    = False
        self.roll_timer = 0
        self.anim_frame = 0
        self.anim_tick  = 0
        self.state      = "idle"
        self.roll_angle = 0.0       # eye spin when rolling
        self.land_squash = 0        # frames of landing squash remaining
        self.pos_history: list[tuple[int, int]] = []

        # Scarf trail: list of (x, y) centre positions
        self._trail: list[tuple[float, float]] = []

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self, keys: pygame.key.ScancodeWrapper, tiles: list,
               particles: ParticleSystem, camera: Camera) -> None:
        """Full physics + state + animation update."""
        left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump  = keys[pygame.K_z]     or keys[pygame.K_SPACE] or keys[pygame.K_UP]
        roll  = keys[pygame.K_DOWN]  or keys[pygame.K_s]

        # Roll
        if roll and self.on_ground and not self.rolling and abs(self.vx) > 4:
            self.rolling    = True
            self.roll_timer = 20
            self.vx         = self.facing * ROLL_SPEED

        if self.rolling:
            self.roll_timer -= 1
            self.roll_angle += 15
            if self.roll_timer <= 0 or not self.on_ground:
                self.rolling = False

        # Horizontal
        if not self.rolling:
            if right:
                self.vx += ACCEL; self.facing = 1
            if left:
                self.vx -= ACCEL; self.facing = -1

        friction = FRICTION if self.on_ground else AIR_FRICTION
        if not (left or right) or self.rolling:
            self.vx *= friction
        self.vx = clamp(self.vx, -MAX_SPEED, MAX_SPEED)

        # Jump buffer / coyote
        if jump:
            self.jump_buf = JUMP_BUFFER
        else:
            self.jump_buf = max(0, self.jump_buf - 1)

        if self.on_ground:
            self.coyote = COYOTE_FRAMES
        else:
            self.coyote = max(0, self.coyote - 1)

        if self.jump_buf > 0 and self.coyote > 0:
            self.vy       = JUMP_FORCE
            self.coyote   = 0
            self.jump_buf = 0

        if not jump and self.vy < -7:
            self.vy += 1.2

        # Gravity
        self.prev_vy  = self.vy
        self.vy      += GRAVITY
        self.vy       = clamp(self.vy, -99, MAX_FALL)

        # Move & resolve
        self.x += self.vx
        self._resolve_x(tiles)

        was_on_ground = self.on_ground
        self.on_ground = False
        self.y        += self.vy
        self._resolve_y(tiles)

        # Landing events
        if self.on_ground and not was_on_ground:
            vy_before = self.prev_vy
            if vy_before > IMPACT_VY_THRESHOLD:
                foot_x = self.x + self.W / 2
                foot_y = self.y + self.H
                particles.spawn_impact(foot_x, foot_y)
                self.land_squash = 6
            if vy_before > SHAKE_VY_THRESHOLD:
                camera.trigger_shake()

        # State machine
        if self.rolling:
            self.state = "roll"
        elif not self.on_ground:
            self.state = "jump" if self.vy < 0 else "fall"
        elif abs(self.vx) > 0.5:
            if (self.vx > 0 and left) or (self.vx < 0 and right):
                self.state = "skid"
            else:
                self.state = "run"
        else:
            self.state = "idle"

        # Dust particles
        if self.on_ground and abs(self.vx) > DUST_SPEED_THRESHOLD:
            foot_x = self.x + self.W / 2
            foot_y = self.y + self.H
            particles.spawn_dust(foot_x, foot_y, self.facing)

        # Anim tick
        speed    = abs(self.vx)
        interval = max(3, int(12 - speed))
        self.anim_tick += 1
        if self.anim_tick >= interval:
            self.anim_tick  = 0
            self.anim_frame = (self.anim_frame + 1) % 4

        # Scarf trail
        cx = self.x + self.W / 2
        cy = self.y + self.H / 2
        self._trail.insert(0, (cx, cy))
        if len(self._trail) > SCARF_HISTORY:
            self._trail.pop()

        # World bounds / respawn
        if self.x < 0:
            self.x = 0; self.vx = 0
        if self.y > HEIGHT + 200:
            self.x, self.y, self.vx, self.vy = 80.0, 100.0, 0.0, 0.0

        self.pos_history.insert(0, (int(self.x), int(self.y)))
        if len(self.pos_history) > 6:
            self.pos_history.pop()
        if self.land_squash > 0:
            self.land_squash -= 1

    def _resolve_x(self, tiles: list) -> None:
        r = self.rect
        for tile, solid in tiles:
            if solid and r.colliderect(tile):
                if self.vx > 0:
                    self.x = tile.left - self.W
                elif self.vx < 0:
                    self.x = tile.right
                self.vx = 0
                r = self.rect

    def _resolve_y(self, tiles: list) -> None:
        r = self.rect
        for tile, solid in tiles:
            if r.colliderect(tile):
                if solid:
                    if self.vy > 0:
                        self.y = tile.top - self.H
                        if self.vy > 5:
                            self.land_squash = 6
                        self.vy = 0
                        self.on_ground = True
                    elif self.vy < 0:
                        self.y = tile.bottom
                        self.vy = 0
                else:
                    if self.vy > 0 and (r.bottom - self.vy) <= tile.top + 4:
                        self.y = tile.top - self.H
                        self.vy = 0
                        self.on_ground = True
                r = self.rect

    # ── Drawing ─────────────────────────────────────────────────────────
    def draw(self, surf, cam_x):
        """Delegate rendering to draw_player.draw_fancy_player."""
        draw_fancy_player(surf, self, cam_x)


# ── Character select screen ───────────────────────────────────────────────────

def run_character_select(screen: pygame.Surface,
                         clock: pygame.time.Clock) -> tuple:
    """
    Show ghost character selection screen.
    Returns the chosen body color tuple when the player confirms.
    """
    # TEMP: skip selection screen while tuning character visuals.
    # Re-enable by removing these two lines and uncommenting the block below.
    selected_index = 0
    return GHOST_OPTIONS[selected_index]["color"]

    # ── Selection screen (commented out) ──────────────────────────────────
    font_title = pygame.font.SysFont("monospace", 28, bold=True)
    font_sub   = pygame.font.SysFont("monospace", 12)
    font_name  = pygame.font.SysFont("monospace", 13, bold=True)

    n        = len(GHOST_OPTIONS)
    selected = 0
    frame    = 0
    spacing  = 145
    start_x  = WIDTH // 2 - spacing * (n - 1) // 2

    # Pre-render the title (static)
    title_shadow = font_title.render("CHOOSE YOUR GHOST", True, (80, 10, 20))
    title_surf   = font_title.render("CHOOSE YOUR GHOST", True, (233, 69, 96))
    tx = WIDTH // 2 - title_surf.get_width() // 2

    # Subtitle
    sub_surf = font_sub.render(
        "◄ ► to browse     SPACE to play", True, (90, 85, 110))

    # Pre-render the twinkling stars (reuse module-level STARS list)
    ghost_cy = HEIGHT // 2 + 30

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    selected = (selected - 1) % n
                elif event.key == pygame.K_RIGHT:
                    selected = (selected + 1) % n
                elif event.key in (pygame.K_SPACE, pygame.K_z):
                    return GHOST_OPTIONS[selected]["color"]

        sel_col = GHOST_OPTIONS[selected]["color"]
        anim    = (frame // 30) % 2

        # ── Background ────────────────────────────────────────────────────
        screen.fill(COL_BG)
        draw_stars(screen, 0, frame)

        # Soft colour wash behind the whole ghost row (selected tint)
        wash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        wash_alpha = int(18 + 8 * math.sin(frame * 0.04))
        wash.fill((*sel_col, wash_alpha))
        screen.blit(wash, (0, 0))

        # Horizontal divider lines for retro feel
        div_y1 = 72
        div_y2 = HEIGHT - 55
        pygame.draw.line(screen, (40, 35, 60), (30, div_y1), (WIDTH - 30, div_y1))
        pygame.draw.line(screen, (40, 35, 60), (30, div_y2), (WIDTH - 30, div_y2))

        # ── Title ─────────────────────────────────────────────────────────
        screen.blit(title_shadow, (tx + 1, 31))
        screen.blit(title_surf,   (tx,     30))

        # ── Subtitle ──────────────────────────────────────────────────────
        screen.blit(sub_surf,
                    (WIDTH // 2 - sub_surf.get_width() // 2, HEIGHT - 38))

        # ── Ghost cards ───────────────────────────────────────────────────
        for i, opt in enumerate(GHOST_OPTIONS):
            ghost_cx = start_x + i * spacing
            is_sel   = (i == selected)
            scale    = 2.0 if is_sel else 1.7
            col      = opt["color"]

            # Subtle card background
            card_w, card_h = 110, 120
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card_alpha = 55 if is_sel else 25
            card_col   = col if is_sel else (30, 28, 45)
            pygame.draw.rect(card_surf, (*card_col, card_alpha),
                             (0, 0, card_w, card_h), border_radius=8)
            screen.blit(card_surf, (ghost_cx - card_w // 2, ghost_cy - 58))

            # Glow halo behind selected ghost (large soft circle)
            if is_sel:
                glow_r = int(52 + 4 * math.sin(frame * 0.07))
                glow   = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                for r in range(glow_r, 0, -4):
                    a = int(38 * (r / glow_r) ** 2)
                    pygame.draw.circle(glow, (*col, a), (glow_r, glow_r), r)
                screen.blit(glow, (ghost_cx - glow_r, ghost_cy - glow_r + 5))

            # Ghost itself
            g_surf = pygame.Surface((160, 130), pygame.SRCALPHA)
            draw_ghost_preview(g_surf, 80, 65, col, scale, anim)

            if not is_sel:
                mask = pygame.Surface((160, 130), pygame.SRCALPHA)
                mask.fill((255, 255, 255, 110))
                g_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            screen.blit(g_surf, (ghost_cx - 80, ghost_cy - 65))

            # Pulsing border — tinted with ghost colour
            if is_sel:
                pulse    = int(160 + 95 * math.sin(frame * 0.09))
                brd_col  = tuple(min(255, int(c * 0.7 + 255 * 0.3)) for c in col)
                brd      = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                pygame.draw.rect(brd, (*brd_col, pulse),
                                 (0, 0, card_w, card_h), 2, border_radius=8)
                screen.blit(brd, (ghost_cx - card_w // 2, ghost_cy - 58))

            # Name — ghost's own colour (bright selected, muted unselected)
            if is_sel:
                name_col = tuple(min(255, c + 60) for c in col)
            else:
                name_col = tuple(max(0, c // 3) for c in col)
            name_surf = font_name.render(opt["name"], True, name_col)
            screen.blit(name_surf,
                        (ghost_cx - name_surf.get_width() // 2, ghost_cy + 58))

        # ── Selection dots ────────────────────────────────────────────────
        dot_y  = HEIGHT - 22
        dot_sp = 14
        dot_ox = WIDTH // 2 - (n - 1) * dot_sp // 2
        for i in range(n):
            dcol  = GHOST_OPTIONS[i]["color"] if i == selected else (55, 50, 70)
            dsize = 5 if i == selected else 3
            pygame.draw.circle(screen, dcol, (dot_ox + i * dot_sp, dot_y), dsize)

        # ── Arrow hints ───────────────────────────────────────────────────
        arr_alpha = int(140 + 115 * math.sin(frame * 0.06))
        arr_surf  = pygame.Surface((24, 24), pygame.SRCALPHA)
        # Left arrow
        pygame.draw.polygon(arr_surf, (*sel_col, arr_alpha),
                            [(18, 4), (6, 12), (18, 20)])
        screen.blit(arr_surf, (18, ghost_cy - 12))
        arr_surf2 = pygame.Surface((24, 24), pygame.SRCALPHA)
        # Right arrow
        pygame.draw.polygon(arr_surf2, (*sel_col, arr_alpha),
                            [(6, 4), (18, 12), (6, 20)])
        screen.blit(arr_surf2, (WIDTH - 42, ghost_cy - 12))

        pygame.display.flip()
        clock.tick(FPS)
        frame += 1


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    pygame.init()
    _build_tile_surfaces()   # must be called after pygame.init()
    screen   = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("retro-pants")
    clock    = pygame.time.Clock()

    font_sm    = pygame.font.SysFont("monospace", 12)
    font_title = pygame.font.SysFont("monospace", 16, bold=True)
    font_float = pygame.font.SysFont("monospace", 14, bold=True)

    player_color = run_character_select(screen, clock)
    print(f"[startup] player.color = {player_color}")

    tiles      = build_tiles(LEVEL)
    player     = Player(80.0, 100.0, color=player_color)
    particles  = ParticleSystem()
    camera     = Camera()
    parallax   = ParallaxBackground()
    crt        = CRTOverlay()
    coins      = [Coin(x, y) for x, y in COIN_POSITIONS]

    # 6 enemies: (spawn_x, spawn_y, patrol_x1, patrol_x2)
    # Ground surface = row 14 top = 14*TILE = 448; enemy centre at 448 - ENEMY_R = 438
    _ER = Enemy.RADIUS
    enemies: list[Enemy] = [
        Enemy( 3*TILE+16, 14*TILE-_ER,  2*TILE+16,  8*TILE+16),  # s1 early
        Enemy(16*TILE+16, 14*TILE-_ER, 14*TILE+16, 20*TILE+16),  # s1 mid
        Enemy(39*TILE+16, 14*TILE-_ER, 38*TILE+16, 41*TILE+16),  # after s2 gap
        Enemy(47*TILE+16, 12*TILE-_ER, 46*TILE+16, 48*TILE+16),  # s3 step-2 platform
        Enemy(66*TILE+16, 14*TILE-_ER, 64*TILE+16, 69*TILE+16),  # after s4 gap
        Enemy(91*TILE+16, 14*TILE-_ER, 88*TILE+16, 95*TILE+16),  # s6 victory
    ]

    # Offscreen surface so CRT can composite on it
    game_surf   = pygame.Surface((WIDTH, HEIGHT))
    score       = 0
    float_texts: list[dict] = []
    frame       = 0

    # Ground shimmer state — briefly flashes a random cap tile's teal edge
    # Build list of cap-eligible (col, row) pairs once
    _cap_tiles = [
        (rect.x // TILE, rect.y // TILE)
        for rect, solid in tiles
        if solid
        and rect.y // TILE > 0
        and rect.x // TILE < len(LEVEL[rect.y // TILE - 1])
        and LEVEL[rect.y // TILE - 1][rect.x // TILE] == " "
    ]
    shimmer: dict = {"col": 0, "row": 0, "timer": 0, "next": 90}

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        keys = pygame.key.get_pressed()
        player.update(keys, tiles, particles, camera)

        # Coin collection
        for coin in coins:
            gained = coin.update(player, particles)
            if gained:
                score += gained
                float_texts.append({
                    "x": coin.x, "y": coin.y - 10,
                    "alpha": 255.0, "dy": -0.75,
                })

        # Enemy update + collision
        for enemy in enemies:
            enemy.update(tiles)
            gained = enemy.check_player(player, particles, camera, float_texts)
            if gained:
                score += gained

        # Floating score text decay
        next_ft = []
        for ft in float_texts:
            ft["y"]    += ft["dy"]
            ft["alpha"] = max(0.0, ft["alpha"] - 255.0 / 40)
            if ft["alpha"] > 0:
                next_ft.append(ft)
        float_texts = next_ft

        particles.update()
        camera.update(player.x)
        parallax.update()

        # Shimmer: every 90 frames pick a random cap tile and flash it for 6 frames
        shimmer["next"] -= 1
        if shimmer["next"] <= 0:
            shimmer["next"]  = 90
            shimmer["timer"] = 6
            if _cap_tiles:
                shimmer["col"], shimmer["row"] = random.choice(_cap_tiles)
        if shimmer["timer"] > 0:
            shimmer["timer"] -= 1

        cx, cy = camera.cx, camera.cy
        t_ms   = pygame.time.get_ticks()

        # ── Draw to game_surf ────────────────────────────────────────
        game_surf.fill(COL_BG)
        draw_stars(game_surf, cx, frame)
        parallax.draw(game_surf, cx)
        draw_tiles(game_surf, tiles, cx, cy, t_ms, shimmer)
        for coin in coins:
            coin.draw(game_surf, cx, cy, t_ms)
        particles.draw(game_surf, cx, cy)
        for enemy in enemies:
            enemy.draw(game_surf, cx, cy)
        player.draw(game_surf, cx)

        # Red screen flash on player hurt
        if camera.flash_timer > 0:
            _flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            _flash.fill((255, 0, 0, int(120 * camera.flash_timer / 20)))
            game_surf.blit(_flash, (0, 0))

        # Floating score texts (+100 coin, +200 stomp)
        for ft in float_texts:
            txt  = ft.get("text", "+100")
            col  = (255, 100, 100) if txt == "+200" else (255, 215, 0)
            ftxt = font_float.render(txt, True, col)
            ftxt.set_alpha(int(ft["alpha"]))
            game_surf.blit(ftxt, (int(ft["x"]) - cx - ftxt.get_width() // 2,
                                  int(ft["y"]) - cy))

        coins_col = sum(1 for c in coins if c.collected)
        draw_hud(game_surf, player, font_sm, font_title, frame,
                 score, coins_col, len(coins))

        # ── Composite to screen with CRT ─────────────────────────────
        screen.blit(game_surf, (0, 0))
        crt.draw(screen, game_surf)

        pygame.display.flip()
        clock.tick(FPS)
        frame += 1


if __name__ == "__main__":
    main()
