# 완전 백신 (S10-7e) — 한 사이트에 너무 오래(par_time 넘게) 머물면 나타나 벽을 무시하고 천천히 쫓아온다.
# 닿으면 한 방에 끝 (WAVE 공중 마디만 피함). 나와 있는 동안 화면이 지글거린다. 좌표는 월드 좌표.
import math
import random

import config
from ui.draw import fill_rect, draw_line, draw_circle, fill_circle, draw_static_text, text_width


class FullVaccine:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.speed = config.PURGE_SPEED
        self.t = 0.0
        self.delay = 0.0                     # 문서를 옮긴 뒤 따라 들어오기까지 남은 시간 (이 동안 안 보이고 안 움직임)

    def enter(self, x, y):
        # 크롤러가 다른 문서로 감 → PURGE_REENTER초 뒤 같은 도착 지점에서 따라 들어옴
        self.x, self.y = x, y
        self.delay = config.PURGE_REENTER

    def present(self):
        return self.delay <= 0

    def update(self, dt, head):
        self.t += dt
        if self.delay > 0:
            self.delay -= dt
            return
        self.speed = min(config.PURGE_MAX, self.speed + config.PURGE_ACCEL * dt)   # 점점 빨라짐
        dx, dy = head.x - self.x, head.y - self.y
        d = math.hypot(dx, dy)
        if d > 1:
            self.x += dx / d * self.speed * dt               # 벽·적 무시하고 곧장
            self.y += dy / d * self.speed * dt

    def touches(self, body):
        # 땅에 있는 마디가 하나라도 닿았는지 (WAVE 공중 마디는 넘어감)
        if not self.present():
            return False
        for i, seg in enumerate(body.segs):
            if body.air(i) == 0 and math.hypot(seg.x - self.x, seg.y - self.y) < config.PURGE_R + body.seg_size(i) / 2:
                return True
        return False

    def draw(self, camera):
        if not self.present():
            return
        sx, sy = self.x, self.y - camera.y
        r = config.PURGE_R
        pulse = 0.5 + 0.5 * math.sin(self.t * 6)
        draw_circle(sx, sy, r + 10 + 6 * pulse, 2, config.COLOR_RED, 0.5)        # 바깥 고리 (숨쉬듯)
        fill_circle(sx, sy, r, (90, 10, 16))
        fill_circle(sx, sy, r * 0.6, config.COLOR_RED)
        for k in range(3):                                                      # 도는 검사 막대
            a = self.t * 3 + k * math.pi * 2 / 3
            draw_line(sx, sy, sx + math.cos(a) * (r + 6), sy + math.sin(a) * (r + 6), 2, (255, 200, 200), 0.8)
        fill_rect(sx - 3, sy - 10, 6, 20, (255, 235, 235))                      # 가운데 +
        fill_rect(sx - 10, sy - 3, 20, 6, (255, 235, 235))
        label = 'VACCINE.EXE'
        draw_static_text(sx - text_width(label, 12, 'mono') / 2, sy + r + 18, label, 12, config.COLOR_RED, 1.0, 'mono')


def draw_noise(strength):
    # 화면 지글거림: 가로로 어긋난 줄·색 번짐·점 노이즈 (strength 0~1, 가까울수록 셈)
    w, h = config.SCREEN_W, config.SCREEN_H - config.HUD_BAR_H
    for _ in range(int(6 + 18 * strength)):                                    # 어긋난 가로 띠
        y = random.uniform(0, h)
        bh = random.uniform(1, 4 + 8 * strength)
        color = random.choice((config.COLOR_RED, config.COLOR_SKY, (255, 255, 255)))
        fill_rect(random.uniform(-40, 40), y, w, bh, color, 0.04 + 0.12 * strength)
    for _ in range(int(40 + 160 * strength)):                                  # 점 노이즈
        fill_rect(random.uniform(0, w), random.uniform(0, h), 2, 2, (255, 255, 255), 0.15 + 0.3 * strength)
    fill_rect(0, 0, 6 + 10 * strength, h, config.COLOR_RED, 0.15 * strength)    # 가장자리 붉은 기운
    fill_rect(w - 6 - 10 * strength, 0, 6 + 10 * strength, h, config.COLOR_RED, 0.15 * strength)
