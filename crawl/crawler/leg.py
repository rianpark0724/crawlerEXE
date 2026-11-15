# 다리 하나 — 마디 옆의 어깨에서 바닥의 발까지 (PRD 5.2)
# 좌표는 전부 월드 좌표. 그릴 때만 camera.to_screen으로 바꾼다.
import math

import config
from ui.draw import draw_line, fill_rect


class Leg:
    def __init__(self, side):
        self.side = side                 # +1 = 머리 방향 기준 왼쪽, -1 = 오른쪽
        self.l1 = config.LEG_L1          # 허벅지 길이 (S04-5에서 다리마다 무작위)
        self.l2 = config.LEG_L2          # 종아리 길이
        self.reach = config.LEG_REACH    # 이상적 발 거리 = (l1 + l2) × reach
        self.shoulder_x = self.shoulder_y = 0.0
        self.ideal_x = self.ideal_y = 0.0
        self.foot_x = self.foot_y = 0.0  # 발 위치 (월드)
        self.knee_x = self.knee_y = 0.0  # 무릎 위치 (월드) — IK로 계산
        self.bend = -side                # 무릎 꺾임 부호 (update에서 다리 기울기에 따라 정함)

    def update(self, seg, size, tilt):
        # 어깨: 마디 중심에서 옆 방향으로 마디 크기의 절반 (마디가 돌면 같이 돈다)
        side_angle = seg.angle + self.side * math.pi / 2
        self.shoulder_x = seg.x + math.cos(side_angle) * size / 2
        self.shoulder_y = seg.y + math.sin(side_angle) * size / 2
        # 다리 방향: 옆 방향에서 tilt만큼 앞으로 기울임 (머리 쪽 다리는 앞, 꼬리 쪽 다리는 뒤로)
        leg_angle = seg.angle + self.side * (math.pi / 2 - tilt)
        # 거미형 무릎: 앞으로 기운 다리(머리 쪽)는 무릎도 앞으로, 나머지는 뒤로 꺾는다
        self.bend = -self.side if tilt > 0 else self.side
        dist = (self.l1 + self.l2) * self.reach
        self.ideal_x = self.shoulder_x + math.cos(leg_angle) * dist     # 이상적 발 위치
        self.ideal_y = self.shoulder_y + math.sin(leg_angle) * dist
        # S04-1: 발은 아직 이상적 위치에 그대로 붙어 다닌다 (S04-3에서 바닥에 고정)
        self.foot_x, self.foot_y = self.ideal_x, self.ideal_y
        self.solve_knee()

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

    def draw_shadow(self, camera):
        sx, sy = camera.to_screen(self.shoulder_x, self.shoulder_y)
        kx, ky = camera.to_screen(self.knee_x, self.knee_y)
        fx, fy = camera.to_screen(self.foot_x, self.foot_y)
        dx, dy = config.SHADOW_DX, config.SHADOW_DY
        draw_line(sx + dx, sy + dy, kx + dx, ky + dy, config.LEG_WIDTH, (0, 0, 0), config.SHADOW_ALPHA)
        draw_line(kx + dx, ky + dy, fx + dx, fy + dy, config.LEG_WIDTH_SHIN, (0, 0, 0), config.SHADOW_ALPHA)

    def draw(self, camera):
        sx, sy = camera.to_screen(self.shoulder_x, self.shoulder_y)
        kx, ky = camera.to_screen(self.knee_x, self.knee_y)
        fx, fy = camera.to_screen(self.foot_x, self.foot_y)
        draw_line(sx, sy, kx, ky, config.LEG_WIDTH, config.COLOR_LEG)          # 허벅지
        draw_line(kx, ky, fx, fy, config.LEG_WIDTH_SHIN, config.COLOR_LEG)     # 종아리 (조금 가늘게)
        j = config.LEG_JOINT
        fill_rect(kx - j / 2, ky - j / 2, j, j, config.COLOR_LEG)              # 무릎 관절
