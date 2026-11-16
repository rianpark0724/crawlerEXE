# 크롤러 효과 — 질주 잔상, 착지 흙먼지. 좌표는 월드, 그릴 때만 화면으로.
import math
import random

import config
from ui.draw import fill_rect, fill_rect_rotated, draw_line


class Effects:
    def __init__(self):
        self.puffs = []          # 흙먼지 [x, y, 나이]
        self.ghosts = []         # 잔상 [나이, 몸 높이, [(x, y, 각도, 크기), ...]]
        self.ghost_timer = 0.0   # 다음 잔상까지 남은 시간
        self.cuts = []           # 잘린 다리 CutLeg — 튕겨 날아가 바닥에서 꼼지락
        self.sparks = []         # 불꽃 [x, y, vx, vy, 나이]
        self.bits = []           # 픽셀 조각 [x, y, 높이, vx, vy, vz, 나이, 색] — 죽을 때 마디가 터진 것

    def add_puff(self, x, y):
        self.puffs.append([x, y, 0.0])

    def add_cut(self, leg, away_x, away_y):
        # 잘린 다리: (away_x, away_y) 방향으로 튕겨 날아가게 + 잘린 어깨 자리에서 불꽃
        self.cuts.append(CutLeg(leg, away_x, away_y))
        for _ in range(config.SPARK_COUNT):
            a = random.uniform(0, 2 * math.pi)
            v = config.SPARK_SPEED * random.uniform(0.5, 1.0)
            self.sparks.append([leg.shoulder_x, leg.shoulder_y, math.cos(a) * v, math.sin(a) * v, 0.0])

    def add_bits(self, x, y, z, count):
        # 데이터 조각이 쏟아진다: 사방으로 튀고 위로 솟았다 떨어지며 흐려짐 (링크 색 파랑·하늘·보라)
        colors = (config.WIKI_LINK, config.COLOR_SKY, config.WIKI_VISITED, config.COLOR_WHITE)
        for _ in range(count):
            a = random.uniform(0, 2 * math.pi)
            v = config.BIT_SPEED * random.uniform(0.4, 1.0)
            self.bits.append([x, y, z, math.cos(a) * v, math.sin(a) * v, random.uniform(60, 160), 0.0, random.choice(colors)])

    def update(self, dt, body):
        # 나이 먹이고 수명이 다한 것은 지운다
        for b in self.bits:
            b[0] += b[3] * dt
            b[1] += b[4] * dt
            b[5] -= config.CUT_GRAVITY * dt
            b[2] = max(0.0, b[2] + b[5] * dt)
            if b[2] == 0:                              # 바닥에 닿으면 미끄러지다 멈춤
                b[3] *= 0.85
                b[4] *= 0.85
            b[6] += dt
        self.bits = [b for b in self.bits if b[6] < config.BIT_LIFE]
        for c in self.cuts:
            c.update(dt)
        self.cuts = [c for c in self.cuts if c.age < config.CUT_LIFE]
        for s in self.sparks:
            s[0] += s[2] * dt
            s[1] += s[3] * dt
            s[4] += dt
        self.sparks = [s for s in self.sparks if s[4] < config.SPARK_LIFE]
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

    def draw_cuts(self, camera):
        for c in self.cuts:
            c.draw(camera)
        for x, y, z, vx, vy, vz, age, color in self.bits:    # 픽셀 조각 (높이만큼 화면 위로)
            sx, sy = camera.to_screen(x, y)
            fill_rect(sx - 1.5, sy - 1.5 + z * config.VIEW_TILT, 3, 3, color, 1 - age / config.BIT_LIFE)
        # 불꽃: 나는 방향으로 꼬리를 끄는 짧은 선, 빨강 → 흰색이 섞여 튐
        for x, y, vx, vy, age in self.sparks:
            k = age / config.SPARK_LIFE
            sx, sy = camera.to_screen(x, y)
            color = config.COLOR_RED if int(x + y) % 2 else config.COLOR_WHITE
            draw_line(sx, sy, sx - vx * config.SPARK_LEN, sy - vy * config.SPARK_LEN, 2, color, 1 - k)

    def draw_ghosts(self, camera):
        # 잔상: 지나간 자리의 몸 모양이 흐리게 남았다 사라진다
        for age, height, shape in self.ghosts:
            alpha = config.GHOST_ALPHA * (1 - age / config.GHOST_LIFE)
            lift = height * config.VIEW_TILT
            for x, y, angle, size in shape:
                sx, sy = camera.to_screen(x, y)
                fill_rect_rotated(sx, sy + lift, size, size, angle, config.COLOR_BODY_LIGHT, alpha)


class CutLeg:
    # 잘린 다리 하나: 모양(어깨·무릎·발)을 무릎 기준 상대 위치로 들고, 통째로 날아가며 돈다.
    # 공중: 위로 튀었다가 중력으로 떨어짐 → 바닥: 미끄러지다 멈추고 무릎이 떨리듯 꼼지락 → 흐려지며 사라짐
    def __init__(self, leg, away_x, away_y):
        self.x, self.y, self.z = leg.knee_x, leg.knee_y, leg.knee_z
        self.shape = [(leg.shoulder_x - leg.knee_x, leg.shoulder_y - leg.knee_y),
                      (0.0, 0.0),
                      (leg.foot_x - leg.knee_x, leg.foot_y - leg.knee_y)]
        d = math.hypot(away_x, away_y) or 1
        speed = config.CUT_FLY_SPEED * random.uniform(0.7, 1.2)
        self.vx, self.vy = away_x / d * speed, away_y / d * speed     # 위험 지점 반대쪽으로
        self.vz = config.CUT_FLY_UP * random.uniform(0.8, 1.2)
        self.rot = 0.0
        self.spin = config.CUT_SPIN * random.choice((-1, 1)) * random.uniform(0.6, 1.0)
        self.age = 0.0
        self.phase = random.uniform(0, 6)

    def update(self, dt):
        self.age += dt
        if self.z > 0 or self.vz > 0:                  # 공중: 포물선 + 회전
            self.vz -= config.CUT_GRAVITY * dt
            self.z = max(0.0, self.z + self.vz * dt)
            self.rot += self.spin * dt
            if self.z == 0:
                self.vz = 0.0
        else:                                          # 바닥: 미끄러지다 멈춤
            k = max(0.0, 1 - config.CUT_GROUND_FRICTION * dt)
            self.vx *= k
            self.vy *= k
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, camera):
        c, s = math.cos(self.rot), math.sin(self.rot)
        calm = 1 - self.age / config.CUT_LIFE
        w = math.sin(self.age * config.CUT_WIGGLE + self.phase) * config.CUT_WIGGLE_AMP * calm if self.z == 0 else 0.0
        alpha = min(1.0, (config.CUT_LIFE - self.age) / config.CUT_FADE)   # 마지막 CUT_FADE초 동안 흐려짐
        pts = []
        for i, (dx, dy) in enumerate(self.shape):
            rx, ry = dx * c - dy * s, dx * s + dy * c                  # 무릎 기준으로 회전
            if i == 1:
                rx, ry = rx + w, ry - w                                # 바닥에선 무릎이 떨림
            sx, sy = camera.to_screen(self.x + rx, self.y + ry)
            pts.append((sx, sy + self.z * config.VIEW_TILT))           # 높이만큼 화면 위로
        (ax, ay), (kx, ky), (fx, fy) = pts
        draw_line(ax, ay, kx, ky, config.LEG_WIDTH, config.COLOR_LEG, alpha)
        draw_line(kx, ky, fx, fy, config.LEG_WIDTH_SHIN, config.COLOR_LEG, alpha)
