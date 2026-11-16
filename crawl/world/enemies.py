# 적 (PRD 9) — 위키 사이트의 적은 위키백과가 문서를 지키는 방식에서 따왔다. 좌표는 월드 좌표.
# 배치: 사이트 JSON의 pages.<제목>.enemies에 종류별 개수, 위치는 문서를 처음 열 때 무작위 (PRD 11.3-7)
# 그림은 코드로 그린다 — 그림 파일로 바꾸려면 각 적의 draw()만 고치면 된다.
import math

import config
from ui.draw import fill_circle, draw_circle, draw_line, fill_rect
from world.objects import random_spot


class RevertBot:
    # 되돌리기 봇: 평소엔 제자리. 링크를 먹으면 깨어나 크롤러의 발자국을 되짚어 따라오고(S09-2),
    # 먹힌 링크 자리를 지나면 그 링크를 되돌린다(S09-3)
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.home_x, self.home_y = x, y      # 제자리 (길을 잃으면 돌아옴)
        self.state = 'idle'                  # idle 대기 / track 추적 / lost 헤맴 / home 복귀
        self.spin = 0.0                      # ↺ 화살표 각도
        self.t = 0.0

    def active(self, camera):
        # 화면 위아래 ENEMY_ACTIVE_PAD 안에 있을 때만 움직인다
        pad = config.ENEMY_ACTIVE_PAD
        return camera.y - pad <= self.y <= camera.y + config.SCREEN_H + pad

    def update(self, dt):
        self.t += dt
        awake = self.state != 'idle'
        self.spin += (config.REVERT_AWAKE_SPIN if awake else config.REVERT_IDLE_SPIN) * dt

    def draw(self, camera):
        # 위키 아이콘 같은 둥근 원판 + 가운데 ↺(되돌리기) 화살표가 돈다. 깨어나면 빨갛게
        sx, sy = camera.to_screen(self.x, self.y)
        awake = self.state != 'idle'
        r = config.REVERT_R
        edge = config.COLOR_RED if awake else config.WIKI_LINK
        fill_circle(sx + config.SHADOW_DX, sy + config.SHADOW_DY, r, (0, 0, 0), config.SHADOW_ALPHA)   # 그림자
        fill_circle(sx, sy, r, config.WIKI_BOX_BG)
        draw_circle(sx, sy, r, 2, edge)
        draw_revert_arrow(sx, sy, r * 0.55, self.spin, edge)
        if awake:                                            # 깨어나면 바깥 고리가 숨쉬듯
            pulse = 0.5 + 0.5 * math.sin(self.t * 10)
            draw_circle(sx, sy, r + 4 + 2 * pulse, 1, config.COLOR_RED, 0.4)


def draw_revert_arrow(x, y, r, angle, color, width=2):
    # ↺ 되돌리기 화살표: 원호 3/4 + 끝에 화살촉 (반시계로 도는 모양)
    steps = 10
    sweep = math.pi * 1.5
    pts = [(x + math.cos(angle + sweep * i / steps) * r, y + math.sin(angle + sweep * i / steps) * r) for i in range(steps + 1)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        draw_line(x1, y1, x2, y2, width, color)
    ex, ey = pts[-1]
    a = angle + sweep + math.pi / 2                          # 원호 끝에서 진행 방향 (반시계)
    for side in (-1, 1):                                     # 화살촉 두 날개
        wa = a + math.pi + side * 0.6
        draw_line(ex, ey, ex + math.cos(wa) * r * 0.7, ey + math.sin(wa) * r * 0.7, width, color)


KINDS = {'revert': RevertBot}


def place_enemies(page, counts):
    # 문서 본문 안 무작위 위치에 적을 놓는다 (counts: {'revert': 1} 같은 종류별 개수)
    enemies = []
    for kind, n in counts.items():
        for _ in range(n):
            spot = random_spot(page, [(e.x, e.y) for e in enemies], config.ENEMY_SPAWN_GAP, config.ENEMY_APART)
            if spot is not None:
                enemies.append(KINDS[kind](*spot))
    return enemies
