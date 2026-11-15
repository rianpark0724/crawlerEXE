# □ 사각형 크롤러의 몸 — 머리(segs[0])만 입력으로 움직이고 나머지 마디는 끌려온다 (PRD 5.1, 6.1)
# 좌표는 전부 월드 좌표. (S03 카메라 전까지는 화면 좌표와 같다)
import math

import config
from ui.draw import draw_line, draw_circle


class Segment:
    # 마디 하나: 중심 위치와 바라보는 방향
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.angle = angle      # 라디안. 앞(머리 쪽)을 향함


class Body:
    def __init__(self, x, y):
        # 머리는 아래(-π/2)를 보고, 나머지 마디는 그 위쪽에 SEG_SPACING 간격으로 줄지어 시작
        self.segs = [Segment(x, y + i * config.SEG_SPACING, -math.pi / 2) for i in range(config.BOX_START_SEGS)]
        self.legs = config.BOX_START_LEGS            # 다리 수 (S04 전까지 임시 값)
        self.speed = 0.0                             # 이번 프레임 머리 속도 (디버그 표시용)

    def update(self, target_x, target_y, dt):
        head = self.segs[0]

        # 1. 커서 쪽으로 회전 — 초당 BOX_TURN_SPEED rad 까지만
        want = math.atan2(target_y - head.y, target_x - head.x)     # 커서 방향
        diff = (want - head.angle + math.pi) % (2 * math.pi) - math.pi   # 돌아야 할 양 (-π ~ π)
        max_turn = config.BOX_TURN_SPEED * dt
        head.angle += max(-max_turn, min(max_turn, diff))
        head.angle = (head.angle + math.pi) % (2 * math.pi) - math.pi     # 각도를 -π ~ π 로 유지

        # 2. 바라보는 방향으로 전진
        self.speed = config.BOX_BASE_SPEED + config.BOX_SPEED_PER_PAIR * (self.legs / 2)   # 120 + 8 × 다리 쌍
        head.x += math.cos(head.angle) * self.speed * dt
        head.y += math.sin(head.angle) * self.speed * dt

        # 3. 나머지 마디는 앞 마디에 끌려온다 (거리 제약)
        self.follow()

    def follow(self):
        # 머리에서 꼬리 순서로: 마디 i를 마디 i-1에서 정확히 SEG_SPACING 떨어진 곳으로 당긴다
        for i in range(1, len(self.segs)):
            front, seg = self.segs[i - 1], self.segs[i]
            dx, dy = front.x - seg.x, front.y - seg.y
            d = math.hypot(dx, dy)
            if d == 0:
                continue
            seg.x = front.x - dx / d * config.SEG_SPACING    # 앞 마디 → 이 마디 방향으로 SEG_SPACING만큼
            seg.y = front.y - dy / d * config.SEG_SPACING
            seg.angle = math.atan2(dy, dx)                   # 앞 마디를 바라봄

    def draw(self):
        # 임시 그림: 마디 = 원, 마디 사이 연결선, 머리 방향 선 (S02-4에서 사각형으로)
        for i in range(1, len(self.segs)):
            front, seg = self.segs[i - 1], self.segs[i]
            draw_line(front.x, front.y, seg.x, seg.y, 1, config.COLOR_GRAY)
            draw_circle(seg.x, seg.y, 6, 1, config.COLOR_WHITE)
        head = self.segs[0]
        draw_circle(head.x, head.y, 8, 1, config.COLOR_WHITE)
        draw_line(head.x, head.y, head.x + math.cos(head.angle) * 14, head.y + math.sin(head.angle) * 14,
                  2, config.COLOR_ORANGE)
