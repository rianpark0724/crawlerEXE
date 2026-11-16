# 댓글 부대 (뉴스 사이트 적) — 기사 속 '댓글 N' 둥지에서 말풍선 벌레가 기어 나와 크롤러 몸에 달라붙는다.
# 다치게 하지는 않고 방해만 한다: 붙은 만큼 느려짐. WAVE로 뛰거나 몸을 빠르게 돌리면 떨어져 나가고,
# 떨어져 어리둥절한 녀석은 발로 밟아 터뜨릴 수 있다. 좌표는 월드 좌표.
import math
import random

import config
from ui.draw import fill_rect, draw_rect, draw_line, fill_rect_rotated, draw_static_text, text_width, fill_circle

TEXTS = ['ㅋㅋㅋ', '1빠', '??', 'ㄹㅇ', '퍼가요', '기레기', 'ㅇㅈ', '광고냐', '헐', '굿', 'ㅠㅠ', '추천']
BUBBLE = (226, 228, 234)          # 말풍선 바탕
BUBBLE_TEXT = (30, 32, 38)
BUBBLE_EDGE = (120, 124, 136)


def wrap(a):
    # 각도를 -π ~ π 로
    return (a + math.pi) % (2 * math.pi) - math.pi


class Comment:
    # 말풍선 벌레 하나. state: chase 쫓아감 / stuck 몸에 붙음 / fly 떨어져 날아감(어리둥절) / pop 밟혀 터지는 중
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.text = random.choice(TEXTS)
        self.state = 'chase'
        self.t = random.uniform(0, 10)       # 다리 꼼지락·흔들림 위상
        self.seg = 0                         # 붙은 마디 번호
        self.along = self.across = 0.0       # 붙은 자리 (마디 기준: 앞뒤, 좌우)
        self.prev_angle = 0.0                # 붙은 마디의 지난 프레임 각도 (회전 속도 재기)
        self.grip = config.COMMENT_GRIP      # 남은 버티는 힘 — 빠르게 돌면 줄고, 0이 되면 떨어짐
        self.vx = self.vy = 0.0
        self.daze = 0.0                      # 떨어진 뒤 어리둥절한 남은 시간 (이동 안 함, 밟힘)
        self.spin = 0.0                      # 날아갈 때 빙글 도는 각도
        self.pop_t = 0.0

    def width(self):
        return text_width(self.text, 11) + 8

    def update(self, dt, body):
        self.t += dt
        if self.state == 'chase':
            self.chase(dt, body)
        elif self.state == 'stuck':
            self.hold(dt, body)
        elif self.state == 'fly':
            self.x += self.vx * dt
            self.y += self.vy * dt
            k = math.exp(-config.COMMENT_FRICTION * dt)          # 공기 저항: 점점 느려짐
            self.vx, self.vy = self.vx * k, self.vy * k
            self.spin += (abs(self.vx) + abs(self.vy)) * 0.02 * dt
            self.daze -= dt
            if self.daze <= 0:
                self.state = 'chase'
        elif self.state == 'pop':
            self.pop_t += dt

    def chase(self, dt, body):
        # 가장 가까운 땅에 있는 마디 쪽으로 기어감 (좌우로 살짝 갈지자)
        best, bi = None, -1
        for i, seg in enumerate(body.segs):
            if body.air(i) > 0:
                continue                                         # 공중(WAVE·낙하) 마디에는 못 붙음
            d = math.hypot(seg.x - self.x, seg.y - self.y)
            if best is None or d < best:
                best, bi = d, i
        if bi < 0:
            return
        seg = body.segs[bi]
        if best < body.seg_size(bi) / 2 + config.COMMENT_R:
            self.stick(bi, body)
            return
        a = math.atan2(seg.y - self.y, seg.x - self.x) + 0.5 * math.sin(self.t * 7)   # 갈지자
        self.x += math.cos(a) * config.COMMENT_SPEED * dt
        self.y += math.sin(a) * config.COMMENT_SPEED * dt

    def stick(self, i, body):
        # 마디 i에 달라붙음: 지금 자리를 마디 기준 좌표(앞뒤·좌우)로 기억해서 마디와 같이 움직인다
        seg = body.segs[i]
        dx, dy = self.x - seg.x, self.y - seg.y
        c, s = math.cos(-seg.angle), math.sin(-seg.angle)
        half = body.seg_size(i) / 2
        self.along = max(-half, min(half, dx * c - dy * s))      # 마디 각도만큼 거꾸로 돌려 마디 기준으로
        self.across = max(-half, min(half, dx * s + dy * c))
        self.seg, self.state = i, 'stuck'
        self.prev_angle = seg.angle
        self.grip = config.COMMENT_GRIP

    def hold(self, dt, body):
        if self.seg >= len(body.segs):
            self.fling(random.uniform(0, math.pi * 2), config.COMMENT_FLING * 0.5)   # 붙은 마디가 떨어져 나감
            return
        seg = body.segs[self.seg]
        c, s = math.cos(seg.angle), math.sin(seg.angle)
        self.x = seg.x + self.along * c - self.across * s        # 마디 기준 자리 → 월드 좌표
        self.y = seg.y + self.along * s + self.across * c
        if body.air(self.seg) > 0 and body.wave_t is not None:
            # WAVE 돌진: 몸이 튀어 오르는 순간 떨쳐짐 (돌진 반대쪽 + 바깥으로)
            out = math.atan2(self.y - seg.y, self.x - seg.x)
            self.fling(out, config.COMMENT_FLING)
            return
        if dt > 0:
            omega = abs(wrap(seg.angle - self.prev_angle)) / dt  # 붙은 마디가 도는 빠르기 (rad/s)
            self.prev_angle = seg.angle
            if omega > config.COMMENT_SPIN:
                self.grip -= (omega - config.COMMENT_SPIN) * dt  # 빠르게 돌수록 버티는 힘이 빨리 줄어듦
            else:
                self.grip = min(config.COMMENT_GRIP, self.grip + config.COMMENT_REGRIP * dt)
            if self.grip <= 0:
                # 원심력: 바깥쪽 + 도는 방향으로 날아감
                out = math.atan2(self.y - seg.y, self.x - seg.x)
                self.fling(out, config.COMMENT_FLING * 0.8)

    def fling(self, angle, speed):
        self.state = 'fly'
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.daze = config.COMMENT_DAZE

    def draw(self, camera, jitter=0.0):
        sx, sy = camera.to_screen(self.x, self.y)
        w, h = self.width(), 16
        if self.state == 'pop':
            # 터짐: 말풍선 조각 몇 개가 퍼지며 흐려짐
            k = self.pop_t / config.COMMENT_POP_TIME
            for j in range(6):
                a = j * 1.05 + self.t
                fill_rect_rotated(sx + math.cos(a) * 18 * k, sy + math.sin(a) * 18 * k, 5, 3, a, BUBBLE, 1 - k)
            return
        if self.state == 'chase':
            # 다리 세 쌍이 꼼지락
            for j in (-1, 0, 1):
                wig = 3 * math.sin(self.t * 18 + j * 2)
                lx = sx + j * (w / 3)
                draw_line(lx, sy - 4, lx - 3 + wig, sy - 11, 1, BUBBLE_EDGE)
                draw_line(lx, sy + 4, lx - 3 - wig, sy + 11, 1, BUBBLE_EDGE)
        if self.state == 'stuck':
            sx += random.uniform(-jitter, jitter)                # 버티느라 바르르
            sy += random.uniform(-jitter, jitter)
        x, y = sx - w / 2, sy - h / 2
        fill_rect(x, y, w, h, BUBBLE, 0.95)
        draw_rect(x, y, w, h, 1, BUBBLE_EDGE)
        fill_rect_rotated(x + 6, y - 2, 5, 5, math.pi / 4, BUBBLE, 0.95)   # 말풍선 꼬리
        draw_static_text(x + 4, y + 1, self.text, 11, BUBBLE_TEXT)
        if self.state == 'fly':                                  # 어리둥절: 머리 위에 빙글 도는 별
            for j in range(3):
                a = self.spin * 3 + j * 2.1
                fill_circle(sx + math.cos(a) * 10, sy + h / 2 + 5 + math.sin(a) * 3, 1.6, config.COLOR_GOLD)


class CommentNest:
    # 댓글 둥지: 기사 속 '댓글 N' 상자. 크롤러가 가까이 오면 말풍선 벌레를 하나씩 내보낸다 (총 COMMENT_TOTAL마리)
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.left = config.COMMENT_TOTAL     # 아직 안 나온 댓글 수
        self.bugs = []
        self.timer = 0.0
        self.t = 0.0

    def active(self, camera):
        pad = config.ENEMY_ACTIVE_PAD
        if self.bugs:
            return True                                          # 나온 벌레는 화면 밖까지 쫓아감
        return camera.y - pad <= self.y <= camera.y + config.SCREEN_H + pad

    def update(self, dt, footprints):
        self.t += dt                                             # 실제 움직임은 swarm (몸이 필요)

    def swarm(self, dt, body):
        # 둥지에서 벌레 내보내기 + 벌레 움직이기
        head = body.segs[0]
        near = math.hypot(head.x - self.x, head.y - self.y) < config.COMMENT_WAKE
        alive = [b for b in self.bugs if b.state != 'pop']
        self.timer -= dt
        if near and self.left > 0 and len(alive) < config.COMMENT_ALIVE and self.timer <= 0:
            self.bugs.append(Comment(self.x + random.uniform(-20, 20), self.y))
            self.left -= 1
            self.timer = config.COMMENT_SPAWN
        for b in self.bugs:
            b.update(dt, body)
        self.bugs = [b for b in self.bugs if b.state != 'pop' or b.pop_t < config.COMMENT_POP_TIME]

    def stuck_count(self):
        return sum(1 for b in self.bugs if b.state == 'stuck')

    def stomp(self, x, y):
        # 발이 x, y에 착지: 떨어져 어리둥절하거나 기어 오는 벌레를 밟으면 터진다. 터뜨렸으면 True
        for b in self.bugs:
            if b.state in ('chase', 'fly') and abs(b.x - x) < b.width() / 2 + config.COMMENT_STOMP and \
                    abs(b.y - y) < 8 + config.COMMENT_STOMP:
                b.state, b.pop_t = 'pop', 0.0
                return True
        return False

    def draw(self, camera):
        # 둥지: 말풍선 아이콘 + '댓글 N'. 벌레가 나올 때마다 숫자가 줄고, 깨어나 있으면 숨쉬듯 밝아짐
        sx, sy = camera.to_screen(self.x, self.y)
        label = '댓글 %d' % (self.left * 37 + 12)                 # 남은 수를 부풀린 가짜 댓글 수
        w = text_width(label, 13) + 30
        glow = 0.6 + 0.4 * math.sin(self.t * 4) if self.left > 0 else 0.35
        fill_rect(sx - w / 2, sy - 12, w, 24, config.WIKI_BOX_BG, 0.95)
        draw_rect(sx - w / 2, sy - 12, w, 24, 1, BUBBLE_EDGE, glow)
        fill_rect(sx - w / 2 + 7, sy - 5, 13, 10, BUBBLE, glow)  # 말풍선 아이콘
        fill_rect_rotated(sx - w / 2 + 10, sy - 6, 4, 4, math.pi / 4, BUBBLE, glow)
        draw_static_text(sx - w / 2 + 25, sy - 8, label, 13, config.WIKI_TEXT, glow)
        for b in self.bugs:
            if b.state != 'stuck':
                b.draw(camera)

    def draw_stuck(self, camera):
        # 몸에 붙은 벌레는 크롤러 위에 그린다
        for b in self.bugs:
            if b.state == 'stuck':
                k = 1 - b.grip / config.COMMENT_GRIP             # 버티는 힘이 줄수록 크게 떨림
                b.draw(camera, 0.5 + 2.5 * k)
