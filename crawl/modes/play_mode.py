# 플레이 화면 — 지금은 빈 화면. ESC 또는 창 닫기로 종료.
from pico2d import get_events
from sdl2 import SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE

import game_framework


def init():
    pass


def finish():
    pass


def handle_events():
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()


def update():
    pass


def draw():
    # 화면 지우기·표시는 game_framework가 한다. 여기서는 그리기만.
    pass


def pause():
    pass


def resume():
    pass
