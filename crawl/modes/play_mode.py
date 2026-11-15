# 플레이 화면 — 크롤러가 커서를 따라가고 카메라가 머리를 따라 세로로 스크롤. 커서 월드 좌표는 매 프레임 갱신(S03-4).
import math
from pico2d import get_events
from sdl2 import SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE, SDL_MOUSEMOTION

import config
import game_framework
from crawler.body import Body
from world.camera import Camera
from world.stage import Page, load_doc
from ui.draw import draw_line, fill_rect, draw_text

mouse_x, mouse_y = 0.0, 0.0   # 커서 위치 (화면 좌표, y 위로 증가) — 커서 그리기용
target_x, target_y = 0.0, 0.0 # 커서 위치 (월드 좌표) — 크롤러 목표
body = None                   # 크롤러 몸
camera = None
page = None


def init():
    global mouse_x, mouse_y, target_x, target_y, body, camera, page
    page = Page(config.TEST_PAGE_HEIGHT, load_doc('crawler'))
    camera = Camera(page.height)                    # 페이지 맨 위에서 시작
    mouse_x, mouse_y = config.SCREEN_W / 2, config.SCREEN_H / 2   # 첫 마우스 이벤트 전에는 화면 가운데
    target_x, target_y = camera.to_world(mouse_x, mouse_y)
    body = Body(*config.TEST_SPAWN)


def finish():
    global body, camera, page
    body = None
    camera = None
    page = None


def handle_events():
    global mouse_x, mouse_y
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        elif event.type == SDL_MOUSEMOTION:
            # 마우스 이벤트 y는 위가 0 → 아래가 0인 pico2d 좌표로 뒤집는다
            mouse_x = event.x
            mouse_y = config.SCREEN_H - 1 - event.y


def update():
    global target_x, target_y
    # 커서의 월드 좌표는 매 프레임 다시 계산한다 — 마우스를 가만히 둬도 카메라가 움직이면 가리키는 곳이 바뀐다
    target_x, target_y = camera.to_world(mouse_x, mouse_y)
    body.update(target_x, target_y, game_framework.frame_time)
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
    draw_cursor()

    if config.SHOW_FPS:   # 왼쪽 위 FPS·프레임 시간 (디버그)
        draw_line(0, camera.dead_low, config.SCREEN_W, camera.dead_low, 1, config.COLOR_GRAY, 0.3)     # 데드존 경계
        draw_line(0, camera.dead_high, config.SCREEN_W, camera.dead_high, 1, config.COLOR_GRAY, 0.3)
        draw_text(10, config.SCREEN_H - 14, 'FPS %5.1f  dt %5.1f ms' % (game_framework.fps, game_framework.frame_time * 1000), config.COLOR_GRAY)
        draw_text(10, config.SCREEN_H - 32, 'mouse screen %4d %4d  world %4d %4d  camera.y %5.1f' % (mouse_x, mouse_y, target_x, target_y, camera.y), config.COLOR_GRAY)
        head = body.segs[0]
        draw_text(10, config.SCREEN_H - 50, 'head %4d %4d  angle %5.2f  speed %5.1f' % (head.x, head.y, head.angle, body.speed), config.COLOR_GRAY)
        gaps = ['%.1f' % math.hypot(a.x - b.x, a.y - b.y) for a, b in zip(body.segs, body.segs[1:])]
        draw_text(10, config.SCREEN_H - 68, 'gaps ' + ' '.join(gaps), config.COLOR_GRAY)   # 마디 간격 (모두 19.0이어야 함)


def pause():
    pass


def resume():
    pass
