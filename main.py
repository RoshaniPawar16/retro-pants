"""retro-pants  —  arcade platformer with CRT visual treatment."""

import pygame
import sys
import math
import random
from draw_player import draw_fancy_player, draw_ghost_preview

# ── Display ──────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 960, 540
FPS           = 60
TILE          = 32

# ── Palette ───────────────────────────────────────────────────────────────────
COL_BG            = (13,  13,  13)
COL_GROUND        = (26,  26,  46)
COL_GROUND_EDGE   = (233, 69,  96)
COL_PLATFORM      = (22,  33,  62)
COL_PLATFORM_DARK = (15,  52,  96)
COL_BODY          = (240, 232, 210)   # warm cream
COL_OUTLINE       = (10,  10,  10)
COL_SCARF         = (255, 107, 107)   # #FF6B6B
COL_STAR_W        = (255, 255, 255)
COL_STAR_B        = (170, 170, 255)
COL_STAR_R        = (255, 107, 107)
COL_HUD_LABEL     = (233, 69,  96)
COL_HUD_VALUE     = (255, 255, 255)
COL_TITLE_SHADOW  = (233, 69,  96)

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

# ── Level map (80+ columns) ───────────────────────────────────────────────────
# 0=air  G=solid ground  P=pass-through platform
LEVEL = [
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                            P                                  ",
    "                                       P         P                             ",
    "                  P                                    P    P                  ",
    "             P         P                    P                        P         ",
    "                  P              P                P                       P    ",
    "    P                       P                          P                       ",
    "                                                                                ",
    "GGGGGGGGG        GGGG    GGGG        GGGGG    GGG   GGGGG        GGGGGGG       ",
    "                                                                                ",
    "         GGGG                GGGG                         GGGG                 ",
    "                  P                    P        P                    P         ",
    "GGGGGGGGGGGGGG         GGGG      GGGGGGGGG           GGGGGGGGGGG          GGGG ",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
]

# ── Coin positions (pixel x, pixel y — placed above platform surfaces) ────────
_T = TILE
COIN_POSITIONS: list[tuple[float, float]] = [
    # Arc above left ground (row 10, cols 1-5)
    ( 1*_T+16, 10*_T-50), ( 2*_T+16, 10*_T-70), ( 3*_T+16, 10*_T-85),
    ( 4*_T+16, 10*_T-70), ( 5*_T+16, 10*_T-50),
    # Mid-air gap reward (between row-10 ground sections, requires jump)
    (12*_T+16,  9*_T+10), (14*_T+16,  8*_T+16), (16*_T+16,  9*_T+10),
    # Above second ground cluster (row 10, cols 17-20)
    (17*_T+16, 10*_T-45), (18*_T+16, 10*_T-65), (20*_T+16, 10*_T-45),
    # Above third ground cluster (row 10, cols 25-28)
    (25*_T+16, 10*_T-45), (26*_T+16, 10*_T-65), (28*_T+16, 10*_T-45),
    # Elevated — above row-12 raised section (cols 9-12)
    ( 9*_T+16, 12*_T-45), (10*_T+16, 12*_T-65), (12*_T+16, 12*_T-45),
    # Above row-14 left ground (cols 2-8)
    ( 2*_T+16, 14*_T-45), ( 5*_T+16, 14*_T-70), ( 8*_T+16, 14*_T-45),
    # Above mid-level ground (row 10, cols 37-41)
    (37*_T+16, 10*_T-45), (39*_T+16, 10*_T-65), (41*_T+16, 10*_T-45),
    # High-risk: above pass-through platforms (rows 7-8, requires skillful jump)
    (18*_T+16,  7*_T-30), (28*_T+16,  8*_T-30),
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


# ── Tile drawing ──────────────────────────────────────────────────────────────
def draw_tiles(surf: pygame.Surface, tiles: list, cam_x: int, cam_y: int) -> None:
    """Draw ground and platform tiles with new palette."""
    for rect, solid in tiles:
        rx = rect.x - cam_x
        ry = rect.y - cam_y
        if rx > WIDTH or rx + TILE < 0:
            continue
        if solid:
            pygame.draw.rect(surf, COL_GROUND, (rx, ry, TILE, TILE))
            pygame.draw.rect(surf, COL_GROUND_EDGE, (rx, ry, TILE, 3))
        else:
            pygame.draw.rect(surf, COL_PLATFORM_DARK, (rx + 2, ry + 6, TILE, 8))
            pygame.draw.rect(surf, COL_PLATFORM, (rx, ry + 4, TILE, 8),
                             border_radius=3)


# ── Particle system ───────────────────────────────────────────────────────────
class ParticleSystem:
    """Manages dust and impact particles; no external assets."""

    _dust_colors = [COL_GROUND_EDGE, COL_STAR_W, COL_STAR_B]

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

    def trigger_shake(self, magnitude: float = SHAKE_MAGNITUDE,
                      frames: int = SHAKE_FRAMES) -> None:
        self._shake_frames = frames
        self._shake_mag    = magnitude

    def update(self, target_x: float) -> None:
        target = target_x - WIDTH // 3
        self.x += (target - self.x) * 0.12
        self.x = max(0.0, self.x)
        self.y = 0.0

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


# ── Parallax background ───────────────────────────────────────────────────────
class ParallaxBackground:
    """Three-layer parallax: ruins, drifting clouds, silhouette hills."""

    _COL_HILLS  = (18, 18, 36)
    _COL_HILLS2 = (26, 26, 46)

    def __init__(self) -> None:
        self._cloud_offset: float = 0.0
        self._ruins_surf  = self._build_ruins()
        self._hills       = self._build_hills()
        self._clouds_surf = self._build_clouds()

    # ── Layer builders ──────────────────────────────────────────────────
    def _build_ruins(self) -> pygame.Surface:
        """Pre-render 6 faint geometric outlines to a 2×-wide SRCALPHA surface."""
        surf = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        col  = (26, 26, 46, 20)
        rng  = random.Random(7)
        for _ in range(6):
            kind = rng.choice(["circle", "rect"])
            x    = rng.randint(0, WIDTH * 2 - 1)
            y    = rng.randint(HEIGHT // 4, HEIGHT - 80)
            if kind == "circle":
                r = rng.randint(10, 32)
                pygame.draw.circle(surf, col, (x, y), r, 2)
            else:
                w = rng.randint(20, 55)
                h = rng.randint(25, 65)
                pygame.draw.rect(surf, col, (x, y - h, w, h), 2)
        return surf

    def _build_hills(self) -> tuple[list, list]:
        """Two polygon hill layers."""
        def make_layer(seed: int, y_base: int, amp: int, freq: float) -> list:
            rng2 = random.Random(seed)
            pts = [(0, HEIGHT)]
            x = 0
            while x <= WIDTH * 2 + 100:
                h = y_base - int(amp * abs(math.sin(x * freq + rng2.uniform(0, 1))))
                pts.append((x, h))
                x += rng2.randint(40, 110)
            pts.append((WIDTH * 2 + 100, HEIGHT))
            return pts

        layer1 = make_layer(3, HEIGHT - 60, 90, 0.008)
        layer2 = make_layer(9, HEIGHT - 30, 50, 0.014)
        return layer1, layer2

    def _build_clouds(self) -> pygame.Surface:
        """Pre-render thin horizontal atmosphere streaks to a 2×-wide surface."""
        surf = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        col  = (170, 170, 255)
        rng  = random.Random(13)
        for _ in range(30):
            x     = rng.randint(0, WIDTH * 2 - 1)
            y     = rng.randint(30, HEIGHT // 2 - 20)
            w     = rng.randint(20, 60)
            h     = rng.choice([3, 3, 4])
            alpha = rng.randint(30, 50)
            pygame.draw.rect(surf, (*col, alpha), (x, y, w, h))
            if x + w > WIDTH * 2:          # wrap streak that bleeds off edge
                pygame.draw.rect(surf, (*col, alpha),
                                 (x + w - WIDTH * 2, y, w, h))
        return surf

    # ── Draw ────────────────────────────────────────────────────────────
    def update(self) -> None:
        self._cloud_offset += 0.3

    def draw(self, surf: pygame.Surface, cam_x: int) -> None:
        self._draw_ruins(surf, cam_x)
        self._draw_hills(surf, cam_x)
        self._draw_clouds(surf, cam_x)

    def _draw_ruins(self, surf: pygame.Surface, cam_x: int) -> None:
        """Blit pre-rendered ruins at 0.1× parallax speed, wrapping."""
        scroll = int(cam_x * 0.1) % (WIDTH * 2)
        blit_w = min(WIDTH, WIDTH * 2 - scroll)
        surf.blit(self._ruins_surf, (0, 0), (scroll, 0, blit_w, HEIGHT))
        if blit_w < WIDTH:
            surf.blit(self._ruins_surf, (blit_w, 0),
                      (0, 0, WIDTH - blit_w, HEIGHT))

    def _draw_hills(self, surf: pygame.Surface, cam_x: int) -> None:
        layer1, layer2 = self._hills
        shift = cam_x * 0.6

        def offset_pts(pts: list, dx: float) -> list:
            moved = []
            wrap  = WIDTH * 2 + 100
            for (x, y) in pts:
                nx = (x - dx) % wrap
                moved.append((int(nx), int(y)))
            return moved

        pts1 = offset_pts(layer1, shift)
        pts2 = offset_pts(layer2, shift)
        if len(pts1) >= 3:
            pygame.draw.polygon(surf, self._COL_HILLS, pts1)
        if len(pts2) >= 3:
            pygame.draw.polygon(surf, self._COL_HILLS2, pts2)

    def _draw_clouds(self, surf: pygame.Surface, cam_x: int) -> None:
        """Blit pre-rendered streak surface at 0.3× parallax + slow drift."""
        scroll = int(self._cloud_offset + cam_x * 0.3) % (WIDTH * 2)
        blit_w = min(WIDTH, WIDTH * 2 - scroll)
        surf.blit(self._clouds_surf, (0, 0), (scroll, 0, blit_w, HEIGHT))
        if blit_w < WIDTH:
            surf.blit(self._clouds_surf, (blit_w, 0),
                      (0, 0, WIDTH - blit_w, HEIGHT))


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
    pygame.draw.rect(surf, (40, 40, 60), (bar_x, bar_y, bar_w, bar_h))
    pygame.draw.rect(surf, COL_HUD_VALUE, (bar_x, bar_y, fill, bar_h))
    pygame.draw.rect(surf, COL_HUD_LABEL, (bar_x, bar_y, bar_w, bar_h), 1)

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
    screen   = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("retro-pants")
    clock    = pygame.time.Clock()

    font_sm    = pygame.font.SysFont("monospace", 12)
    font_title = pygame.font.SysFont("monospace", 16, bold=True)
    font_float = pygame.font.SysFont("monospace", 14, bold=True)

    player_color = run_character_select(screen, clock)

    tiles      = build_tiles(LEVEL)
    player     = Player(80.0, 100.0, color=player_color)
    particles  = ParticleSystem()
    camera     = Camera()
    parallax   = ParallaxBackground()
    crt        = CRTOverlay()
    coins      = [Coin(x, y) for x, y in COIN_POSITIONS]

    # Offscreen surface so CRT can composite on it
    game_surf   = pygame.Surface((WIDTH, HEIGHT))
    score       = 0
    float_texts: list[dict] = []
    frame       = 0

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

        cx, cy = camera.cx, camera.cy
        t_ms   = pygame.time.get_ticks()

        # ── Draw to game_surf ────────────────────────────────────────
        game_surf.fill(COL_BG)
        draw_stars(game_surf, cx, frame)
        parallax.draw(game_surf, cx)
        draw_tiles(game_surf, tiles, cx, cy)
        for coin in coins:
            coin.draw(game_surf, cx, cy, t_ms)
        particles.draw(game_surf, cx, cy)
        player.draw(game_surf, cx)

        # Floating +100 texts
        for ft in float_texts:
            ftxt = font_float.render("+100", True, (255, 215, 0))
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
