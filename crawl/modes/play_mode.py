# 플레이 화면 — 스테이지 JSON을 읽어 페이지를 만들고, 크롤러가 커서를 따라 걷는다(S05-1). F1 디버그 뷰.
from pico2d import get_events
from sdl2 import (SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE, SDLK_F1, SDL_MOUSEMOTION,
                  SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_BUTTON_LEFT)

import config
import game_framework
from crawler.body import Body
from world.camera import Camera
from world.stage import Page, load_stage, load_doc
from ui.hud import draw_scrollbar
from ui.draw import draw_line, fill_rect
from ui import debug_view

mouse_x, mouse_y = 0.0, 0.0   # 커서 위치 (화면 좌표, y 위로 증가) — 커서 그리기용
target_x, target_y = 0.0, 0.0 # 커서 위치 (월드 좌표) — 크롤러 목표
body = None                   # 크롤러 몸
left_down = False             # 좌클릭을 누르고 있는지 (질주)
camera = None
page = None
stage = None                  # 지금 스테이지 JSON 내용 (dict)


def init(stage_id=config.FIRST_STAGE):
    global mouse_x, mouse_y, target_x, target_y, body, camera, page, left_down, stage
    left_down = False
    stage = load_stage(stage_id)
    page = Page(stage['height'], load_doc(stage['page']))   # 배경 문서 (PRD 11.2 "page")
    camera = Camera(page.height)                    # 페이지 맨 위에서 시작
    mouse_x, mouse_y = config.SCREEN_W / 2, config.SCREEN_H / 2   # 첫 마우스 이벤트 전에는 화면 가운데
    target_x, target_y = camera.to_world(mouse_x, mouse_y)
    body = Body(*stage['spawn'])                    # 시작 위치


def finish():
    global body, camera, page, stage
    body = None
    camera = None
    page = None
    stage = None


def handle_events():
    global mouse_x, mouse_y, left_down
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_F1:
            debug_view.toggle()
        elif event.type == SDL_MOUSEMOTION:
            # 마우스 이벤트 y는 위가 0 → 아래가 0인 pico2d 좌표로 뒤집는다
            mouse_x = event.x
            mouse_y = config.SCREEN_H - 1 - event.y
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            left_down = True
        elif event.type == SDL_MOUSEBUTTONUP and event.button == SDL_BUTTON_LEFT:
            left_down = False


def update():
    global target_x, target_y
    # 커서의 월드 좌표는 매 프레임 다시 계산한다 — 마우스를 가만히 둬도 카메라가 움직이면 가리키는 곳이 바뀐다
    target_x, target_y = camera.to_world(mouse_x, mouse_y)
    body.update(target_x, target_y, game_framework.frame_time, left_down)
    camera.update(body.segs[0].y, game_framework.frame_time)


def draw_cursor():
    s = config.CURSOR_SIZE
    draw_line(mouse_x - s, mouse_y, mouse_x + s, mouse_y, 1, config.COLOR_YELLOW)
    draw_line(mouse_x, mouse_y - s, mouse_x, mouse_y + s, 1, config.COLOR_YELLOW)


def draw():
    # 화면 지우기·표시는 game_framework가 한다. 여기서는 그리기만.
    fill_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_BG)   # 남색 배경
    page.draw(camera)
    body.draw(camera)
    draw_scrollbar(camera, page.height)   # HUD — 화면 좌표

    debug_view.draw(camera, body, (mouse_x, mouse_y), (target_x, target_y))   # F1
    draw_cursor()


def pause():
    pass


def resume():
    pass
