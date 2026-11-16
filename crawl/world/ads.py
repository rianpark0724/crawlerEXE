# 광고 팝업 (뉴스 사이트 적) — 크롤러가 갈 자리에 광고창 그림자가 먼저 깔리고, 쾅 떨어진다.
# 떨어지는 순간 아래 깔린 다리·마디는 맞고(바깥으로 튕김), WAVE 공중이면 피한다.
# 떨어진 광고는 한동안 벽으로 남아 길을 막는다. 오른쪽 위 닫기 칸을 발로 2번 디디면 닫힌다. 좌표는 월드 좌표.
import math
import random

import config
from ui.draw import fill_rect, draw_rect, draw_line, draw_static_text, text_width
from world.enemies import ProtectedBlock

AD_LINES = [('축하합니다!', '1,000,000번째 방문자'), ('단 하루!', '전 품목 90% 할인'), ('지금 클릭!', '무료 경품 당첨'),
            ('이 기사 대신', '이걸 보세요'), ('의사들이 숨긴', '놀라운 비법'), ('구독하면', '광고 없이 보기')]
AD_BG = (24, 22, 30)
AD_YELLOW = (250, 210, 40)
AD_PINK = (255, 80, 150)


class Ad(ProtectedBlock):
    # 광고 하나. state: warn 그림자 경고 / slam 떨어지는 순간(맞음) / stay 벽 / close 닫히는 중 / gone
    # 벽 판정(rect)·밀어낼 방향(push_dir)은 보호된 문단과 같다
    def __init__(self, x, y):
        w, h = config.AD_W, config.AD_H
        self.x, self.y, self.w, self.h = x - w / 2, y - h / 2, w, h
        self.state, self.t = 'warn', 0.0
        self.lines = random.choice(AD_LINES)
        self.close_n = 0                     # 닫기 칸을 디딘 횟수
        self.close_t = 0.0                   # 마지막으로 닫기 칸을 디딘 시각 (t 기준)

    def update(self, dt):
        self.t += dt
        if self.state == 'warn' and self.t >= config.AD_WARN:
            self.state, self.t = 'slam', 0.0
        elif self.state == 'slam' and self.t >= config.AD_SLAM:
            self.state, self.t = 'stay', 0.0
        elif self.state == 'stay' and self.t >= config.AD_STAY:
            self.state, self.t = 'close', 0.0                    # 시간이 지나면 저절로 닫힘
        elif self.state == 'close' and self.t >= config.AD_CLOSE_TIME:
            self.state = 'gone'

    def is_wall(self):
        return self.state == 'stay'

    def close_rect(self):
        # 오른쪽 위 닫기 칸 (월드)
        s = config.AD_CLOSE_SIZE
        return self.x + self.w - s - 4, self.y + self.h - s - 4, s, s

    def step_close(self, fx, fy):
        # 발이 (fx, fy)에 착지: 닫기 칸이면 한 번 셈 (AD_CLOSE_FORGET 안에 이어서). 다 차면 닫힘. 디뎠으면 True
        if self.state != 'stay':
            return False
        x, y, w, h = self.close_rect()
        m = config.AD_CLOSE_MARGIN
        if not (x - m <= fx <= x + w + m and y - m <= fy <= y + h + m):
            return False
        if self.t - self.close_t > config.AD_CLOSE_FORGET:
            self.close_n = 0
        self.close_n += 1
        self.close_t = self.t
        if self.close_n >= config.AD_CLOSE_STEPS:
            self.state, self.t = 'close', 0.0
        return True

    def draw(self, camera):
        sx, sy = self.x, self.y - camera.y
        if sy > config.SCREEN_H + 40 or sy + self.h < -40:
            return
        cx, cy = sx + self.w / 2, sy + self.h / 2
        if self.state == 'warn':
            # 그림자: 작게 시작해 광고 크기로 커지며 진해짐 + 빨간 모서리 표시가 깜빡임
            k = self.t / config.AD_WARN
            w, h = self.w * (0.3 + 0.7 * k), self.h * (0.3 + 0.7 * k)
            fill_rect(cx - w / 2, cy - h / 2, w, h, (0, 0, 0), 0.25 + 0.4 * k)
            blink = 0.4 + 0.6 * (math.sin(self.t * 30) > 0)
            for ex, ey in ((0, 0), (1, 0), (0, 1), (1, 1)):     # 네 모서리 ㄱ자 표시
                px, py = sx + ex * self.w, sy + ey * self.h
                dx, dy = (14 if ex == 0 else -14), (14 if ey == 0 else -14)
                draw_line(px, py, px + dx, py, 2, config.COLOR_RED, blink)
                draw_line(px, py, px, py + dy, 2, config.COLOR_RED, blink)
            return
        scale, alpha = 1.0, 1.0
        if self.state == 'slam':
            scale = 1 + 0.25 * (1 - self.t / config.AD_SLAM)     # 위에서 내려꽂히듯 커졌다가 제자리
        elif self.state == 'close':
            k = self.t / config.AD_CLOSE_TIME
            scale, alpha = 1 - 0.6 * k, 1 - k                    # 닫힘: 작아지며 사라짐
        w, h = self.w * scale, self.h * scale
        x, y = cx - w / 2, cy - h / 2
        fill_rect(x, y, w, h, AD_BG, 0.97 * alpha)
        flash = AD_YELLOW if int(self.t * 4) % 2 == 0 else AD_PINK   # 번쩍번쩍 테두리
        draw_rect(x, y, w, h, 3, flash, alpha)
        if self.state == 'close' and scale < 0.7:
            return
        # 'AD' 딱지 + 광고 문구
        fill_rect(x + 8, y + h - 26, 30, 18, AD_YELLOW, alpha)
        draw_static_text(x + 12, y + h - 25, 'AD', 13, AD_BG, alpha, 'bold')
        top, bottom = self.lines
        draw_static_text(x + (w - text_width(top, 20, 'bold')) / 2, y + h * 0.52, top, 20, AD_YELLOW, alpha, 'bold')
        draw_static_text(x + (w - text_width(bottom, 15)) / 2, y + h * 0.32, bottom, 15, config.COLOR_WHITE, alpha)
        bw = 110                                                  # 가짜 버튼
        fill_rect(x + (w - bw) / 2, y + 12, bw, 22, AD_PINK, alpha)
        draw_static_text(x + (w - text_width('자세히 보기', 13)) / 2, y + 15, '자세히 보기', 13, config.COLOR_WHITE, alpha)
        if self.state == 'stay':
            # 닫기 칸: 회색 상자 + X (선으로). 디딘 만큼 주황으로 채워짐
            bx, by, bs, _ = self.close_rect()
            by -= camera.y
            fill_rect(bx, by, bs, bs, (60, 60, 70))
            if self.close_n:
                fill_rect(bx, by, bs, bs * self.close_n / config.AD_CLOSE_STEPS, config.COLOR_ORANGE, 0.8)
            draw_rect(bx, by, bs, bs, 1, config.COLOR_WHITE)
            draw_line(bx + 5, by + 5, bx + bs - 5, by + bs - 5, 2, config.COLOR_WHITE)
            draw_line(bx + 5, by + bs - 5, bx + bs - 5, by + 5, 2, config.COLOR_WHITE)
            left = 1 - self.t / config.AD_STAY                    # 저절로 닫힐 때까지 남은 시간: 아래 얇은 막대
            fill_rect(x, y - 4, w * left, 2, flash, 0.7)


class AdSpawner:
    # 광고 뿌리개: 이 문서에서 AD_PERIOD마다 크롤러가 가는 길 앞에 광고를 떨어뜨린다 (동시에 AD_MAX개까지)
    def __init__(self, x, y):
        self.x, self.y = x, y                # 쓰지 않음 (place_enemies 형식 맞춤)
        self.ads = []
        self.timer = config.AD_FIRST         # 문서에 들어오자마자 떨어지지 않게

    def active(self, camera):
        return True

    def update(self, dt, footprints):
        for ad in self.ads:
            ad.update(dt)
        self.ads = [ad for ad in self.ads if ad.state != 'gone']

    def drop(self, dt, body, page):
        # 머리가 가는 쪽 앞(속도 × AD_LEAD 초 뒤 자리)에 광고를 떨어뜨림. 기사 단 안으로 맞춤
        self.timer -= dt
        if self.timer > 0 or len(self.ads) >= config.AD_MAX:
            return
        self.timer = config.AD_PERIOD * random.uniform(0.8, 1.2)
        head = body.segs[0]
        x = head.x + math.cos(head.angle) * body.speed * config.AD_LEAD + random.uniform(-30, 30)
        y = head.y + math.sin(head.angle) * body.speed * config.AD_LEAD + random.uniform(-30, 30)
        cx = getattr(page.style, 'CONTENT_X', config.WIKI_CONTENT_X)     # 사이트별 본문 단
        cw = getattr(page.style, 'CONTENT_W', config.WIKI_CONTENT_W)
        left, right = cx + config.AD_W / 2, cx + cw - config.AD_W / 2
        x = max(left, min(right, x))
        y = max(config.AD_H, min(page.height - config.AD_H - 120, y))
        self.ads.append(Ad(x, y))

    def slamming(self):
        return [ad for ad in self.ads if ad.state == 'slam']

    def walls(self):
        return [ad for ad in self.ads if ad.is_wall()]

    def draw(self, camera):
        for ad in self.ads:
            ad.draw(camera)
