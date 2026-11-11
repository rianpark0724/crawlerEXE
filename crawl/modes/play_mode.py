# 플레이 화면 — 지금은 선 그리기 테스트(S01-3). S02에서 테스트 그림을 지운다.
import math
from pico2d import get_events
from sdl2 import SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE

import config
import game_framework
from ui.draw import draw_line

spin = 0.0   # 테스트: 계속 도는 선의 각도(라디안)


def init():
    global spin
    spin = 0.0


def finish():
    pass


def handle_events():
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()


def update():
    global spin
    spin += 1.0 * game_framework.frame_time   # 초당 1 rad 회전


def draw_cross(x, y):
    # 끝점 확인용 작은 십자
    draw_line(x - 4, y, x + 4, y)
    draw_line(x, y - 4, x, y + 4)


def draw():
    # 화면 지우기·표시는 game_framework가 한다. 여기서는 그리기만.
    # [테스트] 왼쪽: 중심에서 15° 간격 24방향 선 + 끝점 십자
    cx, cy, r = 360, config.SCREEN_H / 2, 220
    for i in range(24):
        a = math.radians(15 * i)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        draw_line(cx, cy, x, y)
        draw_cross(x, y)
    # [테스트] 오른쪽: 계속 도는 선 + 두께 비교(1~4px 가로선)
    sx, sy = 920, config.SCREEN_H / 2 + 80
    draw_line(sx, sy, sx + 160 * math.cos(spin), sy + 160 * math.sin(spin), 2)
    for w in range(1, 5):
        y = 120 + w * 30
        draw_line(760, y, 1080, y, w)


def pause():
    pass


def resume():
    pass
