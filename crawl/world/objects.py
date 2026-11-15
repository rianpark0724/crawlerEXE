# 페이지 위 오브젝트 — 다리 파츠 (PRD 7, 8). 좌표는 월드 좌표.
# 배치: 사이트 JSON의 pages.<제목>.parts에 종류별 개수, 위치는 문서를 처음 열 때 무작위 (PRD 11.3-7)
import math
import random

import config
from crawler.body import draw_segment
from ui.draw import fill_rect, fill_rect_rotated, draw_line, draw_circle


class LegPart:
    # 떨어져 나온 크롤러 마디 하나 + 다리 한 쌍 — 발로 밟으면 크롤러가 자란다 (마디 +1, 다리 +2)
    # 크롤러와 같은 그리기(draw_segment)·다리 색을 써서 '크롤러 조각'으로 보이게
    def __init__(self, x, y, kind='plain'):
        self.x, self.y = x, y
        self.angle = random.uniform(-math.pi, math.pi)   # 놓인 방향은 제각각
        self.kind = kind                         # plain (능력 파츠 long·spike·mag는 S14)
        self.taken = False
        self.t = random.uniform(0, 10)           # 꼼지락 박자를 파츠마다 다르게

    def update(self, dt):
        self.t += dt

    def hit(self, x, y):
        # 발 착지 (x, y)가 상자 중심 PART_PICK_R 안인지
        return not self.taken and math.hypot(x - self.x, y - self.y) <= config.PART_PICK_R

    def draw(self, camera):
        sx, sy = camera.to_screen(self.x, self.y)
        size = config.BOX_SEG_SIZE
        lift = config.BODY_HEIGHT * config.VIEW_TILT       # 크롤러 마디처럼 몸 높이만큼 떠 있음
        fill_rect_rotated(sx + config.SHADOW_DX, sy + config.SHADOW_DY, size + 2, size + 2, self.angle, (0, 0, 0), config.SHADOW_ALPHA)
        # 다리 한 쌍: 마디 옆면 → 솟은 무릎 → 바닥의 발. 박자에 맞춰 앞뒤로 꼼지락 (좌우가 엇갈리게)
        for side in (+1, -1):
            out = self.angle + side * math.pi / 2                                  # 옆 방향
            d = out + side * config.PART_WIGGLE_ANGLE * math.sin(self.t * config.PART_WIGGLE + side)
            shx, shy = sx + math.cos(out) * size / 2, sy + lift + math.sin(out) * size / 2     # 어깨
            kx = sx + math.cos(d) * config.PART_REACH * 0.55
            ky = sy + math.sin(d) * config.PART_REACH * 0.55 + config.PART_KNEE_Z * config.VIEW_TILT   # 무릎 (위로 솟음)
            fx, fy = sx + math.cos(d) * config.PART_REACH, sy + math.sin(d) * config.PART_REACH        # 발 (바닥)
            draw_line(shx, shy, kx, ky, config.LEG_WIDTH, config.COLOR_LEG)
            draw_line(kx, ky, fx, fy, config.LEG_WIDTH_SHIN, config.COLOR_LEG)
            j = config.LEG_JOINT
            fill_rect(kx - j / 2, ky - j / 2, j, j, config.COLOR_LEG)
        draw_segment(sx, sy + lift, size, self.angle)        # 크롤러와 똑같은 마디
        # 은은한 고리: 주울 수 있는 물건이라는 표시
        pulse = 0.5 + 0.5 * math.sin(self.t * 3)
        draw_circle(sx, sy + lift, config.PART_PICK_R + 4 + 2 * pulse, 1, config.COLOR_BODY_LIGHT, 0.2 + 0.2 * pulse)


def place_parts(page, counts):
    # 문서 본문 안 무작위 위치에 파츠를 놓는다. 링크 단어·목표 키워드·출구 상자·시작 위치 근처는 피한다
    # counts: {'plain': 1} 같은 종류별 개수
    avoid = config.PART_AVOID
    boxes = [(x, y, w, h) for x, y, w, h, *_ in page.links] + list(page.goals) + [page.exit_rect]
    sx, sy = page.spawn()
    top = sy - config.PART_SPAWN_GAP                       # 시작 위치 아래부터
    bottom = page.exit_rect[1] + page.exit_rect[3] + avoid  # 출구 상자 위까지
    left = config.WIKI_CONTENT_X + avoid
    right = config.WIKI_CONTENT_X + config.WIKI_CONTENT_W - avoid
    parts = []
    for kind, n in counts.items():
        for _ in range(n):
            for _try in range(200):                       # 조건에 맞는 자리를 찾을 때까지 다시 뽑기
                x, y = random.uniform(left, right), random.uniform(bottom, top)
                near_box = any(bx - avoid <= x <= bx + bw + avoid and by - avoid <= y <= by + bh + avoid
                               for bx, by, bw, bh in boxes)
                near_part = any(math.hypot(x - p.x, y - p.y) < avoid * 3 for p in parts)
                if not near_box and not near_part:
                    parts.append(LegPart(x, y, kind))
                    break
    return parts
