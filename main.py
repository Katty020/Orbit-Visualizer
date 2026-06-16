import pygame
import sys
import math
import os
import random
from datetime import datetime

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Orbit Visualizers")

width = screen.get_width()
height = screen.get_height()
fps = pygame.time.Clock()
centre = (width // 2, height // 2)

show_axes = False
show_hud = True
show_orbits = True
show_links = False
show_trails = True
paused = False

time_scale = 1.0
frame_count = 0

planets = []
stars = []

PALETTE = [
    (255, 105, 180),
    (0, 206, 209),
    (135, 206, 250),
    (255, 215, 0),
    (186, 85, 211),
    (255, 160, 122),
    (50, 205, 50),
    (255, 99, 71),
]

def from_centre(x, y):
    return (centre[0] + x, centre[1] - y)

def distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(value, low, high):
    return max(low, min(high, value))

def draw_vertical_gradient(surface, top_color, bottom_color):
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(lerp(top_color[0], bottom_color[0], t))
        g = int(lerp(top_color[1], bottom_color[1], t))
        b = int(lerp(top_color[2], bottom_color[2], t))
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

def draw_glow(surface, pos, core_color, radius):
    glow_surface = pygame.Surface((radius * 6, radius * 6), pygame.SRCALPHA)
    for i in range(5, 0, -1):
        alpha = int(60 * (i / 5))
        pygame.draw.circle(
            glow_surface,
            (*core_color, alpha),
            (radius * 3, radius * 3),
            radius + i * 3
        )
    surface.blit(glow_surface, (pos[0] - radius * 3, pos[1] - radius * 3))
    pygame.draw.circle(surface, core_color, pos, radius)

def build_starfield(count=350):
    for _ in range(count):
        stars.append({
            "pos": (random.randint(0, width), random.randint(0, height)),
            "radius": random.randint(1, 2),
            "twinkle": random.uniform(0.6, 1.0),
            "speed": random.uniform(0.5, 1.5),
        })

def add_planet(mouse_pos):
    rad = distance(centre, mouse_pos)
    if rad < 30:
        return
    ang = math.atan2(centre[1] - mouse_pos[1], mouse_pos[0] - centre[0])
    ang_vel = math.sqrt(1 / rad ** 3) * 90
    size = int(clamp(3 + rad / 120, 3, 14))
    color = random.choice(PALETTE)
    planets.append({
        "a": rad,
        "angle": ang,
        "omega": ang_vel,
        "color": color,
        "size": size,
        "trail": [],
    })

def remove_nearest(mouse_pos, max_distance=45):
    if not planets:
        return
    closest_index = None
    closest_dist = None
    for i, planet in enumerate(planets):
        pos = from_centre(
            planet["a"] * math.cos(planet["angle"]),
            planet["a"] * math.sin(planet["angle"])
        )
        d = distance(pos, mouse_pos)
        if closest_dist is None or d < closest_dist:
            closest_dist = d
            closest_index = i
    if closest_dist is not None and closest_dist <= max_distance:
        planets.pop(closest_index)

def update_planets():
    for planet in planets:
        planet["angle"] = planet["angle"] + planet["omega"] * time_scale
        if frame_count % 2 == 0:
            planet["trail"].append(
                from_centre(
                    planet["a"] * math.cos(planet["angle"]),
                    planet["a"] * math.sin(planet["angle"])
                )
            )
            if len(planet["trail"]) > 220:
                planet["trail"].pop(0)

def render():
    draw_vertical_gradient(screen, (4, 6, 18), (1, 1, 8))

    tick = pygame.time.get_ticks() / 1000
    for star in stars:
        twinkle = star["twinkle"] + 0.2 * math.sin(tick * star["speed"])
        brightness = int(clamp(180 * twinkle, 80, 255))
        pygame.draw.circle(screen, (brightness, brightness, brightness), star["pos"], star["radius"])

    if show_orbits:
        for planet in planets:
            pygame.draw.circle(
                screen,
                (40, 70, 90),
                center=centre,
                radius=int(planet["a"]),
                width=1
            )

    if show_trails:
        for planet in planets:
            trail_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            for i in range(1, len(planet["trail"])):
                alpha = int(255 * (i / len(planet["trail"])) * 0.35)
                pygame.draw.line(
                    trail_surface,
                    (*planet["color"], alpha),
                    planet["trail"][i - 1],
                    planet["trail"][i],
                    2
                )
            screen.blit(trail_surface, (0, 0))

    if show_links and len(planets) > 1:
        for i in range(len(planets) - 1):
            a = planets[i]
            b = planets[i + 1]
            pos_a = from_centre(a["a"] * math.cos(a["angle"]), a["a"] * math.sin(a["angle"]))
            pos_b = from_centre(b["a"] * math.cos(b["angle"]), b["a"] * math.sin(b["angle"]))
            pygame.draw.line(screen, (200, 200, 220), pos_a, pos_b, 1)

    for planet in planets:
        pos = from_centre(
            planet["a"] * math.cos(planet["angle"]),
            planet["a"] * math.sin(planet["angle"])
        )
        draw_glow(screen, pos, planet["color"], planet["size"])

    draw_glow(screen, centre, (255, 196, 64), 18)
    pygame.draw.circle(screen, (255, 120, 20), centre, 9)

    mouse_pos = pygame.mouse.get_pos()
    mouse_radius = distance(centre, mouse_pos)
    pygame.draw.circle(screen, (0, 95, 105), centre, int(mouse_radius), 1)
    draw_glow(screen, mouse_pos, (120, 255, 240), 6)

    if show_axes:
        pygame.draw.line(screen, (0, 120, 0), (0, height // 2), (width, height // 2))
        pygame.draw.line(screen, (0, 120, 0), (width // 2, 0), (width // 2, height))
        pygame.draw.line(screen, (200, 60, 60), centre, mouse_pos)

    if show_hud:
        font = pygame.font.SysFont("consolas", 16)
        info = [
            f"Planets: {len(planets)}",
            f"Time scale: {time_scale:.2f}x",
            f"Paused: {'Yes' if paused else 'No'}",
            "Left click: add planet | Right click: remove planet",
            "Space: pause | T: trails | O: orbits | L: links",
            "A: axes | C: clear trails | R: reset | H: hide HUD",
            "S: screenshot | +/-: speed | Q: quit",
        ]
        for i, line in enumerate(info):
            label = font.render(line, True, (220, 230, 255))
            screen.blit(label, (20, 20 + i * 18))

        ang = math.degrees(math.atan2(centre[1] - mouse_pos[1], mouse_pos[0] - centre[0]))
        readout = font.render(
            f"Radius: {int(mouse_radius)}  Angle: {int(ang)} deg",
            True,
            (240, 240, 240)
        )
        screen.blit(readout, (mouse_pos[0] + 12, mouse_pos[1] + 8))


build_starfield()

while True:
    frame_count += 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_q]:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                if not os.path.isdir("images"):
                    os.makedirs("images")
                pygame.image.save(screen, f"images/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png")
            elif event.key == pygame.K_a:
                show_axes = not show_axes
            elif event.key == pygame.K_h:
                show_hud = not show_hud
            elif event.key == pygame.K_t:
                show_trails = not show_trails
            elif event.key == pygame.K_o:
                show_orbits = not show_orbits
            elif event.key == pygame.K_l:
                show_links = not show_links
            elif event.key == pygame.K_c:
                for planet in planets:
                    planet["trail"] = []
            elif event.key == pygame.K_r:
                planets = []
            elif event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                time_scale = clamp(time_scale + 0.1, 0.1, 4.0)
            elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                time_scale = clamp(time_scale - 0.1, 0.1, 4.0)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            add_planet(pygame.mouse.get_pos())
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            remove_nearest(pygame.mouse.get_pos())

    if not paused:
        update_planets()
    render()
    pygame.display.update()
    fps.tick(60)
