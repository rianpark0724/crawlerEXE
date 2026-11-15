# F1 디버그 뷰 — 발 목표 원, 걸음 상태, 데드존, 수치 (PRD 16 U2: "F1에서 발이 목표 원 밖으로 나갈 때만 한 걸음")
import math

import config
import game_framework
from ui.draw import draw_line, draw_circle, fill_rect, draw_text

on = config.DEBUG_START      # 켜져 있는지


def toggle():
    global on
    on = not on


def draw(camera, body, mouse, target):
    if not on:
        return
    # 다리: 이상적 위치(바닥)에 임계 거리 원, 발 → 이상적 위치 선, 발 점
    for leg in body.all_legs():
        ix, iy = camera.to_screen(leg.ideal_x, leg.ideal_y)
        fx, fy = camera.to_screen(leg.foot_x, leg.foot_y)
        ring = config.COLOR_RED if leg.overstretched() else config.COLOR_YELLOW
        draw_circle(ix, iy, leg.threshold, 1, ring, 0.7)                 # 이 원 밖으로 발이 나가면 걸음
        draw_line(fx, fy, ix, iy, 1, config.COLOR_GRAY, 0.8)
        dot = config.COLOR_GREEN if leg.stepping else config.COLOR_WHITE  # 초록 = 걷는 중
        fill_rect(fx - 2, fy - 2, 4, 4, dot)
    # 카메라 데드존 경계
    draw_line(0, camera.dead_low, config.SCREEN_W, camera.dead_low, 1, config.COLOR_GRAY, 0.4)
    draw_line(0, camera.dead_high, config.SCREEN_W, camera.dead_high, 1, config.COLOR_GRAY, 0.4)
    # 수치 (왼쪽 위, 반투명 판 위에)
    head = body.segs[0]
    legs = body.all_legs()
    gaps = ' '.join('%.1f' % math.hypot(a.x - b.x, a.y - b.y) for a, b in zip(body.segs, body.segs[1:]))
    lines = [
        'FPS %5.1f  dt %5.1f ms' % (game_framework.fps, game_framework.frame_time * 1000),
        'mouse screen %4d %4d  world %4d %4d  camera.y %5.1f' % (mouse[0], mouse[1], target[0], target[1], camera.y),
        'head %4d %4d  angle %5.2f  speed %5.1f' % (head.x, head.y, head.angle, body.speed),
        'gaps %s   legs %d  stepping %d' % (gaps, len(legs), sum(leg.stepping for leg in legs)),
        '[F1] debug',
    ]
    h = 18 * len(lines) + 8
    fill_rect(0, config.SCREEN_H - h, 470, h, (0, 0, 0), 0.55)
    for i, text in enumerate(lines):
        draw_text(10, config.SCREEN_H - 14 - 18 * i, text, config.COLOR_WHITE)
