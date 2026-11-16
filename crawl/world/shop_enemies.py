# 쇼핑몰 사이트 적 (S10-6) — 쇼핑몰이 봇을 막고 손님을 붙잡는 방식에서 따왔다. 좌표는 월드 좌표.
#   캡차 (captcha)      링크를 빨리 연달아 먹으면 '로봇이 아닙니다' 판이 뜬다. 고를 칸에 머리를 잠깐 머물러 다 고를 때까지 링크를 못 먹음.
#                       시간 안에 못 풀면 판에서 백신 프로그램이 나와 흔들거리다 찔러 온다 (풀면 사라짐)
#   별점 투척 (stars)   1–2점 리뷰가 화난 ★을 크롤러에게 던진다 (피하는 탄)
#   타임딜 (deal)       상품 링크 몇 개에 시간 제한 — 시간 안에 먹으면 데이터 보너스 (벌이 아니라 상)
#   추천 상품 (recommend) 한자리에서 머뭇거리면 '이런 상품은 어때요?' 카드가 앞을 막는다 (벽, 다치지 않음)
#   카트 (cart)         크롤러 높이 줄로 장바구니 카트가 굴러온다. 치이면 실려서 화면 끝까지 밀려감
# 모두 watch(dt, body)로 크롤러를 본다 (play_mode가 매 프레임 부름).
import math
import random

import config
from ui.draw import fill_rect, draw_rect, draw_line, draw_static_text, text_width, get_image, fill_rect_rotated
from world.enemies import ProtectedBlock

HEAD_BLUE = (40, 110, 200)      # 캡차 머리 띠
BOARD = (232, 234, 238)         # 캡차 판 (밝게 — 화면에서 확 튀도록)
INK = (30, 32, 38)
OK_GREEN = (40, 170, 90)
BOX_BROWN = (170, 120, 70)
VAC_GLASS = (200, 230, 240)     # 백신 주사기 유리
VAC_LIQUID = (60, 210, 120)     # 백신 약
ORANGE = (255, 153, 0)
ICONS = {'box': '택배 상자', 'cup': '텀블러', 'umbrella': '우산', 'lamp': '스탠드'}


def wrap_text(text, size, width):
    # 글을 width 안에 들어가게 여러 줄로 (글자 단위)
    lines, cur = [], ''
    for ch in text:
        if text_width(cur + ch, size) > width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    return lines + [cur] if cur else lines


# ── 캡차 ──
class Captcha:
    # 한 문서에 하나. 평소엔 숨어서 먹은 시각만 센다 → 빨리 먹으면 크롤러 앞에 판이 뜬다
    def __init__(self):
        self.x = self.y = 0.0                # 판 왼쪽 아래 (뜬 동안만 의미)
        self.on = False                      # 판이 떠 있는지 (떠 있으면 링크를 못 먹음)
        self.eats = []                       # 최근에 링크를 먹은 시각들
        self.t = 0.0
        self.cool = 0.0                      # 풀고 나서 다시 뜨기까지 남은 시간
        self.solved = None                   # 다 풀고 나서 지난 시간 (None = 아님) — '확인됨' 뒤 사라짐
        self.hold = None                     # [칸 번호, 머문 시간]
        self.wrong = 0.0                     # 틀린 칸 빨간 번쩍임 남은 시간
        self.skip = None                     # 방금 고른(또는 틀린) 칸 — 머리가 한 번 나갔다 와야 다시 셈
        self.left = 0.0                      # 풀어야 하는 남은 시간 — 0이 되면 백신 프로그램이 나옴
        self.vaccines = []                   # 시간 초과로 나온 백신 프로그램들
        self.alarm = 0.0                     # '봇으로 판정되었습니다' 빨간 띠 남은 시간

    @classmethod
    def place(cls, page, others):
        return cls()

    def active(self, camera):
        return True

    def update(self, dt, footprints):
        self.t += dt
        self.cool = max(0.0, self.cool - dt)
        self.wrong = max(0.0, self.wrong - dt)
        if self.solved is not None:
            self.solved += dt
            if self.solved >= config.CAPTCHA_SOLVED_TIME:
                self.on, self.solved = False, None
                self.vaccines = []                                  # 풀었음: 백신도 물러감
        elif self.on:
            self.left -= dt
            if self.left <= 0:                                      # 시간 초과: 봇으로 판정 → 판에서 백신이 나옴, 시간은 다시
                w, h = self.size()
                for _ in range(config.CAPTCHA_VACCINES):
                    if len(self.vaccines) < config.VAC_MAX:
                        self.vaccines.append(Vaccine(self.x + w / 2 + random.uniform(-40, 40), self.y + h / 2))
                self.left = config.CAPTCHA_TIME
                self.alarm = config.CAPTCHA_ALARM
        self.alarm = max(0.0, self.alarm - dt)

    def size(self):
        n, gap = config.CAPTCHA_TILE, config.CAPTCHA_GAP
        grid = 3 * n + 2 * gap
        return grid + 24, grid + 24 + config.CAPTCHA_HEAD_H

    def blocking(self):
        return self.on and self.solved is None

    def note_eat(self, now, body, page):
        # 링크를 먹음: CAPTCHA_WINDOW초 안에 CAPTCHA_EATS번이면 머리 앞에 판을 띄운다
        self.eats = [t for t in self.eats if now - t < config.CAPTCHA_WINDOW] + [now]
        if self.on or self.cool > 0 or len(self.eats) < config.CAPTCHA_EATS:
            return
        head = body.segs[0]
        w, h = self.size()
        cx = head.x + math.cos(head.angle) * config.CAPTCHA_AHEAD
        cy = head.y + math.sin(head.angle) * config.CAPTCHA_AHEAD
        left = page.style.CONTENT_X
        self.x = max(left, min(left + page.style.CONTENT_W - w, cx - w / 2))
        self.y = max(40, min(page.height - h - 140, cy - h / 2))
        self.on, self.solved, self.eats = True, None, []
        self.left = config.CAPTCHA_TIME
        self.shuffle()

    def shuffle(self):
        # 고를 그림 하나 + 칸 9개 (고를 그림 3–4칸, 나머지는 다른 그림)
        self.want = random.choice(list(ICONS))
        n = random.randint(3, 4)
        others = [k for k in ICONS if k != self.want]
        self.tiles = [self.want] * n + [random.choice(others) for _ in range(9 - n)]
        random.shuffle(self.tiles)
        self.picked = [False] * 9
        self.hold = None

    def tile_rect(self, i):
        n, gap = config.CAPTCHA_TILE, config.CAPTCHA_GAP
        col, row = i % 3, i // 3
        return self.x + 12 + col * (n + gap), self.y + 12 + (2 - row) * (n + gap), n, n

    def watch(self, dt, body):
        # 백신은 크롤러를 보고 움직이고, 머리가 한 칸 안에 멈춰 서서 CAPTCHA_HOLD초 머물면 그 칸을 고름
        # (지나가기만 하면 안 셈). 틀린 칸이면 다시 섞임
        if self.solved is None:
            for v in self.vaccines:
                v.update(dt, body.segs[0])
        if not self.blocking():
            return
        head = body.segs[0]
        inside = None
        for i in range(9):
            x, y, w, h = self.tile_rect(i)
            if x <= head.x <= x + w and y <= head.y <= y + h and not self.picked[i]:
                inside = i
        if inside != self.skip:
            self.skip = None                                       # 그 칸에서 나갔음
        if inside is None or inside == self.skip:
            self.hold = None
            return
        if self.hold is None or self.hold[0] != inside:
            self.hold = [inside, 0.0]
        if body.speed > config.CAPTCHA_STILL:
            self.hold[1] = 0.0                                     # 지나가는 중이면 안 셈 — 멈춰 서야 고름
            return
        self.hold[1] += dt
        if self.hold[1] < config.CAPTCHA_HOLD:
            return
        self.hold = None
        self.skip = inside                                         # 섞인 뒤 머리 밑 칸이 바로 또 골라지지 않게
        if self.tiles[inside] == self.want:
            self.picked[inside] = True
            if all(p for p, t in zip(self.picked, self.tiles) if t == self.want) and \
                    sum(self.picked) == self.tiles.count(self.want):
                self.solved = 0.0                                  # 다 골랐음 → '확인됨'
                self.cool = config.CAPTCHA_COOLDOWN
        else:
            self.wrong = config.CAPTCHA_WRONG_TIME                 # 틀림: 빨갛게 번쩍이고 처음부터, 시간도 깎임
            self.left = max(0.5, self.left - config.CAPTCHA_WRONG_COST)
            self.shuffle()

    def draw(self, camera):
        if not self.on:
            return
        w, h = self.size()
        sx, sy = self.x, self.y - camera.y
        fade = 1.0 if self.solved is None else 1 - self.solved / config.CAPTCHA_SOLVED_TIME
        fill_rect(sx - 3, sy - 3, w + 6, h + 6, (0, 0, 0), 0.5 * fade)        # 그림자
        fill_rect(sx, sy, w, h, BOARD, fade)
        hh = config.CAPTCHA_HEAD_H
        fill_rect(sx, sy + h - hh, w, hh, OK_GREEN if self.solved is not None else HEAD_BLUE, fade)
        if self.solved is not None:
            draw_static_text(sx + 14, sy + h - 40, '확인되었습니다', 18, (255, 255, 255), fade, 'bold')
        elif self.alarm > 0:                            # 방금 시간 초과: 빨간 띠
            fill_rect(sx, sy + h - hh, w, hh, config.COLOR_RED, fade)
            draw_static_text(sx + 14, sy + h - 30, '봇으로 판정되었습니다', 15, (255, 255, 255), fade, 'bold')
            draw_static_text(sx + 14, sy + h - 54, '백신 프로그램 실행', 13, (255, 255, 255), fade)
        else:
            draw_static_text(sx + 14, sy + h - 26, '로봇이 아닙니다', 13, (255, 255, 255), fade)
            draw_static_text(sx + 14, sy + h - 52, '%s 칸을 모두 고르세요' % ICONS[self.want], 17, (255, 255, 255), fade, 'bold')
            sec = '%d' % max(0, math.ceil(self.left))                  # 남은 시간 (오른쪽 위)
            draw_static_text(sx + w - 14 - text_width(sec, 20, 'bold'), sy + h - 32, sec, 20,
                             (255, 230, 120) if self.left < 4 else (255, 255, 255), fade, 'bold')
            fill_rect(sx, sy + h - hh, w * self.left / config.CAPTCHA_TIME, 4, ORANGE, fade)
        for i in range(9):
            x, y, tw, th = self.tile_rect(i)
            y -= camera.y
            fill_rect(x, y, tw, th, (205, 208, 214), fade)
            draw_icon(self.tiles[i], x + tw / 2, y + th / 2, fade)
            if self.picked[i]:                                     # 고른 칸: 파란 테두리 + 체크(선으로)
                draw_rect(x, y, tw, th, 4, HEAD_BLUE, fade)
                fill_rect(x + 4, y + th - 26, 22, 22, HEAD_BLUE, fade)
                draw_line(x + 9, y + th - 15, x + 14, y + th - 20, 2, (255, 255, 255), fade)
                draw_line(x + 14, y + th - 20, x + 22, y + th - 9, 2, (255, 255, 255), fade)
            elif self.hold is not None and self.hold[0] == i:      # 머무는 중: 테두리가 아래부터 주황으로 차오름
                k = self.hold[1] / config.CAPTCHA_HOLD
                fill_rect(x, y, 4, th * k, ORANGE, fade)
                fill_rect(x + tw - 4, y, 4, th * k, ORANGE, fade)
                fill_rect(x, y, tw * k, 4, ORANGE, fade)
        if self.wrong > 0:
            fill_rect(sx, sy, w, h - hh, config.COLOR_RED, 0.35 * self.wrong / config.CAPTCHA_WRONG_TIME)
        for v in self.vaccines:
            v.draw(camera, fade)

    def stabbing(self):
        # 찌르러 날아오는 중인 백신들 (판정)
        return [v for v in self.vaccines if v.state == 'dash'] if self.solved is None else []


# ── 백신 프로그램 (캡차 시간 초과 때 판에서 나옴) ──
class Vaccine:
    # 주사기 모양. hover 크롤러 둘레를 흔들흔들 떠다니며 겨눔 → aim 멈춰 부들부들 떨며 찌를 길 표시(겨눈 자리 고정)
    # → dash 그 길로 곧장 날아와 찌름(방향 못 바꿈, 바늘 끝이 닿으면 피격) → rest 잠깐 멈칫 → 다시 hover
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.angle = 0.0                     # 바늘이 향한 방향
        self.state, self.t = 'hover', random.uniform(0, 0.6)
        self.orbit = random.uniform(0, math.pi * 2)   # 크롤러 둘레 어느 쪽에 떠 있을지
        self.vx = self.vy = 0.0

    def tip(self):
        # 바늘 끝 (피격 판정 자리)
        return self.x + math.cos(self.angle) * config.VAC_LEN / 2, self.y + math.sin(self.angle) * config.VAC_LEN / 2

    def update(self, dt, head):
        self.t += dt
        if self.state == 'hover':
            # 크롤러 둘레 VAC_ORBIT 거리의 자리로 부드럽게 따라가며 흔들거림, 바늘은 크롤러 쪽
            self.orbit += 0.6 * dt
            gx = head.x + math.cos(self.orbit) * config.VAC_ORBIT
            gy = head.y + math.sin(self.orbit) * config.VAC_ORBIT
            self.x += (gx - self.x) * min(1.0, 2.5 * dt) + math.sin(self.t * 5) * 40 * dt
            self.y += (gy - self.y) * min(1.0, 2.5 * dt) + math.cos(self.t * 4) * 40 * dt
            self.angle = math.atan2(head.y - self.y, head.x - self.x) + 0.25 * math.sin(self.t * 6)
            if self.t >= config.VAC_HOVER:
                self.state, self.t = 'aim', 0.0
                self.angle = math.atan2(head.y - self.y, head.x - self.x)   # 이 순간 겨눈 방향으로 고정
        elif self.state == 'aim':
            if self.t >= config.VAC_AIM:
                self.state, self.t = 'dash', 0.0
                self.vx = math.cos(self.angle) * config.VAC_DASH_SPEED
                self.vy = math.sin(self.angle) * config.VAC_DASH_SPEED
        elif self.state == 'dash':
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.t * config.VAC_DASH_SPEED >= config.VAC_DASH_DIST:
                self.state, self.t = 'rest', 0.0
        elif self.state == 'rest':
            if self.t >= config.VAC_REST:
                self.state, self.t = 'hover', 0.0

    def hit(self):
        # 찔렀음: 바로 멈칫 (연달아 찌르지 않게)
        self.state, self.t = 'rest', 0.0

    def draw(self, camera, alpha=1.0):
        sx, sy = self.x, self.y - camera.y
        a = self.angle
        if self.state == 'aim':                                     # 부들부들 + 찌를 길 빨간 점선
            sx += random.uniform(-2.5, 2.5)
            sy += random.uniform(-2.5, 2.5)
            blink = 0.4 + 0.6 * (math.sin(self.t * 30) > 0)
            for k in range(2, 16):
                d = k * config.VAC_DASH_DIST / 15
                fill_rect(sx + math.cos(a) * d - 2, sy + math.sin(a) * d - 2, 4, 4, config.COLOR_RED, 0.5 * blink * alpha)
        if self.state == 'dash':                                    # 날아갈 때 뒤로 잔상
            for k in range(1, 4):
                fill_rect_rotated(sx - self.vx * 0.02 * k, sy - self.vy * 0.02 * k, config.VAC_LEN * 0.7, 8, a,
                                  VAC_GLASS, 0.25 / k * alpha)
        c, s = math.cos(a), math.sin(a)
        L = config.VAC_LEN
        # 몸통(유리) + 안의 초록 약 + 뒤쪽 밀대 + 앞쪽 바늘
        fill_rect_rotated(sx, sy, L * 0.55, 12, a, VAC_GLASS, 0.9 * alpha)
        fill_rect_rotated(sx + c * 3, sy + s * 3, L * 0.4, 7, a, VAC_LIQUID, alpha)
        bx, by = sx - c * L * 0.3, sy - s * L * 0.3
        fill_rect_rotated(bx, by, 4, 16, a, (220, 220, 230), alpha)
        draw_line(bx, by, bx - c * 8, by - s * 8, 2, (220, 220, 230), alpha)
        tx, ty = sx + c * L / 2, sy + s * L / 2
        draw_line(sx + c * L * 0.28, sy + s * L * 0.28, tx, ty, 2, (235, 235, 240), alpha)
        fill_rect_rotated(tx, ty, 3, 3, a, config.COLOR_RED, alpha)    # 바늘 끝


def draw_icon(kind, cx, cy, alpha):
    # 캡차 칸 그림 (코드로): 택배 상자 · 텀블러 · 우산 · 스탠드
    if kind == 'box':
        fill_rect(cx - 26, cy - 20, 52, 40, BOX_BROWN, alpha)
        fill_rect(cx - 4, cy - 20, 8, 40, (225, 200, 150), alpha)          # 테이프
        draw_rect(cx - 26, cy - 20, 52, 40, 1, INK, alpha)
    elif kind == 'cup':
        fill_rect(cx - 12, cy - 26, 24, 46, (120, 190, 180), alpha)
        fill_rect(cx - 14, cy + 20, 28, 8, INK, alpha)                       # 뚜껑
    elif kind == 'umbrella':
        for i in range(8):                                                    # 반원 지붕: 짧은 선 8개
            a1, a2 = math.pi * i / 8, math.pi * (i + 1) / 8
            draw_line(cx + math.cos(a1) * 28, cy + math.sin(a1) * 22, cx + math.cos(a2) * 28, cy + math.sin(a2) * 22, 3, (40, 60, 120), alpha)
        draw_line(cx - 28, cy, cx + 28, cy, 2, (40, 60, 120), alpha)
        draw_line(cx, cy, cx, cy - 24, 2, INK, alpha)
        draw_line(cx, cy - 24, cx - 6, cy - 28, 2, INK, alpha)
    else:                                                                    # 스탠드: 받침 + 꺾인 팔 + 갓
        fill_rect(cx - 16, cy - 28, 32, 6, INK, alpha)
        draw_line(cx, cy - 22, cx - 10, cy + 4, 3, INK, alpha)
        draw_line(cx - 10, cy + 4, cx + 10, cy + 20, 3, INK, alpha)
        fill_rect(cx + 6, cy + 10, 20, 10, (240, 200, 90), alpha)


# ── 별점 투척 ──
class StarShot:
    # 날아가는 화난 별 하나 (닿으면 피격 — play_mode가 원 판정)
    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.t = 0.0
        self.dead = False


class StarThrower:
    # 화난 별점 하나 (1–2점 리뷰, 별점 3점 이하 상품 카드). 크롤러가 가까이 오면 STAR_PERIOD마다
    # 부들부들(경고) 떨다가 ★ 세 개를 크롤러 쪽으로 부채꼴로 던진다
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.timer = config.STAR_PERIOD * random.uniform(0.5, 1.0)
        self.shots = []
        self.t = 0.0

    @classmethod
    def place(cls, page, others):
        # 아직 쓰지 않은 낮은 별점 리뷰 자리 (없으면 None)
        used = [(o.x, o.y) for o in others if isinstance(o, StarThrower)]
        free = [s for s in page.review_spots if s not in used]
        return cls(*free[0]) if free else None

    def active(self, camera):
        return True

    def update(self, dt, footprints):
        self.t += dt
        for s in self.shots:
            s.t += dt
            s.x += s.vx * dt
            s.y += s.vy * dt
        self.shots = [s for s in self.shots if not s.dead and s.t < config.STAR_LIFE]

    def warning(self):
        return self.timer < config.STAR_WARN

    def watch(self, dt, body):
        head = body.segs[0]
        if math.hypot(head.x - self.x, head.y - self.y) > config.STAR_RANGE:
            self.timer = max(self.timer, config.STAR_WARN + 0.2)      # 멀면 경고 없이 대기
            return
        self.timer -= dt
        if self.timer > 0:
            return
        self.timer = config.STAR_PERIOD
        # 머리가 별이 닿을 때쯤 있을 자리를 조금 앞서 노린다 (완전히 맞히면 못 피하니 절반만 앞서)
        d = math.hypot(head.x - self.x, head.y - self.y)
        lead = d / config.STAR_SPEED * 0.5
        tx = head.x + math.cos(head.angle) * body.speed * lead
        ty = head.y + math.sin(head.angle) * body.speed * lead
        a = math.atan2(ty - self.y, tx - self.x)
        for k in range(config.STAR_FAN):                            # 부채꼴: 가운데 + 양옆으로 STAR_SPREAD씩
            ak = a + (k - (config.STAR_FAN - 1) / 2) * config.STAR_SPREAD
            self.shots.append(StarShot(self.x, self.y, math.cos(ak) * config.STAR_SPEED, math.sin(ak) * config.STAR_SPEED))

    def draw(self, camera):
        sx, sy = self.x, self.y - camera.y
        if self.warning():                                          # 부들부들: 리뷰 별이 빨갛게 떨림
            jx = random.uniform(-2, 2)
            draw_static_text(sx - 8 + jx, sy - 10, '★', 20, config.COLOR_RED, 0.9)
        for s in self.shots:
            px, py = s.x, s.y - camera.y
            for k in range(1, 4):                                   # 꼬리: 지나온 자리에 흐린 별
                draw_static_text(px - s.vx * 0.03 * k - 8, py - s.vy * 0.03 * k - 10, '★', 18, config.COLOR_RED, 0.25 / k)
            draw_static_text(px - 9, py - 11, '★', 20, ORANGE)


# ── 타임딜 ──
class TimeDeal:
    # 상품 링크 하나에 붙은 시간 제한 딱지. 시간 안에 먹으면 보너스 (시간이 지나도 링크는 그대로 — 갇히지 않게)
    def __init__(self, lid, x, y):
        self.lid = lid
        self.x, self.y = x, y                # 딱지 자리 (링크 첫 조각 위)
        self.left = config.DEAL_TIME
        self.done = False                    # 먹었거나 시간이 다 됨

    @classmethod
    def place(cls, page, others):
        # 아직 딱지가 없는 파란 링크 중 하나 (상품으로 가는 링크만, 검색 페이지 링크 제외)
        taken = [o.lid for o in others if isinstance(o, TimeDeal)]
        cands = [(x, y, h, lid) for x, y, w, h, text, target, lid in page.links
                 if lid not in taken and not target.startswith('검색:')]
        firsts = {}
        for x, y, h, lid in cands:                                  # 링크마다 맨 위 첫 조각
            if lid not in firsts or y > firsts[lid][1]:
                firsts[lid] = (x, y + h + 4)
        if not firsts:
            return None
        lid = random.choice(list(firsts))
        return cls(lid, *firsts[lid])

    def active(self, camera):
        return True

    def update(self, dt, footprints):
        if not self.done:
            self.left -= dt
            if self.left <= 0:
                self.done = True

    def draw(self, camera):
        if self.done:
            return
        sx, sy = self.x, self.y - camera.y
        label = '타임딜 0:%02d' % max(0, math.ceil(self.left))
        w = text_width(label, 12, 'bold') + 12
        hurry = self.left < 5 and int(self.left * 4) % 2 == 0      # 5초 남으면 깜빡
        fill_rect(sx, sy, w, 18, config.COLOR_RED if hurry else (204, 12, 57))
        draw_static_text(sx + 6, sy + 1, label, 12, (255, 255, 255), 1.0, 'bold')
        k = self.left / config.DEAL_TIME                             # 남은 시간 막대
        fill_rect(sx, sy - 3, w * k, 2, ORANGE)


# ── 추천 상품 ──
class RecoCard(ProtectedBlock):
    # '이런 상품은 어때요?' 카드 — 벽 (판정·밀어내기는 보호된 문단과 같음). 나타났다가 RECO_STAY 뒤 사라짐
    def __init__(self, x, y, product, image):
        w, h = config.RECO_W, config.RECO_H
        self.x, self.y, self.w, self.h = x - w / 2, y - h / 2, w, h
        self.product, self.image = product, image
        self.t = 0.0

    def alpha(self):
        pop = min(1.0, self.t / config.RECO_POP)
        out = min(1.0, (config.RECO_STAY - self.t) / config.RECO_POP)
        return max(0.0, min(pop, out))


class Recommender:
    # 한 문서에 하나. 머리가 RECO_RADIUS 안에서 RECO_IDLE초 넘게 머뭇거리면 그 앞에 추천 카드를 띄운다
    def __init__(self, products):
        self.products = products             # [(이름, 그림)] — 이 문서의 상품 링크들
        self.cards = []
        self.anchor = None                   # 머뭇거림을 재기 시작한 자리 (x, y, 머문 시간)

    @classmethod
    def place(cls, page, others):
        items = [(c['name'], c['image']) for c in page.reco_items]
        return cls(items) if items else None

    def active(self, camera):
        return True

    def update(self, dt, footprints):
        for c in self.cards:
            c.t += dt
        self.cards = [c for c in self.cards if c.t < config.RECO_STAY]

    def walls(self):
        return [c for c in self.cards if c.alpha() > 0.5]

    def watch(self, dt, body):
        head = body.segs[0]
        if self.anchor is None or math.hypot(head.x - self.anchor[0], head.y - self.anchor[1]) > config.RECO_RADIUS:
            self.anchor = [head.x, head.y, 0.0]                     # 움직였으면 처음부터
            return
        self.anchor[2] += dt
        if self.anchor[2] < config.RECO_IDLE or len(self.cards) >= config.RECO_MAX:
            return
        self.anchor[2] = 0.0
        # 머리가 보는 쪽 앞에 (몸과 겹치지 않는 방향을 몇 개 시도)
        for turn in (0, 0.6, -0.6, 1.2, -1.2, math.pi):
            a = head.angle + turn
            cx = head.x + math.cos(a) * config.RECO_AHEAD
            cy = head.y + math.sin(a) * config.RECO_AHEAD
            card = RecoCard(cx, cy, *random.choice(self.products))
            if not any(card.x - 12 <= s.x <= card.x + card.w + 12 and card.y - 12 <= s.y <= card.y + card.h + 12
                       for s in body.segs):
                self.cards.append(card)
                return

    def draw(self, camera):
        for c in self.cards:
            a = c.alpha()
            sx, sy = c.x, c.y - camera.y + 12 * (1 - min(1.0, c.t / config.RECO_POP))   # 아래에서 살짝 떠오름
            fill_rect(sx - 2, sy - 2, c.w + 4, c.h + 4, (0, 0, 0), 0.4 * a)
            fill_rect(sx, sy, c.w, c.h, (30, 34, 42), a)
            draw_rect(sx, sy, c.w, c.h, 2, ORANGE, a)
            draw_static_text(sx + 10, sy + c.h - 24, '이런 상품은 어때요?', 13, ORANGE, a, 'bold')
            image = get_image(c.image)
            isz = c.h - 40
            if image is not None:
                image.opacify(a)
                image.draw_to_origin(sx + 10, sy + 8, isz, isz)
            else:
                fill_rect(sx + 10, sy + 8, isz, isz, (50, 54, 62), a)
            name = c.product.strip('[]').split('|')[0]
            for k, line in enumerate(wrap_text(name, 12, c.w - isz - 30)[:4]):
                draw_static_text(sx + isz + 20, sy + c.h - 48 - k * 17, line, 12, (225, 225, 225), a)
            left = 1 - c.t / config.RECO_STAY                       # 사라질 때까지 남은 시간
            fill_rect(sx, sy - 4, c.w * left, 2, ORANGE, 0.7 * a)


# ── 장바구니 카트 ──
class Cart:
    # 한 줄을 가로로 훑고 지나가는 카트. warn 경고(화살표·점선) → roll 굴러감. 닿은 크롤러는 실어서 화면 끝까지 밀고 감
    def __init__(self, y, side):
        self.y = y                           # 굴러갈 줄 (카트 가운데 y)
        self.side = side                     # +1 = 왼쪽에서 오른쪽으로, -1 = 반대
        self.x = -config.CART_W if side > 0 else config.SCREEN_W + config.CART_W   # 카트 가운데 x
        self.state, self.t = 'warn', 0.0
        self.dx = 0.0                        # 이번 프레임에 움직인 거리 (실린 크롤러도 같이)
        self.carrying = False

    def update(self, dt):
        self.t += dt
        self.dx = 0.0
        if self.state == 'warn' and self.t >= config.CART_WARN:
            self.state, self.t = 'roll', 0.0
        elif self.state == 'roll':
            self.dx = self.side * config.CART_SPEED * dt
            self.x += self.dx

    def gone(self):
        return self.state == 'roll' and (self.x < -config.CART_W * 2 or self.x > config.SCREEN_W + config.CART_W * 2)

    def rect(self):
        w, h = config.CART_W, config.CART_H
        return self.x - w / 2, self.y - h / 2, w, h

    def grab(self):
        self.carrying = True                 # 크롤러를 실음 (play_mode가 피격 처리 뒤 부름)

    def draw(self, camera):
        sy = self.y - camera.y
        if sy < -80 or sy > config.SCREEN_H + 80:
            return
        if self.state == 'warn':
            # 경고: 들어올 쪽 화면 끝에 빨간 화살표 + 줄을 따라 깜빡이는 점선
            blink = 0.4 + 0.6 * (math.sin(self.t * 28) > 0)
            ex = 18 if self.side > 0 else config.SCREEN_W - 18
            for k in range(3):
                ax = ex + self.side * k * 14
                draw_line(ax - self.side * 8, sy + 10, ax + self.side * 4, sy, 3, config.COLOR_RED, blink)
                draw_line(ax - self.side * 8, sy - 10, ax + self.side * 4, sy, 3, config.COLOR_RED, blink)
            for x in range(60, config.SCREEN_W - 60, 30):
                fill_rect(x, sy - 1, 14, 3, config.COLOR_RED, 0.6 * blink)
            return
        # 카트: 바구니(격자) + 손잡이 + 바퀴 두 개. 지나간 자리에 속도선
        w, h = config.CART_W, config.CART_H
        x0, y0 = self.x - w / 2, sy - h / 2
        for k in range(1, 4):
            fill_rect(self.x - self.side * (w / 2 + k * 22), sy - 12 + k * 6, 18, 2, (200, 200, 210), 0.5 / k)
        fill_rect(x0, y0 + 12, w, h - 12, (70, 76, 90))
        for i in range(1, 5):                                          # 바구니 격자
            draw_line(x0 + i * w / 5, y0 + 12, x0 + i * w / 5, y0 + h, 1, (150, 156, 170))
        draw_line(x0, y0 + 12 + (h - 12) / 2, x0 + w, y0 + 12 + (h - 12) / 2, 1, (150, 156, 170))
        draw_rect(x0, y0 + 12, w, h - 12, 2, ORANGE)
        hx = x0 if self.side > 0 else x0 + w                           # 손잡이는 뒤쪽
        draw_line(hx, y0 + h, hx - self.side * 14, y0 + h + 12, 3, (200, 200, 210))
        for wx in (x0 + 12, x0 + w - 12):
            fill_rect(wx - 6, y0, 12, 12, (30, 30, 34))
            draw_rect(wx - 6, y0, 12, 12, 1, (200, 200, 210))


class CartRush:
    # 카트 보내는 곳 (한 문서에 하나). CART_PERIOD마다 크롤러 높이 줄로 카트를 보낸다.
    # 실린 크롤러는 카트와 같이 밀려가다 화면 끝에서 내려짐
    def __init__(self):
        self.carts = []
        self.timer = config.CART_FIRST

    @classmethod
    def place(cls, page, others):
        return cls()

    def active(self, camera):
        return True

    def update(self, dt, footprints):
        for c in self.carts:
            c.update(dt)
        self.carts = [c for c in self.carts if not c.gone()]

    def launch(self, y):
        # 높이 y 줄로 카트 하나 (어느 쪽에서 올지는 무작위)
        self.carts.append(Cart(y, random.choice((1, -1))))

    def rolling(self):
        return [c for c in self.carts if c.state == 'roll' and not c.carrying]

    def watch(self, dt, body):
        head = body.segs[0]
        self.timer -= dt
        if self.timer <= 0:
            self.timer = config.CART_PERIOD * random.uniform(0.8, 1.2)
            self.launch(head.y + random.uniform(-30, 30))           # 지금 크롤러 높이 — 경고를 보고 위아래로 비켜야 함
        for c in self.carts:
            if c.carrying:
                head.x += c.dx                                       # 실려 감: 머리를 카트와 같이 밀고, 몸은 끌려옴
                head.y += (c.y - head.y) * min(1.0, 8 * dt)
                body.stun = max(body.stun, 0.1)                      # 실려 가는 동안 조종 불가
                edge = config.CART_DROP_EDGE
                if head.x < edge or head.x > config.SCREEN_W - edge:  # 화면 끝 → 내려놓음
                    head.x = max(edge, min(config.SCREEN_W - edge, head.x))
                    c.carrying = False

    def draw(self, camera):
        for c in self.carts:
            c.draw(camera)
