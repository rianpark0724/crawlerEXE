# 적 (PRD 9) — 위키 사이트의 적은 위키백과가 문서를 지키는 방식에서 따왔다. 좌표는 월드 좌표.
# 배치: 사이트 JSON의 pages.<제목>.enemies에 종류별 개수, 위치는 문서를 처음 열 때 무작위 (PRD 11.3-7)
# 그림은 코드로 그린다 — 그림 파일로 바꾸려면 각 적의 draw()만 고치면 된다.
import math
import random

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
        self.step = 0                        # 다음에 읽을 발자국 번호 (footprints 목록의 위치)
        self.speed = config.REVERT_SPEED
        self.lost_t = 0.0                    # 헤맨 시간
        self.trail = []                      # 읽은 발자국에 남긴 diff 줄 [x, y, 나이]
        self.pause = 0.0                     # 다리를 자르거나 링크를 되돌린 뒤 멈칫이 남은 시간
        self.burst = 0.0                     # 되돌릴 때 퍼지는 원이 남은 시간

    def react(self):
        # 다리를 잘랐거나 링크를 되돌림: 잠깐 멈추고 ↺가 크게 한 바퀴, 빨간 원이 퍼진다
        self.pause = self.burst = config.REVERT_PAUSE

    def wake(self, step):
        # 이 문서에서 링크가 먹힘 → 깨어나 step번 발자국부터 따라온다 (이미 추적 중이면 그대로)
        if self.state != 'track':
            self.state, self.step, self.speed = 'track', step, config.REVERT_SPEED

    def active(self, camera):
        # 화면 위아래 ENEMY_ACTIVE_PAD 안에 있을 때만 움직인다
        pad = config.ENEMY_ACTIVE_PAD
        return camera.y - pad <= self.y <= camera.y + config.SCREEN_H + pad

    def update(self, dt, footprints):
        # footprints: 이 문서의 발자국 [(x, y) 또는 None(WAVE로 끊김)] — play_mode가 착지마다 쌓는다
        self.t += dt
        awake = self.state != 'idle'
        self.spin += (config.REVERT_AWAKE_SPIN if awake else config.REVERT_IDLE_SPIN) * dt
        for tr in self.trail:
            tr[2] += dt
        self.trail = [tr for tr in self.trail if tr[2] < config.REVERT_TRAIL_LIFE]
        self.burst = max(0.0, self.burst - dt)
        if self.pause > 0:
            self.pause -= dt
            self.spin += math.pi * 2 / config.REVERT_PAUSE * dt   # 멈칫하는 동안 ↺가 한 바퀴 더
            return
        if self.state == 'track':
            self.track(dt, footprints)
        elif self.state == 'lost':
            # 두리번거림: 제자리에서 작게 흔들리다가 시간이 다 되면 제자리로
            self.lost_t += dt
            self.x += math.cos(self.t * 7) * 30 * dt
            self.y += math.sin(self.t * 5) * 30 * dt
            if self.lost_t >= config.REVERT_LOST_TIME:
                self.state = 'home'
        elif self.state == 'home':
            if self.move_to(self.home_x, self.home_y, config.REVERT_HOME_SPEED, dt):
                self.state = 'idle'

    def track(self, dt, footprints):
        # 발자국을 순서대로 되짚는다. 읽을 때마다 빨라짐. 끊김(None)을 만나면 길을 잃음
        move = self.speed * dt
        while move > 0 and self.step < len(footprints):
            spot = footprints[self.step]
            if spot is None:                                   # WAVE로 끊긴 자리
                self.state, self.lost_t = 'lost', 0.0
                self.step += 1
                return
            d = math.hypot(spot[0] - self.x, spot[1] - self.y)
            if d <= config.REVERT_READ or d <= move:            # 이 발자국에 닿음 → 읽고 다음으로
                self.x, self.y = spot
                move -= d
                self.trail.append([spot[0], spot[1], 0.0])
                self.step += 1
                self.speed = min(config.REVERT_MAX, self.speed + config.REVERT_GAIN)
            else:
                self.x += (spot[0] - self.x) / d * move
                self.y += (spot[1] - self.y) / d * move
                move = 0

    def move_to(self, x, y, speed, dt):
        # (x, y)로 speed만큼 다가감. 도착하면 True
        d = math.hypot(x - self.x, y - self.y)
        if d <= speed * dt:
            self.x, self.y = x, y
            return True
        self.x += (x - self.x) / d * speed * dt
        self.y += (y - self.y) / d * speed * dt
        return False

    def draw(self, camera):
        # 위키 아이콘 같은 둥근 원판 + 가운데 ↺(되돌리기) 화살표가 돈다. 깨어나면 빨갛게
        # 읽은 발자국: 위키 문서 비교(diff)처럼 빨강(지움)·초록(되돌림) 짧은 줄이 남았다 사라짐
        for x, y, age in self.trail:
            tx, ty = camera.to_screen(x, y)
            a = 1 - age / config.REVERT_TRAIL_LIFE
            fill_rect(tx - 7, ty + 1, 14, 2, config.COLOR_RED, 0.7 * a)
            fill_rect(tx - 7, ty - 3, 14, 2, config.COLOR_GREEN, 0.7 * a)
        sx, sy = camera.to_screen(self.x, self.y)
        awake = self.state != 'idle'
        r = config.REVERT_R
        edge = config.COLOR_RED if awake else config.WIKI_LINK
        fill_circle(sx + config.SHADOW_DX, sy + config.SHADOW_DY, r, (0, 0, 0), config.SHADOW_ALPHA)   # 그림자
        fill_circle(sx, sy, r, config.WIKI_BOX_BG)
        draw_circle(sx, sy, r, 2, edge)
        draw_revert_arrow(sx, sy, r * 0.55, self.spin, edge)
        if self.burst > 0:                                   # 되돌림·자름: 빨간 원이 퍼짐
            k = 1 - self.burst / config.REVERT_PAUSE
            draw_circle(sx, sy, r + config.REVERT_FX_R * k, 3, config.COLOR_RED, 1 - k)
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
