# F1 디버그 뷰 — 발 목표 원, 걸음 상태, 데드존, 수치 (PRD 16 U2: "F1에서 발이 목표 원 밖으로 나갈 때만 한 걸음")
import math

import config
import game_framework
from ui.draw import draw_line, draw_circle, draw_rect, fill_rect, draw_text

on = config.DEBUG_START      # 켜져 있는지
landings = []                # 착지 표시 [x, y, 나이] (월드 좌표)


def toggle():
    global on
    on = not on


def note_landing(x, y):
    # 착지 이벤트가 오면 그 자리에 퍼지는 원을 하나 만든다
    if on:
        landings.append([x, y, 0.0])


def update(dt):
    global landings
    for item in landings:
        item[2] += dt
    landings = [item for item in landings if item[2] < config.DEBUG_LAND_TIME]


def draw(camera, body, mouse, target, page, extra):
    if not on:
        return
    # 다리: 이상적 위치(바닥)에 임계 거리 원, 발 → 이상적 위치 선, 발 점
    for leg in body.all_legs():
        ix, iy = camera.to_screen(leg.ideal_x, leg.ideal_y)
        fx, fy = camera.to_screen(leg.foot_x, leg.foot_y)
        ring = config.COLOR_RED if leg.overstretched() else config.COLOR_YELLOW
        draw_circle(ix, iy, leg.threshold_now(), 1, ring, 0.7)           # 이 원 밖으로 발이 나가면 걸음 (질주 중엔 ×1.4)
        draw_line(fx, fy, ix, iy, 1, config.COLOR_GRAY, 0.8)
        dot = config.COLOR_GREEN if leg.stepping else config.COLOR_WHITE  # 초록 = 걷는 중
        fill_rect(fx - 2, fy - 2, 4, 4, dot)
    # 먹을 수 있는 링크의 판정 상자 (조각 상자 + COLLECT_MARGIN)
    m = config.COLLECT_MARGIN
    for x, y, w, h, text, target_doc, lid in page.links:
        if not page.groups[lid]['eaten']:
            sx, sy = camera.to_screen(x - m, y - m)
            draw_rect(sx, sy, w + 2 * m, h + 2 * m, 1, config.COLOR_SKY, 0.6)
    # 착지 순간: 초록 원이 퍼지며 사라짐
    for x, y, age in landings:
        k = age / config.DEBUG_LAND_TIME
        sx, sy = camera.to_screen(x, y)
        draw_circle(sx, sy, 3 + config.DEBUG_LAND_R * k, 2, config.COLOR_GREEN, 1 - k)
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
        'head %4d %4d  angle %5.2f  speed %5.1f%s' % (head.x, head.y, head.angle, body.speed, '  sprint x%.2f  h %.1f' % (body.sprint_k, body.height)),
        'gaps %s   legs %d  stepping %d' % (gaps, len(legs), sum(leg.stepping for leg in legs)),
        'wave %s' % ('%.2f / %.2fs' % (body.wave_t, body.wave_length()) if body.wave_t is not None
                     else ('cooldown %.1fs' % body.wave_cool if body.wave_cool > 0 else 'ready')),
        extra,
        '[F1] debug',
    ]
    h = 18 * len(lines) + 8
    top = config.SCREEN_H - config.DEBUG_PANEL_TOP     # HUD 상태 줄 아래부터
    fill_rect(0, top - h, 470, h, (0, 0, 0), 0.55)
    for i, text in enumerate(lines):
        draw_text(10, top - 14 - 18 * i, text, config.COLOR_WHITE)
