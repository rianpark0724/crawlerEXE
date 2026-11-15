# □ 사각형 크롤러의 몸 — 머리(segs[0])만 입력으로 움직이고 나머지 마디는 끌려온다 (PRD 5.1, 6.1)
# 좌표는 전부 월드 좌표. 그릴 때만 camera.to_screen으로 바꾼다.
import math

import config
from crawler.leg import Leg
from ui.draw import fill_rect_rotated, draw_line


class Segment:
    # 마디 하나: 중심 위치와 바라보는 방향
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.angle = angle      # 라디안. 앞(머리 쪽)을 향함
        self.vx = self.vy = 0.0  # 이번 프레임 이동 속도 (px/s) — 다리가 앞으로 미리 딛는 데 사용
        self.legs = [Leg(+1), Leg(-1)]   # 다리 한 쌍 (왼쪽, 오른쪽)
        self.legs[0].partner, self.legs[1].partner = self.legs[1], self.legs[0]   # 서로 반대쪽 다리


class Body:
    def __init__(self, x, y):
        # 머리는 아래(-π/2)를 보고, 나머지 마디는 그 위쪽에 SEG_SPACING 간격으로 줄지어 시작
        self.segs = [Segment(x, y + i * config.SEG_SPACING, -math.pi / 2) for i in range(config.BOX_START_SEGS)]
        self.speed = 0.0                             # 이번 프레임 머리 속도 (디버그 표시용)
        self.update_legs(0.0)                        # 발을 처음 위치에 놓는다

    def all_legs(self):
        return [leg for seg in self.segs for leg in seg.legs]

    def seg_size(self, i):
        return config.BOX_HEAD_SIZE if i == 0 else config.BOX_SEG_SIZE

    def update(self, target_x, target_y, dt):
        before = [(seg.x, seg.y) for seg in self.segs]
        self.move_head(target_x, target_y, dt)   # 1~2. 머리 회전·전진
        self.follow()                            # 3. 나머지 마디는 앞 마디에 끌려온다 (거리 제약)
        for seg, (px, py) in zip(self.segs, before):
            if dt > 0:
                seg.vx, seg.vy = (seg.x - px) / dt, (seg.y - py) / dt   # 마디 속도 = 이번 프레임 이동량 / 시간
        self.update_legs(dt)                     # 4. 다리

    def move_head(self, target_x, target_y, dt):
        head = self.segs[0]
        dist = math.hypot(target_x - head.x, target_y - head.y)    # 커서까지 거리
        if dist < config.BOX_STOP_DIST:
            # 커서 위에 도착: 회전도 전진도 하지 않는다 (가까우면 방향이 크게 흔들려 떨기 때문)
            self.speed = 0.0
            return

        # 1. 커서 쪽으로 회전 — 초당 BOX_TURN_SPEED rad 까지만
        want = math.atan2(target_y - head.y, target_x - head.x)     # 커서 방향
        diff = (want - head.angle + math.pi) % (2 * math.pi) - math.pi   # 돌아야 할 양 (-π ~ π)
        max_turn = config.BOX_TURN_SPEED * dt
        head.angle += max(-max_turn, min(max_turn, diff))
        head.angle = (head.angle + math.pi) % (2 * math.pi) - math.pi     # 각도를 -π ~ π 로 유지

        # 2. 바라보는 방향으로 전진
        self.speed = config.BOX_BASE_SPEED + config.BOX_SPEED_PER_PAIR * (len(self.all_legs()) / 2)   # 120 + 8 × 다리 쌍
        self.speed = min(self.speed, dist * config.BOX_SLOW_FACTOR)        # 커서 가까이 가면 감속
        self.speed *= max(config.BOX_MIN_FACING, math.cos(diff))           # 커서와 다른 방향을 볼수록 느리게 (뒤돌 때 거의 제자리 회전)
        head.x += math.cos(head.angle) * self.speed * dt
        head.y += math.sin(head.angle) * self.speed * dt

    def update_legs(self, dt):
        # (1) 어깨·이상적 위치: 다리 기울기는 머리 마디 +LEG_TILT(앞) → 꼬리 마디 -LEG_TILT(뒤)로 고르게
        n = len(self.segs)
        for i, seg in enumerate(self.segs):
            tilt = config.LEG_TILT * (1 - 2 * i / (n - 1)) if n > 1 else 0.0
            for leg in seg.legs:
                leg.update_pose(seg, self.seg_size(i), tilt)
        legs = self.all_legs()
        # (2) 걷는 중인 다리 진행 (착지·순간이동 처리)
        for leg in legs:
            leg.update_step(dt)
        # (3) 새 걸음 시작: 이상적 위치에서 가장 멀리 벗어난 다리부터.
        #     동시에 걷는 다리는 전체의 절반까지, 같은 마디 반대쪽 다리가 걷는 중이면 기다린다 (번갈아 걷기)
        stepping = sum(1 for leg in legs if leg.stepping)
        limit = max(1, len(legs) // 2)
        waiting = [leg for leg in legs if leg.wants_step()]
        waiting.sort(key=lambda leg: leg.distance(), reverse=True)
        for leg in waiting:
            if stepping >= limit:
                break
            if leg.partner.stepping:
                continue
            leg.start_step()
            stepping += 1
        # (4) 무릎
        for leg in legs:
            leg.solve_knee()

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

    def draw(self, camera):
        # 1. 그림자를 먼저 전부 깐다 (몸·다리 위에 그림자가 겹치지 않게)
        for leg in self.all_legs():
            leg.draw_shadow(camera)
        for i, seg in enumerate(self.segs):
            size = self.seg_size(i)
            sx, sy = camera.to_screen(seg.x, seg.y)
            fill_rect_rotated(sx + config.SHADOW_DX, sy + config.SHADOW_DY, size + 2, size + 2, seg.angle,
                              (0, 0, 0), config.SHADOW_ALPHA)
        # 2. 다리 (마디 아래에)
        for leg in self.all_legs():
            leg.draw(camera)
        # 3. 마디: 꼬리부터 그려서 머리가 맨 위에 오게 한다
        for i in range(len(self.segs) - 1, -1, -1):
            seg = self.segs[i]
            size = self.seg_size(i)
            sx, sy = camera.to_screen(seg.x, seg.y)
            self.draw_segment(sx, sy, size, seg.angle)
        # 머리 앞쪽 가장자리 근처에 주황 점 — 어느 쪽이 앞인지 표시
        head = self.segs[0]
        hx, hy = camera.to_screen(head.x, head.y)
        r = config.BOX_HEAD_SIZE / 2 - config.BOX_EYE_SIZE / 2 - 1     # 중심에서 점까지 거리
        fill_rect_rotated(hx + math.cos(head.angle) * r, hy + math.sin(head.angle) * r,
                          config.BOX_EYE_SIZE, config.BOX_EYE_SIZE, head.angle, config.COLOR_ORANGE)

    def draw_segment(self, x, y, size, angle):
        # 입체감 있는 사각 마디 하나 (화면 좌표). 빛은 LIGHT_DIR(왼쪽 위)에서 온다고 본다
        lx, ly = config.LIGHT_DIR
        # 반투명 몸 채움
        fill_rect_rotated(x, y, size, size, angle, config.COLOR_BODY, config.BOX_BODY_ALPHA)
        # 윗면 하이라이트: 작은 밝은 사각형을 빛 쪽으로 살짝 옮겨 겹침 → 볼록해 보임
        hs = size * config.BOX_HIGHLIGHT_SIZE
        shift = size * config.BOX_HIGHLIGHT_SHIFT
        fill_rect_rotated(x + lx * shift, y + ly * shift, hs, hs, angle, config.COLOR_BODY_LIGHT, config.BOX_HIGHLIGHT_ALPHA)
        # 테두리: 네 변을 각각 빛을 받는 정도에 따라 밝게/어둡게
        c, s = math.cos(angle), math.sin(angle)
        h = size / 2
        corners = []
        for px, py in [(-h, -h), (h, -h), (h, h), (-h, h)]:
            corners.append((x + px * c - py * s, y + px * s + py * c))    # 회전 변환
        for k in range(4):
            x1, y1 = corners[k]
            x2, y2 = corners[(k + 1) % 4]
            nx, ny = (y2 - y1) / size, -(x2 - x1) / size          # 변의 바깥쪽 방향 (단위 벡터)
            lit = (nx * lx + ny * ly + 1) / 2                     # 빛을 받는 정도 0(등진 쪽) ~ 1(정면)
            f = config.EDGE_DARK + (1 - config.EDGE_DARK) * lit   # 밝기 배율
            color = (int(config.COLOR_WHITE[0] * f), int(config.COLOR_WHITE[1] * f), int(config.COLOR_WHITE[2] * f))
            draw_line(x1, y1, x2, y2, 1, color)
