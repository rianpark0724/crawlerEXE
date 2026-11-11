# 플레이 화면 — 지금은 선·도형 그리기 테스트(S01-3·4). S02에서 테스트 그림을 지운다.
import math
from pico2d import get_events
from sdl2 import SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE

import config
import game_framework
from ui.draw import draw_line, draw_circle, draw_rect, fill_rect, draw_text

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


def draw_cross(x, y, color):
    # 끝점 확인용 작은 십자
    draw_line(x - 4, y, x + 4, y, 1, color)
    draw_line(x, y - 4, x, y + 4, 1, color)


def draw():
    # 화면 지우기·표시는 game_framework가 한다. 여기서는 그리기만.
    fill_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_BG)   # 남색 배경

    colors = [config.COLOR_WHITE, config.COLOR_ORANGE, config.COLOR_SKY]   # 테스트 색 3가지

    # [테스트] 왼쪽: 15° 간격 24방향 선, 색 3가지 번갈아 + 끝점 십자
    cx, cy, r = 300, config.SCREEN_H / 2, 200
    for i in range(24):
        a = math.radians(15 * i)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        draw_line(cx, cy, x, y, 1, colors[i % 3])
        draw_cross(x, y, colors[i % 3])

    # [테스트] 가운데 위: 계속 도는 선 + 반투명(alpha 0.4) 굵은 선
    sx, sy = 700, 560
    draw_line(sx, sy, sx + 120 * math.cos(spin), sy + 120 * math.sin(spin), 2, config.COLOR_RED)
    draw_line(sx - 120, sy - 100, sx + 120, sy - 100, 6, config.COLOR_WHITE, 0.4)

    # [테스트] 오른쪽: 두께 1~4px × 색 3가지 가로선
    for w in range(1, 5):
        for j, c in enumerate(colors):
            x0 = 900 + j * 120
            y = 520 + w * 30
            draw_line(x0, y, x0 + 100, y, w, c)

    # [테스트] 아래: 원 윤곽(반지름 10·30·60, 두께 1·2·3) + 사각 윤곽(두께 1·2·4)
    for k, (rad, w) in enumerate([(10, 1), (30, 2), (60, 3)]):
        draw_circle(640 + k * 140, 180, rad, w, colors[k])
    for k, w in enumerate([1, 2, 4]):
        draw_rect(1010 + k * 90, 130, 70, 100, w, colors[k])

    if config.SHOW_FPS:   # 왼쪽 위 FPS·프레임 시간 (디버그)
        draw_text(10, config.SCREEN_H - 14, 'FPS %5.1f  dt %5.1f ms' % (game_framework.fps, game_framework.frame_time * 1000), config.COLOR_GRAY)


def pause():
    pass


def resume():
    pass
