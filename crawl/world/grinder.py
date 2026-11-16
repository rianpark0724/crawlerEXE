# 완전 클리어 (S10-7d) — crawl://final의 데이터 깔때기. 좌표는 월드 = 화면 (한 화면짜리 페이지).
# 크롤러는 화면 위쪽에 나타나고, 깔때기는 아래쪽에 입구가 위·주둥이가 아래를 향해 있다.
# 플레이어가 크롤러를 입구로 몰면 아래로 빨려 내려가며: 입구 테두리에서 다리가 뜯기고(다리 점수),
# 좁아질수록 마디가 옆으로 짓눌리고, 목을 지난 마디의 데이터가 주둥이 아래로 주르륵 흘러 통에 쌓인다(데이터 점수).
# 마지막 마디가 주둥이 속으로 들어가고 데이터가 다 떨어지면 끝 (play_mode가 시간을 멈추고 최종 점수).
import math
import random

import config
from ui.draw import fill_rect, draw_rect, draw_line, draw_static_text, text_width

INSIDE_TOP = (40, 44, 54)       # 깔때기 안쪽 (위 — 밝음)
INSIDE_BOTTOM = (10, 11, 14)    # 깔때기 안쪽 (아래 — 어두움)
WALL = (120, 128, 145)          # 깔때기 벽 테두리
METAL = (70, 76, 90)            # 주둥이·통


class Grinder:
    def __init__(self, data, par_total):
        self.cx = config.SCREEN_W / 2
        self.data = data                     # 흘러나올 데이터 수 (몸에 든 것 전부)
        self.par_total = par_total           # 세 사이트 기준 시간 합 (시간 보너스)
        self.t = 0.0
        self.state = 'open'                  # open 기다림 / pull 빨려 들어가는 중 / done 끝
        self.shares = []                     # 마디마다 들어 있는 데이터 수 (빨려 들어갈 때 나눔)
        self.passed = set()                  # 목을 지난 마디 (데이터를 쏟음)
        self.pending = 0                     # 주둥이에서 아직 안 흘러나온 데이터 수
        self.drip_timer = 0.0
        self.drips = []                      # 흘러내리는 데이터 [x, y, vy]
        self.data_in = 0                     # 통에 떨어진 데이터 수
        self.legs_in = 0                     # 뜯긴 다리 수
        self.sparks = []                     # 다리가 뜯길 때 튀는 불꽃 [x, y, vx, vy, 나이]
        self.wobble = 0.0                    # 깔때기가 덜컹거리는 남은 시간
        self.eye = None                      # 다 짜낸 뒤 주스에서 튀어나온 눈알 (Eye)

    # ── 점수 ──
    def score_data(self):
        return self.data_in * config.SCORE_DATA

    def score_legs(self):
        return self.legs_in * config.SCORE_LEG

    def time_bonus(self, play_time):
        return max(0, int(self.par_total - play_time)) * config.SCORE_TIME

    # ── 모양 ──
    def half_width(self, y):
        # 높이 y에서 깔때기 안쪽 반폭: 입구(MOUTH_Y)에서 넓고 목(NECK_Y)까지 곧게 좁아짐, 그 아래 주둥이는 목 폭 그대로
        top, neck = config.FUNNEL_MOUTH_Y, config.FUNNEL_NECK_Y
        if y >= top:
            return config.FUNNEL_MOUTH_W / 2
        if y <= neck:
            return config.FUNNEL_NECK_W / 2
        k = (y - neck) / (top - neck)
        return (config.FUNNEL_NECK_W + (config.FUNNEL_MOUTH_W - config.FUNNEL_NECK_W) * k) / 2

    def at_mouth(self, x, y):
        # 머리가 입구에 닿았는지 (입구 줄 바로 위 ~ 안쪽)
        return abs(x - self.cx) < config.FUNNEL_MOUTH_W / 2 - 10 and y < config.FUNNEL_MOUTH_Y + 14

    # ── 움직임 ──
    def update(self, dt, body, target_x, target_y):
        self.t += dt
        if self.eye is not None:
            self.eye.update(dt, target_x, target_y)              # 눈알은 마우스(커서 월드 좌표)를 따라 찰박찰박
        self.wobble = max(0.0, self.wobble - dt)
        head = body.segs[0]
        if self.state == 'open' and self.at_mouth(head.x, head.y):
            self.start_pull(body)
        if self.state == 'pull':
            self.pull(dt, body)
        self.update_drips(dt)
        for s in self.sparks:
            s[0] += s[2] * dt
            s[1] += s[3] * dt
            s[3] -= 600 * dt
            s[4] += dt
        self.sparks = [s for s in self.sparks if s[4] < 0.6]
        if self.state == 'pull' and all(body.hidden(i) for i in range(len(body.segs))) \
                and self.pending == 0 and not self.drips:
            self.state = 'done'                                  # 다 들어갔고 데이터도 다 떨어짐
        if self.state == 'done':
            body.stun = max(body.stun, 1.0)                      # 짜낸 몸은 주둥이 속에 그대로 (커서를 따라 기어 나오지 않게)
            body.hide_below = float('inf')                       # 전부 안 보임

    def start_pull(self, body):
        # 빨려 들어가기 시작: 데이터를 마디마다 나눠 담고, 마디가 떨어져 나가지 않게, 주둥이 아래는 안 보이게
        self.state = 'pull'
        n = len(body.segs)
        self.shares = [self.data // n + (1 if i < self.data % n else 0) for i in range(n)]
        body.in_funnel = True
        body.hide_below = config.FUNNEL_SPOUT_Y

    def pull(self, dt, body):
        # 머리를 깔때기 가운데 줄을 따라 아래로 끌어내림 (조종 불가). 나머지 마디는 끌려옴
        body.stun = max(body.stun, 0.2)
        head = body.segs[0]
        head.x += (self.cx - head.x) * min(1.0, 6 * dt)
        head.y -= config.FUNNEL_PULL * dt
        head.angle = -math.pi / 2                                # 머리는 아래(주둥이)를 봄
        for i, seg in enumerate(body.segs):
            # 벽: 깔때기 안의 마디는 그 높이의 안쪽 폭을 넘지 못하고, 좁아진 만큼 짓눌림
            if seg.y < config.FUNNEL_MOUTH_Y:
                h = self.half_width(seg.y)
                seg.x = max(self.cx - h + 4, min(self.cx + h - 4, seg.x))
                top, neck = config.FUNNEL_MOUTH_Y, config.FUNNEL_NECK_Y
                seg.crush = min(1.0, (top - seg.y) / (top - neck))
                if seg.legs:                                     # 입구 테두리에서 다리가 뜯김
                    self.tear_legs(body, seg)
            if seg.y < config.FUNNEL_NECK_Y and i not in self.passed:
                self.passed.add(i)                               # 목을 지남: 이 마디의 데이터가 주둥이로
                self.pending += self.shares[i] if i < len(self.shares) else 0
                self.wobble = 0.15

    def tear_legs(self, body, seg):
        for leg in list(seg.legs):
            self.legs_in += 1
            body.cut_leg(leg, self.cx, seg.y - 40)               # 위·바깥으로 튕겨 나감
        for _ in range(8):
            a = random.uniform(0.3, math.pi - 0.3)
            v = random.uniform(120, 260)
            self.sparks.append([seg.x, seg.y, math.cos(a) * v, math.sin(a) * v, 0.0])
        self.wobble = 0.2

    def update_drips(self, dt):
        # 주둥이에서 데이터가 일정 간격으로 하나씩 흘러나와 떨어짐 → 통에 닿으면 점수
        self.drip_timer -= dt
        if self.pending > 0 and self.drip_timer <= 0:
            self.drip_timer = config.FUNNEL_DRIP
            self.pending -= 1
            self.drips.append([self.cx + random.uniform(-4, 4), config.FUNNEL_SPOUT_Y - 4, -40.0])
        keep = []
        for d in self.drips:
            d[2] -= config.FUNNEL_GRAVITY * dt
            d[1] += d[2] * dt
            if d[1] <= config.FUNNEL_BIN_Y + self.bin_level():
                self.data_in += 1                                # 통에 떨어짐
                continue
            keep.append(d)
        self.drips = keep

    def bin_level(self):
        # 통에 쌓인 데이터 주스 높이 (px) — 비율이 아니라 실제 데이터 수만큼 (많이 모았으면 가득, 적으면 바닥에 조금)
        return min(config.FUNNEL_BIN_H - 6, self.data_in * config.JUICE_PER_DATA)

    def spawn_eye(self):
        # 다 짜냈음: 주스 표면에서 네모 눈이 튀어나옴
        self.eye = Eye(self.cx, config.FUNNEL_BIN_Y + 3 + self.bin_level())

    # ── 그리기 ──
    def draw_under(self, camera):
        # 크롤러 아래: 깔때기 안쪽(위는 밝고 아래로 어두워지는 가로줄들)과 통
        jx = random.uniform(-2, 2) if self.wobble > 0 else 0.0    # 덜컹
        top, neck = config.FUNNEL_MOUTH_Y, config.FUNNEL_NECK_Y
        for y in range(int(neck), int(top), 2):
            k = (y - neck) / (top - neck)
            h = self.half_width(y)
            color = tuple(int(b + (a - b) * k) for a, b in zip(INSIDE_TOP, INSIDE_BOTTOM))
            fill_rect(self.cx - h + jx, y - camera.y, h * 2, 2, color)
        # 통: 주둥이 아래 넓은 상자 + 데이터 주스 (표면이 출렁이고, 안에 0·1 거품)
        bw, bh, by = config.FUNNEL_BIN_W, config.FUNNEL_BIN_H, config.FUNNEL_BIN_Y
        sy = by - camera.y
        fill_rect(self.cx - bw / 2, sy, bw, bh, (18, 20, 26))
        level = self.bin_level()
        if level > 0:
            fill_rect(self.cx - bw / 2 + 3, sy + 3, bw - 6, level, config.COLOR_SKY, 0.55)
            for x in range(int(self.cx - bw / 2 + 3), int(self.cx + bw / 2 - 3), 6):   # 출렁이는 표면 (밝은 줄)
                wave = 2 * math.sin(self.t * 4 + x * 0.08)
                fill_rect(x, sy + 3 + level - 2 + wave, 6, 3, config.COLOR_SKY, 0.95)
            rnd = random.Random(7)
            for i in range(int(level / 6)):                      # 주스 속 0·1 (데이터였던 흔적)
                bx = self.cx - bw / 2 + 10 + rnd.random() * (bw - 30)
                byy = sy + 6 + (rnd.random() * level + self.t * 8) % max(1.0, level - 8)
                draw_static_text(bx, byy, rnd.choice('01'), 9, (200, 240, 255), 0.5, 'mono')
        draw_rect(self.cx - bw / 2, sy, bw, bh, 2, METAL)

    def draw_over(self, camera):
        # 크롤러 위: 깔때기 벽 테두리·입구 테두리, 주둥이(마디를 가림), 흘러내리는 데이터, 불꽃
        jx = random.uniform(-2, 2) if self.wobble > 0 else 0.0
        top, neck, spout = config.FUNNEL_MOUTH_Y, config.FUNNEL_NECK_Y, config.FUNNEL_SPOUT_Y
        mw, nw = config.FUNNEL_MOUTH_W / 2, config.FUNNEL_NECK_W / 2
        cy = -camera.y
        for side in (-1, 1):                                     # 벽: 굵은 사선
            draw_line(self.cx + side * mw + jx, top + cy, self.cx + side * nw + jx, neck + cy, 6, WALL)
        fill_rect(self.cx - mw - 14 + jx, top - 4 + cy, mw * 2 + 28, 8, WALL)   # 입구 테두리
        fill_rect(self.cx - nw - 4 + jx, spout + cy, nw * 2 + 8, neck - spout, METAL)   # 주둥이 관 (들어간 마디를 가림)
        draw_rect(self.cx - nw - 4 + jx, spout + cy, nw * 2 + 8, neck - spout, 1, WALL)
        for x, y, vy in self.drips:                              # 주르륵: 떨어지는 데이터 + 아래로 늘어진 꼬리
            fill_rect(x - 3, y + cy, 6, 6, config.COLOR_SKY)
            fill_rect(x - 2, y + cy + 6, 4, min(18, -vy * 0.03), config.COLOR_SKY, 0.45)
        for x, y, vx, vy, age in self.sparks:
            fill_rect(x - 2, y - 2 + cy, 4, 4, config.COLOR_ORANGE, 1 - age / 0.6)
        draw_static_text(self.cx - mw, top + 14 + cy, 'DATA FUNNEL', 13, config.HUD_LABEL, 1.0, 'mono')
        if self.eye is not None:
            self.eye.draw(camera)                                # 눈알은 맨 위 (깔때기 위로도 뛰어다님)

    def draw_panel(self, play_time, done_time):
        # 오른쪽 점수판: 통에 떨어진 데이터·뜯긴 다리 점수가 올라가고, 다 끝나면 시간 보너스와 최종 점수
        x, y = config.GRIND_PANEL_X, config.FUNNEL_MOUTH_Y
        draw_static_text(x, y, '점수 계산', 18, config.WIKI_TEXT, 1.0, 'bold')
        rows = [('데이터', '%d × %d' % (self.data_in, config.SCORE_DATA), self.score_data()),
                ('남은 다리', '%d × %d' % (self.legs_in, config.SCORE_LEG), self.score_legs())]
        if done_time is not None:
            rows.append(('시간 보너스', '%d:%02d / 기준 %d:%02d' % (done_time // 60, done_time % 60,
                                                              self.par_total // 60, self.par_total % 60),
                         self.time_bonus(done_time)))
        for i, (label, detail, pts) in enumerate(rows):
            ry = y - 40 - i * 30
            draw_static_text(x, ry, label, 14, config.HUD_LABEL)
            draw_static_text(x + 100, ry, detail, 14, config.WIKI_TEXT)
            s = '{:,}'.format(pts)
            draw_static_text(x + 320 - text_width(s, 15, 'bold'), ry, s, 15, config.COLOR_SKY, 1.0, 'bold')
        total = self.score_data() + self.score_legs() + (self.time_bonus(done_time) if done_time is not None else 0)
        ty = y - 40 - len(rows) * 30 - 16
        draw_line(x, ty + 28, x + 320, ty + 28, 1, config.HUD_BAR_LINE)
        draw_static_text(x, ty - 10, '최종 점수' if done_time is not None else '합계', 16, config.WIKI_TEXT, 1.0, 'bold')
        s = '{:,}'.format(total)
        size = 34 if done_time is not None else 24
        draw_static_text(x + 320 - text_width(s, size, 'bold'), ty - 14, s, size, config.COLOR_GOLD, 1.0, 'bold')
        if self.state == 'open':                                 # 안내 (왼쪽)
            for i, line in enumerate(['모든 사이트를 크롤링했습니다.', '크롤러를 깔때기에 넣어', '모은 데이터를 짜내세요.']):
                draw_static_text(config.GRIND_HINT_X, config.FUNNEL_MOUTH_Y - i * 24, line, 15, config.WIKI_TEXT)


class Eye:
    # 다 짜낸 크롤러에서 남은 네모 눈 (머리에 붙어 있던 픽셀 눈). 주스에서 퐁 튀어나와 마우스 쪽으로 찰박찰박 뛰어다닌다 (높이 z: 0이면 땅)
    # 메뉴 칸은 이 눈알이 그 위에 서 있으면 넘어간다 (play_mode의 standing_spot)
    def __init__(self, x, y, splash=True):
        # splash: 주스에서 튀어나올 땐 방울이 튐 (ESC 일시정지로 머리에서 빠져나올 땐 없음)
        self.x, self.y = x, y
        self.z, self.vz = 0.0, config.EYE_POP_VZ             # 튀어나옴: 위로 높이 솟았다가
        self.vx, self.vy = 0.0, config.EYE_POP_VY            # 통 위쪽(화면 위)으로 떨어짐
        self.rest = 0.0                                      # 다음 뜀까지 남은 시간
        self.squash = 0.0                                    # 착지 납작함 남은 시간
        self.drops = []                                      # 튄 주스 방울 [x, y, z, vx, vy, vz]
        self.wet = splash                                    # 주스에 젖었는지 (방울·젖은 자국)
        self.splash(14)

    def splash(self, n):
        if not self.wet:
            return
        for _ in range(n):
            a = random.uniform(0, math.pi * 2)
            v = random.uniform(30, 110)
            self.drops.append([self.x, self.y, 2.0, math.cos(a) * v, math.sin(a) * v, random.uniform(80, 220)])

    def update(self, dt, tx, ty):
        self.squash = max(0.0, self.squash - dt)
        if self.z > 0 or self.vz > 0:                        # 공중
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.vz -= config.EYE_GRAVITY * dt
            self.z += self.vz * dt
            if self.z <= 0:                                  # 착지: 찰박 — 납작해지고 방울이 튐
                self.z = self.vz = 0.0
                self.vx = self.vy = 0.0
                self.squash = config.EYE_SQUASH
                self.rest = config.EYE_HOP_GAP
                self.splash(6)
        else:
            self.rest -= dt
            d = math.hypot(tx - self.x, ty - self.y)
            if self.rest <= 0 and d > 6:
                # 커서 쪽으로 한 번 뜀: 한 번에 EYE_HOP_DIST까지, 뜀 시간 EYE_HOP_TIME (높이는 그 시간에 맞춰)
                step = min(config.EYE_HOP_DIST, d)
                t = config.EYE_HOP_TIME
                self.vx, self.vy = (tx - self.x) / d * step / t, (ty - self.y) / d * step / t
                self.vz = config.EYE_GRAVITY * t / 2
        for p in self.drops:
            p[0] += p[3] * dt
            p[1] += p[4] * dt
            p[5] -= config.EYE_GRAVITY * dt
            p[2] += p[5] * dt
        self.drops = [p for p in self.drops if p[2] > 0]

    def grounded(self):
        return self.z == 0

    def draw(self, camera):
        # 크롤러 머리에 붙어 있던 네모난 픽셀 눈 그대로 (크기만 키움). 착지 직후엔 가로로 퍼지고 세로로 눌림
        sx, sy = self.x, self.y - camera.y
        s = config.EYE_SIZE
        shadow = s * max(0.4, 1 - self.z / 120)                  # 그림자 (높이 뜰수록 작게)
        fill_rect(sx - shadow / 2, sy - 3 - shadow / 4, shadow, shadow / 2, (0, 0, 0), 0.35)
        for x, y, z, vx, vy, vz in self.drops:                  # 주스 방울
            fill_rect(x - 2, y + z - camera.y - 2, 4, 4, config.COLOR_SKY, 0.85)
        k = self.squash / config.EYE_SQUASH
        w, h = s * (1 + 0.4 * k), s * (1 - 0.35 * k)
        fill_rect(sx - w / 2, sy + self.z, w, h, config.EYE_COLOR)
        if self.grounded() and self.wet:                          # 젖은 자국: 밑에 주스가 살짝
            fill_rect(sx - s * 0.7, sy - 2, s * 1.4, 2, config.COLOR_SKY, 0.4)
