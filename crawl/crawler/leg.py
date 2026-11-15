# 다리 하나 — 마디 옆의 어깨에서 바닥의 발까지 (PRD 5.2)
# 좌표는 전부 월드 좌표. 그릴 때만 camera.to_screen으로 바꾼다.
# 걸음을 언제 시작할지는 Body가 정한다 (번갈아 걷기·동시 걸음 제한). 다리는 자세 계산과 걸음 진행만.
import math
import random

import config
from ui.draw import draw_line, fill_rect


class Leg:
    def __init__(self, side):
        self.side = side                 # +1 = 머리 방향 기준 왼쪽, -1 = 오른쪽
        self.partner = None              # 같은 마디의 반대쪽 다리 (Segment가 연결)
        # 다리마다 다른 개성 (PRD 5.2) — 같은 걸음이 없게
        self.l1 = random.uniform(*config.LEG_L1_RANGE)                  # 허벅지 길이
        self.l2 = random.uniform(*config.LEG_L2_RANGE)                  # 종아리 길이
        self.reach = random.uniform(*config.LEG_REACH_RANGE)            # 이상적 발 거리 = (l1 + l2) × reach
        self.threshold = random.uniform(*config.LEG_THRESHOLD_RANGE)    # 발이 이상적 위치에서 이만큼 벗어나면 걸음
        self.stride = 1.0                # 임계 거리 배율 (질주 중 SPRINT_STRIDE — Body가 정함)
        self.body_h = config.BODY_HEIGHT # 지금 몸(어깨) 높이 (착지 반동으로 바뀜 — Body가 정함)
        self.landed = False              # 이번 프레임에 착지했는지 (Body가 읽고 지움)
        self.lift_scale = 1.0            # 발 들어 올리는 높이 배율 (질주 중 커짐 — Body가 정함)
        self.step_time = random.uniform(*config.LEG_STEP_TIME_RANGE)    # 한 걸음에 걸리는 시간
        self.tilt_random = random.uniform(-config.LEG_TILT_RANDOM, config.LEG_TILT_RANDOM)   # 다리 방향 흔들림
        self.placed = False              # 발을 처음 바닥에 놓았는지
        self.stepping = False            # 걸음 중인지
        self.t = 0.0                     # 걸음 진행도 0 → 1
        self.from_x = self.from_y = 0.0  # 걸음 시작 위치
        self.lift = 0.0                  # 발 높이 = 들어 올린 정도 (px). 바닥에 디디면 0
        self.steps = 0                   # 걸음 수 (확인용)
        self.shoulder_x = self.shoulder_y = 0.0
        self.ideal_x = self.ideal_y = 0.0
        self.foot_x = self.foot_y = 0.0  # 발 위치 (월드)
        self.knee_x = self.knee_y = 0.0  # 무릎 위치 (월드) — IK로 계산
        self.knee_z = 0.0                # 무릎 높이 (바닥에서)
        self.bend = -side                # 무릎 꺾임 부호 (다리 기울기에 따라 정함)

    def update_pose(self, seg, size, tilt, base_tilt):
        # 어깨와 이상적 발 위치 계산 (마디가 움직이면 매 프레임 바뀐다)
        side_angle = seg.angle + self.side * math.pi / 2
        self.shoulder_x = seg.x + seg.ox + math.cos(side_angle) * size / 2   # 어깨: 마디 옆면 가운데 (몸 쏠림 포함)
        self.shoulder_y = seg.y + seg.oy + math.sin(side_angle) * size / 2
        leg_angle = seg.angle + self.side * (math.pi / 2 - tilt - self.tilt_random)   # 다리 방향: 옆에서 tilt만큼 앞으로
        # 무릎이 꺾이는 쪽: 지네형 = 모든 다리 뒤로 / 거미형 = 앞으로 기운 다리만 앞으로 (무작위 없는 tilt로 정함)
        if config.KNEE_STYLE == 'spider' and base_tilt > 0:
            self.bend = -self.side
        else:
            self.bend = self.side
        dist = (self.l1 + self.l2) * self.reach
        # 이상적 발 위치 = 어깨에서 다리 방향으로 dist + 마디 속도 × LEG_LEAD초 (가는 쪽으로 미리 딛기)
        self.ideal_x = self.shoulder_x + math.cos(leg_angle) * dist + seg.vx * config.LEG_LEAD
        self.ideal_y = self.shoulder_y + math.sin(leg_angle) * dist + seg.vy * config.LEG_LEAD
        # 이상적 위치가 다리 길이 밖이면 닿는 거리까지 당긴다 (짧은 다리 + 빠른 이동)
        ix, iy = self.ideal_x - self.shoulder_x, self.ideal_y - self.shoulder_y
        r = math.hypot(ix, iy)
        if r > self.max_reach():
            k = self.max_reach() / r
            self.ideal_x, self.ideal_y = self.shoulder_x + ix * k, self.shoulder_y + iy * k
        if not self.placed:
            self.foot_x, self.foot_y = self.ideal_x, self.ideal_y        # 처음엔 바로 이상적 위치에
            self.placed = True

    def distance(self):
        # 발이 이상적 위치에서 얼마나 벗어났나
        return math.hypot(self.ideal_x - self.foot_x, self.ideal_y - self.foot_y)

    def max_reach(self):
        # 다리를 거의 다 폈을 때 어깨~발 바닥 거리 (어깨가 body_h만큼 떠 있으니 피타고라스로)
        full = (self.l1 + self.l2) * config.LEG_MAX_STRETCH
        return math.sqrt(max(0.0, full * full - self.body_h ** 2))

    def reach_now(self):
        return math.hypot(self.foot_x - self.shoulder_x, self.foot_y - self.shoulder_y)

    def overstretched(self):
        return self.reach_now() > self.max_reach()

    def wants_step(self):
        # 이상적 위치에서 임계 거리보다 벗어났거나, 다리가 다 펴질 만큼 멀어졌으면 걷고 싶다
        return not self.stepping and (self.distance() > self.threshold_now() or self.overstretched())

    def threshold_now(self):
        # 지금 쓰는 임계 거리 = 다리 고유값 × 배율 (질주하면 커져서 보폭이 커지고 발 위치가 덜 정확해짐)
        return self.threshold * self.stride

    def start_step(self):
        self.stepping = True
        self.t = 0.0
        self.from_x, self.from_y = self.foot_x, self.foot_y

    def update_step(self, dt):
        # 순간이동처럼 너무 멀어지면 걷지 않고 바로 옮긴다
        if self.distance() > self.threshold_now() * config.LEG_TELEPORT:
            self.foot_x, self.foot_y = self.ideal_x, self.ideal_y
            self.stepping = False
            self.lift = 0.0
            return
        if not self.stepping:
            # 걸음 차례를 못 받았는데 다리가 다 펴질 만큼 멀어졌으면 발이 끌려온다 (미끄러짐 — 뼈가 늘어나 보이지 않게)
            r = self.reach_now()
            if r > self.max_reach():
                k = self.max_reach() / r
                self.foot_x = self.shoulder_x + (self.foot_x - self.shoulder_x) * k
                self.foot_y = self.shoulder_y + (self.foot_y - self.shoulder_y) * k
            return
        self.t += dt / self.step_time
        if self.t >= 1:
            self.foot_x, self.foot_y = self.ideal_x, self.ideal_y      # 착지 (S05에서 여기서 수집 판정)
            self.stepping = False
            self.lift = 0.0
            self.steps += 1
            self.landed = True
            return
        e = self.t * self.t * (3 - 2 * self.t)                         # ease-in-out: 천천히 떼고 천천히 내려놓음
        # 시작점 → "지금의" 이상적 위치로 보간 (몸이 움직여도 착지 순간 정확히 이상적 위치에 내려앉게)
        px = self.from_x + (self.ideal_x - self.from_x) * e
        py = self.from_y + (self.ideal_y - self.from_y) * e
        # 걸음 중 다리 오므리기: 발을 어깨 쪽으로 당겨 무릎이 더 접히게 (가운데에서 가장 많이, 착지 때 다시 펴짐)
        tuck = 1 - config.LEG_TUCK * math.sin(math.pi * self.t)
        self.foot_x = self.shoulder_x + (px - self.shoulder_x) * tuck
        self.foot_y = self.shoulder_y + (py - self.shoulder_y) * tuck
        self.lift = math.sin(math.pi * self.t) * config.LEG_LIFT * self.lift_scale   # 가운데에서 가장 높이 들림

    def solve_knee(self):
        # 3D 2관절 IK: 어깨(몸 높이)·발(바닥 또는 들린 높이)과 두 뼈 길이로 무릎 위치를 구한다
        sx, sy, sz = self.shoulder_x, self.shoulder_y, self.body_h
        fz = self.lift
        dx, dy, dz = self.foot_x - sx, self.foot_y - sy, fz - sz
        d = math.sqrt(dx * dx + dy * dy + dz * dz)
        if d < 1e-6:
            self.knee_x, self.knee_y, self.knee_z = sx, sy, sz + self.l1
            return
        ux, uy, uz = dx / d, dy / d, dz / d                                           # 어깨 → 발 방향 (단위 벡터)
        d = max(abs(self.l1 - self.l2) + 0.01, min(self.l1 + self.l2 - 0.01, d))     # 삼각형이 될 수 있는 범위로 제한
        alpha = math.acos((self.l1 ** 2 + d ** 2 - self.l2 ** 2) / (2 * self.l1 * d)) # 코사인 법칙: 허벅지와 어깨→발 사이 각
        # 무릎이 솟는 방향 w: 위(z)를 주로, 거미형 앞/뒤 꺾임 쪽으로 KNEE_SIDE만큼 기울인다
        h = math.hypot(dx, dy) or 1e-6
        px, py = -dy / h * self.bend, dx / h * self.bend                              # 바닥에서 어깨→발에 수직, bend 쪽
        s, c = math.sin(config.KNEE_SIDE), math.cos(config.KNEE_SIDE)
        wx, wy, wz = px * s, py * s, c
        dot = wx * ux + wy * uy + wz * uz                                             # w에서 어깨→발 방향 성분을 빼서 수직으로
        wx, wy, wz = wx - dot * ux, wy - dot * uy, wz - dot * uz
        n = math.sqrt(wx * wx + wy * wy + wz * wz) or 1e-6
        wx, wy, wz = wx / n, wy / n, wz / n
        ca, sa = math.cos(alpha), math.sin(alpha)
        self.knee_x = sx + self.l1 * (ca * ux + sa * wx)                              # 무릎 = 어깨 + l1·(cos α·u + sin α·w)
        self.knee_y = sy + self.l1 * (ca * uy + sa * wy)
        self.knee_z = sz + self.l1 * (ca * uz + sa * wz)

    def draw_shadow(self, camera):
        # 그림자: 높이만큼 빛 반대쪽으로 밀려 바닥에 생긴다 — 바닥에 닿은 발은 그림자와 붙고, 솟은 무릎은 멀어진다
        s = shadow_point(camera, self.shoulder_x, self.shoulder_y, self.body_h)
        k = shadow_point(camera, self.knee_x, self.knee_y, self.knee_z)
        f = shadow_point(camera, self.foot_x, self.foot_y, self.lift)
        draw_line(s[0], s[1], k[0], k[1], config.LEG_WIDTH, (0, 0, 0), config.SHADOW_ALPHA)
        draw_line(k[0], k[1], f[0], f[1], config.LEG_WIDTH_SHIN, (0, 0, 0), config.SHADOW_ALPHA)

    def draw(self, camera):
        sx, sy = project(camera, self.shoulder_x, self.shoulder_y, self.body_h)
        kx, ky = project(camera, self.knee_x, self.knee_y, self.knee_z)
        fx, fy = project(camera, self.foot_x, self.foot_y, self.lift)
        draw_line(sx, sy, kx, ky, config.LEG_WIDTH, config.COLOR_LEG)          # 허벅지
        draw_line(kx, ky, fx, fy, config.LEG_WIDTH_SHIN, config.COLOR_LEG)     # 종아리 (조금 가늘게)
        j = config.LEG_JOINT
        fill_rect(kx - j / 2, ky - j / 2, j, j, config.COLOR_LEG)              # 무릎 관절


def project(camera, x, y, z):
    # 높이 z인 점을 화면에: 살짝 비스듬히 내려다보는 시점이라 높을수록 화면 위로 VIEW_TILT 비율만큼
    sx, sy = camera.to_screen(x, y)
    return sx, sy + z * config.VIEW_TILT


def shadow_point(camera, x, y, z):
    # 높이 z인 점의 그림자 위치: 높이에 비례해 빛 반대쪽으로 (몸 높이에서 SHADOW_DX, SHADOW_DY만큼)
    sx, sy = camera.to_screen(x, y)
    k = z / config.BODY_HEIGHT
    return sx + config.SHADOW_DX * k, sy + config.SHADOW_DY * k
