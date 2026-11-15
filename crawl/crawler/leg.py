# 다리 하나 — 마디 옆의 어깨에서 바닥의 발까지 (PRD 5.2)
# 좌표는 전부 월드 좌표. 그릴 때만 camera.to_screen으로 바꾼다.
# 걸음을 언제 시작할지는 Body가 정한다 (번갈아 걷기·동시 걸음 제한). 다리는 자세 계산과 걸음 진행만.
import math

import config
from ui.draw import draw_line, fill_rect


class Leg:
    def __init__(self, side):
        self.side = side                 # +1 = 머리 방향 기준 왼쪽, -1 = 오른쪽
        self.partner = None              # 같은 마디의 반대쪽 다리 (Segment가 연결)
        self.l1 = config.LEG_L1          # 허벅지 길이 (S04-5에서 다리마다 무작위)
        self.l2 = config.LEG_L2          # 종아리 길이
        self.reach = config.LEG_REACH    # 이상적 발 거리 = (l1 + l2) × reach
        self.threshold = config.LEG_THRESHOLD   # 발이 이상적 위치에서 이만큼 벗어나면 걸음
        self.step_time = config.LEG_STEP_TIME   # 한 걸음에 걸리는 시간
        self.placed = False              # 발을 처음 바닥에 놓았는지
        self.stepping = False            # 걸음 중인지
        self.t = 0.0                     # 걸음 진행도 0 → 1
        self.from_x = self.from_y = 0.0  # 걸음 시작 위치
        self.lift = 0.0                  # 발을 들어 올린 높이 (그리기용, px)
        self.steps = 0                   # 걸음 수 (확인용)
        self.shoulder_x = self.shoulder_y = 0.0
        self.ideal_x = self.ideal_y = 0.0
        self.foot_x = self.foot_y = 0.0  # 발 위치 (월드)
        self.knee_x = self.knee_y = 0.0  # 무릎 위치 (월드) — IK로 계산
        self.bend = -side                # 무릎 꺾임 부호 (다리 기울기에 따라 정함)

    def update_pose(self, seg, size, tilt):
        # 어깨와 이상적 발 위치 계산 (마디가 움직이면 매 프레임 바뀐다)
        side_angle = seg.angle + self.side * math.pi / 2
        self.shoulder_x = seg.x + math.cos(side_angle) * size / 2      # 어깨: 마디 옆면 가운데
        self.shoulder_y = seg.y + math.sin(side_angle) * size / 2
        leg_angle = seg.angle + self.side * (math.pi / 2 - tilt)        # 다리 방향: 옆에서 tilt만큼 앞으로
        self.bend = -self.side if tilt > 0 else self.side               # 거미형 무릎: 앞 다리는 앞으로, 나머지는 뒤로
        dist = (self.l1 + self.l2) * self.reach
        # 이상적 발 위치 = 어깨에서 다리 방향으로 dist + 마디 속도 × LEG_LEAD초 (가는 쪽으로 미리 딛기)
        self.ideal_x = self.shoulder_x + math.cos(leg_angle) * dist + seg.vx * config.LEG_LEAD
        self.ideal_y = self.shoulder_y + math.sin(leg_angle) * dist + seg.vy * config.LEG_LEAD
        if not self.placed:
            self.foot_x, self.foot_y = self.ideal_x, self.ideal_y        # 처음엔 바로 이상적 위치에
            self.placed = True

    def distance(self):
        # 발이 이상적 위치에서 얼마나 벗어났나
        return math.hypot(self.ideal_x - self.foot_x, self.ideal_y - self.foot_y)

    def wants_step(self):
        return not self.stepping and self.distance() > self.threshold

    def start_step(self):
        self.stepping = True
        self.t = 0.0
        self.from_x, self.from_y = self.foot_x, self.foot_y

    def update_step(self, dt):
        # 순간이동처럼 너무 멀어지면 걷지 않고 바로 옮긴다
        if self.distance() > self.threshold * config.LEG_TELEPORT:
            self.foot_x, self.foot_y = self.ideal_x, self.ideal_y
            self.stepping = False
            self.lift = 0.0
            return
        if not self.stepping:
            return
        self.t += dt / self.step_time
        if self.t >= 1:
            self.foot_x, self.foot_y = self.ideal_x, self.ideal_y      # 착지 (S05에서 여기서 수집 판정)
            self.stepping = False
            self.lift = 0.0
            self.steps += 1
            return
        e = self.t * self.t * (3 - 2 * self.t)                         # ease-in-out: 천천히 떼고 천천히 내려놓음
        # 시작점 → "지금의" 이상적 위치로 보간 (몸이 움직여도 착지 순간 정확히 이상적 위치에 내려앉게)
        px = self.from_x + (self.ideal_x - self.from_x) * e
        py = self.from_y + (self.ideal_y - self.from_y) * e
        # 걸음 중 다리 오므리기: 발을 어깨 쪽으로 당겨 무릎이 더 접히게 (가운데에서 가장 많이, 착지 때 다시 펴짐)
        tuck = 1 - config.LEG_TUCK * math.sin(math.pi * self.t)
        self.foot_x = self.shoulder_x + (px - self.shoulder_x) * tuck
        self.foot_y = self.shoulder_y + (py - self.shoulder_y) * tuck
        self.lift = math.sin(math.pi * self.t) * config.LEG_LIFT       # 가운데에서 가장 높이 들림

    def solve_knee(self):
        # 2관절 IK: 어깨·발 위치와 두 뼈 길이로 무릎 위치를 구한다 (코사인 법칙)
        dx, dy = self.foot_x - self.shoulder_x, self.foot_y - self.shoulder_y
        d = math.hypot(dx, dy)
        d = max(abs(self.l1 - self.l2) + 0.01, min(self.l1 + self.l2 - 0.01, d))   # 삼각형이 될 수 있는 범위로 제한
        theta = math.atan2(dy, dx)                                                    # 어깨 → 발 방향
        alpha = math.acos((self.l1 ** 2 + d ** 2 - self.l2 ** 2) / (2 * self.l1 * d)) # 어깨에서 본 허벅지와 어깨→발 사이 각
        a = theta + self.bend * alpha                                                 # bend 부호로 무릎이 앞/뒤 어느 쪽으로 꺾일지
        self.knee_x = self.shoulder_x + self.l1 * math.cos(a)
        self.knee_y = self.shoulder_y + self.l1 * math.sin(a)

    def lifted(self, camera):
        # 그릴 위치 (화면 좌표). 들린 만큼 무릎·발을 그림자 반대쪽(빛 쪽)으로 옮긴다 — 그림자는 바닥에 남아 떠 보임
        ux, uy = -config.SHADOW_DX, -config.SHADOW_DY
        n = math.hypot(ux, uy)
        ox, oy = ux / n * self.lift, uy / n * self.lift
        sx, sy = camera.to_screen(self.shoulder_x, self.shoulder_y)
        kx, ky = camera.to_screen(self.knee_x, self.knee_y)
        fx, fy = camera.to_screen(self.foot_x, self.foot_y)
        return sx, sy, kx + ox * 0.6, ky + oy * 0.6, fx + ox, fy + oy

    def draw_shadow(self, camera):
        # 그림자는 바닥(들어 올리기 전 위치)에
        sx, sy = camera.to_screen(self.shoulder_x, self.shoulder_y)
        kx, ky = camera.to_screen(self.knee_x, self.knee_y)
        fx, fy = camera.to_screen(self.foot_x, self.foot_y)
        dx, dy = config.SHADOW_DX, config.SHADOW_DY
        draw_line(sx + dx, sy + dy, kx + dx, ky + dy, config.LEG_WIDTH, (0, 0, 0), config.SHADOW_ALPHA)
        draw_line(kx + dx, ky + dy, fx + dx, fy + dy, config.LEG_WIDTH_SHIN, (0, 0, 0), config.SHADOW_ALPHA)

    def draw(self, camera):
        sx, sy, kx, ky, fx, fy = self.lifted(camera)
        draw_line(sx, sy, kx, ky, config.LEG_WIDTH, config.COLOR_LEG)          # 허벅지
        draw_line(kx, ky, fx, fy, config.LEG_WIDTH_SHIN, config.COLOR_LEG)     # 종아리 (조금 가늘게)
        j = config.LEG_JOINT
        fill_rect(kx - j / 2, ky - j / 2, j, j, config.COLOR_LEG)              # 무릎 관절
