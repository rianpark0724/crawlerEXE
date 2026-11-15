# 다리 하나 — 마디 옆의 어깨에서 바닥의 발까지 (PRD 5.2)
# 좌표는 전부 월드 좌표. 그릴 때만 camera.to_screen으로 바꾼다.
import math

import config
from ui.draw import draw_line


class Leg:
    def __init__(self, side):
        self.side = side                 # +1 = 머리 방향 기준 왼쪽, -1 = 오른쪽
        self.l1 = config.LEG_L1          # 허벅지 길이 (S04-5에서 다리마다 무작위)
        self.l2 = config.LEG_L2          # 종아리 길이
        self.reach = config.LEG_REACH    # 이상적 발 거리 = (l1 + l2) × reach
        self.shoulder_x = self.shoulder_y = 0.0
        self.ideal_x = self.ideal_y = 0.0
        self.foot_x = self.foot_y = 0.0  # 발 위치 (월드)

    def update(self, seg, size, tilt):
        # 어깨: 마디 중심에서 옆 방향으로 마디 크기의 절반 (마디가 돌면 같이 돈다)
        side_angle = seg.angle + self.side * math.pi / 2
        self.shoulder_x = seg.x + math.cos(side_angle) * size / 2
        self.shoulder_y = seg.y + math.sin(side_angle) * size / 2
        # 다리 방향: 옆 방향에서 tilt만큼 앞으로 기울임 (머리 쪽 다리는 앞, 꼬리 쪽 다리는 뒤로)
        leg_angle = seg.angle + self.side * (math.pi / 2 - tilt)
        dist = (self.l1 + self.l2) * self.reach
        self.ideal_x = self.shoulder_x + math.cos(leg_angle) * dist     # 이상적 발 위치
        self.ideal_y = self.shoulder_y + math.sin(leg_angle) * dist
        # S04-1: 발은 아직 이상적 위치에 그대로 붙어 다닌다 (S04-3에서 바닥에 고정)
        self.foot_x, self.foot_y = self.ideal_x, self.ideal_y

    def draw_shadow(self, camera):
        sx, sy = camera.to_screen(self.shoulder_x, self.shoulder_y)
        fx, fy = camera.to_screen(self.foot_x, self.foot_y)
        dx, dy = config.SHADOW_DX, config.SHADOW_DY
        draw_line(sx + dx, sy + dy, fx + dx, fy + dy, config.LEG_WIDTH, (0, 0, 0), config.SHADOW_ALPHA)

    def draw(self, camera):
        sx, sy = camera.to_screen(self.shoulder_x, self.shoulder_y)
        fx, fy = camera.to_screen(self.foot_x, self.foot_y)
        draw_line(sx, sy, fx, fy, config.LEG_WIDTH, config.COLOR_LEG)     # S04-1: 어깨 → 발 직선
