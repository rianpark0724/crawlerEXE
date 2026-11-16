# 링크 섭취 연출 — 먹은 링크의 글자가 떨어져 나와 밟은 다리를 거쳐 머리로 빨려 들어가고(꿀꺽),
# 단어를 다 삼키면 몸 안에 데이터 조각으로 쌓인다(저장). 되돌리기 봇이 되돌리면 반대로 글자가 몸에서 링크로 돌아간다.
# 좌표는 월드 좌표.
import config
from ui.draw import draw_static_text, text_width


class Glyph:
    # 날아가는 글자 하나: 시작점 → (휘는 점) → 끝점을 2차 베지어 곡선으로. 끝점은 매 프레임 다시 정할 수 있다(움직이는 머리)
    def __init__(self, ch, x, y, cx, cy, size, delay, word, inward):
        self.ch = ch
        self.x0, self.y0 = x, y          # 출발 (링크 글자 자리 또는 머리)
        self.cx, self.cy = cx, cy        # 휘는 점 (밟은 발 위쪽)
        self.ex, self.ey = x, y          # 도착 (머리 또는 링크 글자 자리) — update에서 정함
        self.size = size
        self.t = -delay                  # 0보다 작으면 아직 출발 전 (글자마다 조금씩 늦게)
        self.word = word                 # 이 글자가 속한 단어 (다 도착하면 저장)
        self.inward = inward             # True = 몸으로 들어감(섭취), False = 몸에서 나감(되돌림)

    def pos(self):
        u = max(0.0, min(1.0, self.t / config.INGEST_TIME))
        e = u * u * (3 - 2 * u)                                    # 천천히 출발해 빨라졌다 도착
        # 2차 베지어: (1-e)²·시작 + 2(1-e)e·휘는 점 + e²·도착
        a, b, c = (1 - e) ** 2, 2 * (1 - e) * e, e * e
        return a * self.x0 + b * self.cx + c * self.ex, a * self.y0 + b * self.cy + c * self.ey, u


class Ingest:
    def __init__(self):
        self.glyphs = []
        self.waiting = {}                # 단어 → 아직 도착 안 한 글자 수
        self.stored = []                 # 몸에 저장된 단어들 (조각 수 = len)

    def eat(self, pieces, foot_x, foot_y):
        # pieces: 먹힌 링크의 조각들 [(x, y, 글, 크기)] — 글자마다 날아갈 글자를 만든다
        word = ''.join(p[2] for p in pieces)
        self.waiting[word] = self.waiting.get(word, 0)
        k = 0
        for x, y, text, size in pieces:
            for i, ch in enumerate(text):
                if ch == ' ':
                    continue
                gx = x + text_width(text[:i], size)
                g = Glyph(ch, gx, y, foot_x, foot_y + config.INGEST_ARC, size, k * config.INGEST_STAGGER, word, True)
                self.glyphs.append(g)
                self.waiting[word] += 1
                k += 1

    def spit(self, pieces, head_x, head_y):
        # 되돌림: 저장된 단어 하나를 빼고, 그 글자들이 머리에서 링크 자리로 돌아간다
        word = ''.join(p[2] for p in pieces)
        if word in self.stored:
            self.stored.remove(word)
        elif self.stored:
            self.stored.pop()
        k = 0
        for x, y, text, size in pieces:
            for i, ch in enumerate(text):
                if ch == ' ':
                    continue
                g = Glyph(ch, head_x, head_y, (head_x + x) / 2, max(head_y, y) + config.INGEST_ARC, size,
                          k * config.INGEST_STAGGER, word, False)
                g.ex, g.ey = x + text_width(text[:i], size), y
                self.glyphs.append(g)
                k += 1

    def update(self, dt, body):
        # 섭취 글자의 도착점 = 지금 머리. 도착하면 꿀꺽, 단어의 마지막 글자가 도착하면 저장 + 소화 빛
        head = body.segs[0]
        done = []
        for g in self.glyphs:
            g.t += dt
            if g.inward:
                g.ex, g.ey = head.x, head.y
            if g.t >= config.INGEST_TIME:
                done.append(g)
        for g in done:
            self.glyphs.remove(g)
            if g.inward:
                body.gulp()
                self.waiting[g.word] -= 1
                if self.waiting[g.word] == 0:
                    del self.waiting[g.word]
                    self.stored.append(g.word)
                    body.digest()

    def draw(self, camera):
        for g in self.glyphs:
            if g.t < 0:
                continue
            x, y, u = g.pos()
            # 들어갈 땐 링크색 → 하늘색으로 바뀌며 작아지고, 나갈 땐 반대
            k = u if g.inward else 1 - u
            color = tuple(int(a + (b - a) * k) for a, b in zip(config.WIKI_LINK, config.COLOR_SKY))
            size = max(8, int(g.size * (1 - 0.4 * k)))
            sx, sy = camera.to_screen(x, y)
            draw_static_text(sx, sy, g.ch, size, color)
