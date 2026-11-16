# 갉아먹은 구멍 그리기 — 부러진 널빤지처럼 줄마다 다르게 뜯겨 나간 자리, 틈으로 흐르는 0과 1, 새어 나오는 데이터 조각 (화면 좌표)
# 다음 문서로 가는 구멍(갉는 중·빨려 들어갈 때)과 새 문서의 도착 구멍이 같이 쓴다.
import math
import random

import config
from ui.draw import fill_rect, fill_rect_rotated, draw_static_text

BIT_COLOR = (70, 210, 150)        # 구멍 속 0·1 (초록빛 데이터)
FLAP = (58, 62, 70)               # 나뭇결 가시 (배경보다 밝게)
FLAP_EDGE = (150, 156, 168)       # 찢긴 단면·균열


def draw_hole(cx, cy, r, t, seed=0, alpha=1.0):
    # 반지름 r 정도의 구멍을 '부러진 널빤지'처럼: 페이지를 가로 판자 줄로 보고, 줄마다 다른 길이로 뚝 부러져 나간 자리.
    # t = 흐르는 시간(0·1이 흐르고 불씨가 깜빡임), seed = 구멍마다 다른 부러진 모양
    if r < 1:
        return
    big = r > config.HOLE_BIG                               # 화면으로 번질 때는 판자를 굵게 (줄 수가 적어 빠름)
    ph = r * 0.16 if big else config.PLANK_H                # 판자 한 줄 높이
    rows = int(r / ph) + 1
    for i in range(-rows, rows + 1):
        y0 = i * ph - ph / 2                                # 이 판자 줄의 아래 (구멍 가운데 기준)
        yc = y0 + ph / 2
        if abs(yc) >= r:
            continue
        rnd = random.Random(seed * 1000 + i)               # 줄마다 고정된 무작위 (구멍이 커져도 같은 모양)
        base = r * math.sqrt(1 - (yc / r) ** 2) * config.PLANK_STRETCH   # 원 안에서 이 줄의 반너비 (가로로 길게 = 판자 결)
        left = base * rnd.uniform(0.55, 1.15)               # 왼쪽·오른쪽이 제각각 다른 길이로 부러짐
        right = base * rnd.uniform(0.55, 1.15)
        if left + right < 3:
            continue
        x0, y_ = cx - left, cy + y0
        fill_rect(x0, y_ + 0.5, left + right, ph - 1, (0, 0, 0), alpha)   # 부러져 나간 자리 (위아래 1px은 판자 틈)
        # 판자 사이 결: 구멍 양옆으로 살짝 이어지는 금
        crack = r * rnd.uniform(0.15, 0.4)
        fill_rect(x0 - crack, y_, crack, 1, FLAP_EDGE, 0.35 * alpha)
        fill_rect(cx + right, y_, crack * rnd.uniform(0.5, 1.2), 1, FLAP_EDGE, 0.35 * alpha)
        # 구멍 속 0·1: 판자 틈마다 한 줄씩, 줄마다 반대 방향으로 흐름
        if not big:
            step = 7
            flow = (t * 22 * (1 if i % 2 else -1) + rnd.random() * step) % step
            gx = -left + flow
            while gx < right - 5:
                ch = '1' if int(gx * 3 + i * 7 + t * 5) % 3 == 0 else '0'
                glow = 0.3 + 0.35 * (0.5 + 0.5 * math.sin(t * 3 + gx * 0.3 + i))
                draw_static_text(cx + gx, y_ + ph / 2 - 5, ch, 8, BIT_COLOR, glow * alpha, 'mono')
                gx += step
        # 부러진 끝: 판자 결 방향(가로)으로 뾰족한 나뭇결 가시가 구멍 안쪽으로 삐죽 (끝으로 갈수록 가늘게)
        for side, ex in ((1, x0), (-1, cx + right)):
            fill_rect(ex - (1 if side > 0 else 0), y_ + 0.5, 1, ph - 1, FLAP_EDGE, 0.8 * alpha)   # 갓 부러진 단면
            for j in range(rnd.randint(1, 3)):
                ln = ph * rnd.uniform(0.6, 1.8)
                sy = y_ + rnd.uniform(1.5, ph - 1.5)
                ang = rnd.uniform(-0.25, 0.25) + (0 if side > 0 else math.pi)
                for k in range(3):                          # 가시 하나 = 점점 짧고 가늘어지는 막대 3개
                    l2, w2 = ln * (1 - k * 0.3), ph * 0.28 * (1 - k * 0.3)
                    fill_rect_rotated(ex + math.cos(ang) * l2 / 2, sy + math.sin(ang) * l2 / 2, l2, w2, ang,
                                      FLAP, 0.95 * alpha)
            # 부러진 끝이 타들어 가듯 주황·빨강 불씨가 깜빡임
            flick = 0.5 + 0.5 * math.sin(t * rnd.uniform(8, 16) + i * 1.7 + side)
            color = config.COLOR_ORANGE if rnd.random() < 0.7 else config.COLOR_RED
            fill_rect(ex - 1.5 + side * 2, y_ + ph / 2 - 1.5, 3, 3, color, (0.25 + 0.65 * flick) * alpha)
    # 큰 구멍(빨려 들어갈 때): 화면 곳곳에 0·1이 성글게 흐름
    if big:
        rnd = random.Random(seed)
        for i in range(config.HOLE_BIG_BITS):
            bx = rnd.uniform(0, config.SCREEN_W)
            by = (rnd.uniform(0, config.SCREEN_H) - t * 40 * rnd.uniform(0.5, 1.5)) % config.SCREEN_H
            if (bx - cx) ** 2 + (by - cy) ** 2 < (r * 0.6) ** 2:
                draw_static_text(bx, by, rnd.choice('01'), 9, BIT_COLOR, 0.45 * alpha, 'mono')


class BitLeak:
    # 구멍에서 새어 나오는 0·1 조각들 (월드 좌표) — 위로 떠오르며 흩어지고 흐려진다
    def __init__(self):
        self.bits = []                                      # [x, y, vx, vy, 나이, 글자]

    def emit(self, x, y, count):
        for _ in range(count):
            self.bits.append([x + random.uniform(-6, 6), y + random.uniform(-4, 4),
                              random.uniform(-30, 30), random.uniform(40, 90), 0.0, random.choice('01')])

    def update(self, dt):
        for b in self.bits:
            b[0] += b[2] * dt
            b[1] += b[3] * dt
            b[3] -= 40 * dt                                 # 조금씩 느려짐
            b[4] += dt
        self.bits = [b for b in self.bits if b[4] < config.LEAK_LIFE]

    def draw(self, camera):
        for x, y, vx, vy, age, ch in self.bits:
            k = age / config.LEAK_LIFE
            sx, sy = camera.to_screen(x, y)
            draw_static_text(sx, sy, ch, 11, BIT_COLOR, 0.9 * (1 - k), 'mono')
