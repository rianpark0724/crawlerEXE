# 크롤러 효과 — 질주 잔상, 착지 흙먼지. 좌표는 월드, 그릴 때만 화면으로.
import math

import config
from ui.draw import fill_rect, fill_rect_rotated


class Effects:
    def __init__(self):
        self.puffs = []          # 흙먼지 [x, y, 나이]
        self.ghosts = []         # 잔상 [나이, 몸 높이, [(x, y, 각도, 크기), ...]]
        self.ghost_timer = 0.0   # 다음 잔상까지 남은 시간

    def add_puff(self, x, y):
        self.puffs.append([x, y, 0.0])

    def update(self, dt, body):
        # 나이 먹이고 수명이 다한 것은 지운다
        for p in self.puffs:
            p[2] += dt
        self.puffs = [p for p in self.puffs if p[2] < config.PUFF_LIFE]
        for g in self.ghosts:
            g[0] += dt
        self.ghosts = [g for g in self.ghosts if g[0] < config.GHOST_LIFE]
        # 질주 중이면 일정 간격으로 몸 마디의 잔상을 남긴다
        self.ghost_timer -= dt
        if body.sprint_frac() > config.GHOST_MIN_SPRINT and self.ghost_timer <= 0:
            self.ghost_timer = config.GHOST_INTERVAL
            shape = [(s.x + s.ox, s.y + s.oy, s.angle, body.seg_size(i)) for i, s in enumerate(body.segs)]
            self.ghosts.append([0.0, body.height, shape])

    def draw_ground(self, camera):
        # 바닥에 붙은 것: 흙먼지 — 착지한 곳에서 점 4개가 퍼지며 흐려진다
        for x, y, age in self.puffs:
            k = age / config.PUFF_LIFE                       # 0(막 생김) → 1(사라짐)
            r = config.PUFF_SPREAD * k
            sx, sy = camera.to_screen(x, y)
            for a in (0.4, 2.0, 3.6, 5.2):                   # 비스듬한 네 방향
                fill_rect(sx + math.cos(a) * r - 1.5, sy + math.sin(a) * r - 1.5, 3, 3,
                          config.WIKI_SUBTLE, config.PUFF_ALPHA * (1 - k))

    def draw_ghosts(self, camera):
        # 잔상: 지나간 자리의 몸 모양이 흐리게 남았다 사라진다
        for age, height, shape in self.ghosts:
            alpha = config.GHOST_ALPHA * (1 - age / config.GHOST_LIFE)
            lift = height * config.VIEW_TILT
            for x, y, angle, size in shape:
                sx, sy = camera.to_screen(x, y)
                fill_rect_rotated(sx, sy + lift, size, size, angle, config.COLOR_BODY_LIGHT, alpha)
