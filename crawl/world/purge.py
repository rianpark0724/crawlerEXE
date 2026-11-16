# 완전 백신 NULL.EXE (S10-7e) — 한 사이트에 너무 오래(par_time 가까이) 머물면 화면 구석에 설치 창이 떠서(벽)
# 게이지가 차고, 다 차면 그 자리에서 검은 구체(블랙홀)가 나와 벽을 무시하고 천천히 쫓아온다.
# 닿으면 한 방에 끝 (WAVE 공중 마디만 피함). 나와 있는 동안 화면이 지글거린다. 좌표는 월드 좌표.
import math
import random

import config
from ui.draw import fill_rect, draw_rect, draw_line, draw_circle, fill_circle, draw_static_text, text_width
from world.enemies import ProtectedBlock

STRAND = (150, 110, 230)        # 빨려 드는 실 가닥 (보랏빛)


class Installer(ProtectedBlock):
    # 설치 창: 화면 왼쪽 아래나 오른쪽 위 구석에 뜨는 팝업. 실제 벽 (판정·밀어내기는 보호된 문단과 같음)
    def __init__(self, camera):
        self.w, self.h = config.INSTALL_W, config.INSTALL_H
        self.corner = random.choice(('bottom_left', 'top_right'))
        self.t = 0.0
        self.place(camera)

    def place(self, camera):
        # 지금 화면의 구석에 놓음 (문서를 옮기면 새 화면 구석에 다시)
        view_h = config.SCREEN_H - config.HUD_BAR_H
        if self.corner == 'bottom_left':
            self.x, self.y = 40, camera.y + 40
        else:
            self.x, self.y = config.SCREEN_W - config.SCROLL_W - self.w - 40, camera.y + view_h - self.h - 40

    def update(self, dt):
        self.t += dt

    def progress(self):
        return min(1.0, self.t / config.PURGE_INSTALL)

    def center(self):
        return self.x + self.w / 2, self.y + self.h / 2

    def draw(self, camera):
        x, y, w, h = self.x, self.y - camera.y, self.w, self.h
        fill_rect(x + 5, y - 5, w, h, (0, 0, 0), 0.5)                      # 그림자
        fill_rect(x, y, w, h, config.HUD_FIELD_BG)
        draw_rect(x, y, w, h, 1, config.WIKI_BORDER_STRONG)
        fill_rect(x, y + h - 28, w, 28, config.HUD_BAR_BG)                  # 제목 줄
        draw_static_text(x + 10, y + h - 22, '%s 설치' % config.PURGE_NAME, 13, config.WIKI_TEXT, 1.0, 'bold')
        fill_circle(x + 26, y + h - 52, 12, (0, 0, 0))                     # 아이콘: 작은 검은 구체
        draw_circle(x + 26, y + h - 52, 13, 1, STRAND)
        draw_static_text(x + 48, y + h - 60, '%s를 설치하는 중...' % config.PURGE_NAME, 13, config.WIKI_TEXT)
        k = self.progress()
        fill_rect(x + 14, y + 40, w - 28, 14, config.HUD_BAR_BG)            # 게이지
        fill_rect(x + 14, y + 40, (w - 28) * k, 14, STRAND)
        draw_rect(x + 14, y + 40, w - 28, 14, 1, config.WIKI_BORDER_STRONG)
        draw_static_text(x + 14, y + 16, '%d%%' % round(k * 100), 12, config.HUD_LABEL)
        bx = x + w - 84                                                      # 눌리지 않는 '취소' 단추
        draw_rect(bx, y + 10, 70, 22, 1, config.COLOR_GRAY)
        draw_static_text(bx + 22, y + 13, '취소', 12, config.COLOR_GRAY)


class FullVaccine:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.speed = config.PURGE_SPEED
        self.t = 0.0
        self.delay = 0.0                     # 문서를 옮긴 뒤 따라 들어오기까지 남은 시간 (이 동안 안 보이고 안 움직임)
        self.grow = 0.0                      # 설치 창에서 막 나와 커지는 중 (0 → 1)

    def enter(self, x, y):
        # 크롤러가 다른 문서로 감 → PURGE_REENTER초 뒤 같은 도착 지점에서 따라 들어옴
        self.x, self.y = x, y
        self.delay = config.PURGE_REENTER

    def present(self):
        return self.delay <= 0

    def update(self, dt, head):
        self.t += dt
        self.grow = min(1.0, self.grow + dt / config.PURGE_GROW)
        if self.delay > 0:
            self.delay -= dt
            return
        self.speed = min(config.PURGE_MAX, self.speed + config.PURGE_ACCEL * dt)   # 점점 빨라짐
        dx, dy = head.x - self.x, head.y - self.y
        d = math.hypot(dx, dy)
        if d > 1:
            self.x += dx / d * self.speed * self.grow * dt   # 벽·적 무시하고 곧장 (다 커지기 전엔 느리게)
            self.y += dy / d * self.speed * self.grow * dt

    def touches(self, body):
        # 땅에 있는 마디가 하나라도 닿았는지 (WAVE 공중 마디는 넘어감)
        if not self.present():
            return False
        r = config.PURGE_R * self.grow
        for i, seg in enumerate(body.segs):
            if body.air(i) == 0 and math.hypot(seg.x - self.x, seg.y - self.y) < r + body.seg_size(i) / 2:
                return True
        return False

    def draw(self, camera):
        # 블랙홀: 검은 구체 둘레로 실타래 같은 나선 가닥들이 계속 감기며 안으로 빨려 듦
        if not self.present():
            return
        sx, sy = self.x, self.y - camera.y
        r = config.PURGE_R * self.grow
        n = config.PURGE_STRANDS
        for k in range(n):
            # 가닥 하나 = 바깥(r×3)에서 안(r)으로 감겨 드는 나선. 시간이 지나면 통째로 돌고, 바깥쪽 시작점이 계속 안으로 흘러듦
            base = self.t * config.PURGE_SPIN + k * math.pi * 2 / n
            flow = (self.t * 1.3 + k / n) % 1.0                   # 0 → 1: 가닥이 안쪽으로 감겨 들어간 정도
            prev = None
            for j in range(14):
                u = j / 13                                         # 0 = 바깥 끝, 1 = 구체 표면
                rad = r * (3.0 - 2.0 * u) * (1 - 0.35 * flow)
                ang = base + u * 2.6 + flow * 1.5                  # 안으로 갈수록 더 감김
                px, py = sx + math.cos(ang) * rad, sy + math.sin(ang) * rad
                if prev is not None:
                    draw_line(prev[0], prev[1], px, py, 1 + u * 1.5, STRAND, (0.15 + 0.7 * u) * (1 - flow * 0.5))
                prev = (px, py)
        fill_circle(sx, sy, r * 1.08, (60, 30, 90), 0.6)                   # 테두리 빛
        fill_circle(sx, sy, r, (0, 0, 0))                                  # 검은 구체
        draw_circle(sx, sy, r + 2, 1, (200, 170, 255), 0.5 + 0.3 * math.sin(self.t * 8))
        label = config.PURGE_NAME
        draw_static_text(sx - text_width(label, 12, 'mono') / 2, sy + r * 3 + 6, label, 12, STRAND, 1.0, 'mono')


def draw_noise(strength):
    # 화면 지글거림: 가로로 어긋난 줄·색 번짐·점 노이즈 (strength 0~1, 가까울수록 셈)
    w, h = config.SCREEN_W, config.SCREEN_H - config.HUD_BAR_H
    for _ in range(int(6 + 18 * strength)):                                    # 어긋난 가로 띠
        y = random.uniform(0, h)
        bh = random.uniform(1, 4 + 8 * strength)
        color = random.choice((STRAND, config.COLOR_SKY, (255, 255, 255)))
        fill_rect(random.uniform(-40, 40), y, w, bh, color, 0.04 + 0.12 * strength)
    for _ in range(int(40 + 160 * strength)):                                  # 점 노이즈
        fill_rect(random.uniform(0, w), random.uniform(0, h), 2, 2, (255, 255, 255), 0.15 + 0.3 * strength)
    fill_rect(0, 0, 6 + 10 * strength, h, (0, 0, 0), 0.3 * strength)           # 가장자리가 어둡게 먹혀 듦
    fill_rect(w - 6 - 10 * strength, 0, 6 + 10 * strength, h, (0, 0, 0), 0.3 * strength)
