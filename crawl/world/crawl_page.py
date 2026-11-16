# 크롤러 브라우저 자체 페이지 (crawl://complete 등) — 사이트 문서가 아니라 CRAWL.EXE의 페이지 (PRD 12)
# 메뉴·결과도 크롤러가 걸어 다니는 페이지다. 선택은 칸을 밟아서 (출구 칸과 같은 판정·채우기).
# play_mode가 위키 Page와 똑같이 다룰 수 있게 같은 이름의 속성·함수를 둔다 (링크·키워드는 없음).
import config
from ui.draw import fill_rect, draw_rect, draw_line, draw_static_text, text_width


class CrawlPage:
    def __init__(self, name, lines, slots, style='center', info=None):
        # name: 주소 이름 (crawl://<name>), slots: [{'label': 칸 글, 'key': 구분 이름, 'action': 밟으면 할 일, 'enabled': 열렸는지}]
        # style 'center': lines = [(글, 크기, 색, 굵게?)] 가운데 정렬 글줄 (complete)
        # style 'report': lines = [(항목, 값, 색)] 고정폭 오류 보고서 — 위에서부터 한 줄씩 나타남 (lost)
        # style 'transfer': 파일 전송 창 — info = {from, to, items(옮길 데이터 수), names(옮기는 문서 이름들)}
        self.style = style
        self.info = info or {}
        self.slot_y = config.CRAWL_SLOT_Y          # 칸 높이 (final은 깔때기 위로 올림)
        self.title = name
        self.url = '/' + name                      # 띠 주소칸: crawl:/ + /complete
        self.height = config.SCREEN_H - config.HUD_BAR_H   # 한 화면 (스크롤 없음)
        self.lines = lines
        self.slots = slots
        # 위키 Page와 같은 이름 — 이 페이지에는 먹을 링크·키워드가 없다
        self.links, self.groups, self.goals = [], {}, []
        self.hazards = []                          # F2 시험용 위험 지점 (이 페이지에서도 시험 가능)
        self.parts = []                            # 다리 파츠 없음 (play_mode가 매 프레임 훑음)
        self.enemies = []                          # 적 없음
        self.time = 0.0

    def spawn(self):
        return config.SCREEN_W / 2, self.height - config.CRAWL_SPAWN_FROM_TOP

    def goal_at(self, x, y):
        return False

    def part_at(self, x, y):
        return None

    def eat_at(self, x, y):
        return None

    def eaten_count(self):
        return 0

    def update(self, dt):
        self.time += dt

    def slot_rects(self):
        # 칸들을 한 줄로 가운데 정렬 [(x, y, w, h)] (월드 = 화면, 스크롤 없음)
        w, h, gap = config.CRAWL_SLOT_W, config.CRAWL_SLOT_H, config.CRAWL_SLOT_GAP
        n = len(self.slots)
        x0 = (config.SCREEN_W - (n * w + (n - 1) * gap)) / 2
        return [(x0 + i * (w + gap), self.slot_y, w, h) for i in range(n)]

    def progress(self):
        # 전송 창: 0 → 1 (TRANSFER_TIME 동안 — 처음엔 빠르고 끝에서 느려지는 진짜 전송 막대처럼)
        u = min(1.0, self.time / config.TRANSFER_TIME)
        return 1 - (1 - u) ** 2

    def transfer_done(self):
        return self.style == 'transfer' and self.time >= config.TRANSFER_TIME + config.TRANSFER_HOLD

    def draw(self, camera, fill=(None, 0.0)):
        if self.style == 'report':
            self.draw_report(camera, fill)
            return
        if self.style == 'transfer':
            self.draw_transfer(camera)
            return
        # 바탕: 점 격자 (사이트 페이지와 다른, 크롤러 브라우저의 빈 페이지 느낌)
        g = config.CRAWL_GRID
        for gx in range(g // 2, config.SCREEN_W, g):
            for gy in range(g // 2, self.height, g):
                fill_rect(gx, gy - camera.y, 2, 2, config.HUD_BAR_LINE)
        # 글줄: 위에서부터 가운데 정렬
        y = self.height - config.CRAWL_TEXT_TOP
        for text, size, color, bold in self.lines:
            kind = 'bold' if bold else 'ui'
            draw_static_text((config.SCREEN_W - text_width(text, size, kind)) / 2, y - camera.y, text, size, color, 1.0, kind)
            y -= size + config.CRAWL_LINE_GAP
        # 칸: 열린 칸은 금색 테두리, 잠긴 칸은 회색. 밟은 만큼 주황으로 차오름 (출구 칸과 같음)
        size = config.WIKI_FONT_H3
        for (sx, sy, w, h), slot in zip(self.slot_rects(), self.slots):
            color = config.COLOR_GOLD if slot['enabled'] else config.COLOR_GRAY
            fill_rect(sx, sy - camera.y, w, h, config.HUD_BAR_BG)
            if slot['key'] == fill[0]:
                fill_rect(sx, sy - camera.y, w * fill[1], h, config.COLOR_ORANGE, 0.35)
            draw_rect(sx, sy - camera.y, w, h, 2 if slot['enabled'] else 1, color)
            tw = text_width(slot['label'], size, 'bold')
            draw_static_text(sx + (w - tw) / 2, sy - camera.y + h / 2 - 11, slot['label'], size, color, 1.0, 'bold')
        if self.slots:                                                   # (칸이 아직 없는 페이지 — final — 에는 안내도 없음)
            hint = '칸 위에 잠시 서 있으면 이동합니다'
            hy = self.slot_y - 34 if self.slot_y == config.CRAWL_SLOT_Y else self.slot_y + config.CRAWL_SLOT_H + 12   # 칸 아래가 막혔으면 위에
            draw_static_text((config.SCREEN_W - text_width(hint, 12)) / 2, hy - camera.y, hint, 12, config.HUD_LABEL)

    def draw_transfer(self, camera):
        # 파일 복사 창처럼: 제목 줄 → 어디서 어디로 → 두 폴더 사이를 날아가는 종이 → 퍼센트·막대 → 이름·남은 시간·남은 항목
        g = config.CRAWL_GRID
        for gx in range(g // 2, config.SCREEN_W, g):                     # 바탕 점 격자 (다른 crawl:// 페이지와 같음)
            for gy in range(g // 2, self.height, g):
                fill_rect(gx, gy - camera.y, 2, 2, config.HUD_BAR_LINE)
        w, h = config.TRANSFER_W, config.TRANSFER_H
        x = (config.SCREEN_W - w) / 2
        y = (self.height - h) / 2 - 20 - camera.y
        k = self.progress()
        fill_rect(x + 6, y - 6, w, h, (0, 0, 0), 0.5)                    # 그림자
        fill_rect(x, y, w, h, config.HUD_FIELD_BG)
        draw_rect(x, y, w, h, 1, config.WIKI_BORDER_STRONG)
        fill_rect(x, y + h - 34, w, 34, config.HUD_BAR_BG)                # 제목 줄
        title = '다음 장소로 이동 중' if k < 1 else '이동 완료'
        draw_static_text(x + 14, y + h - 26, title, 14, config.WIKI_TEXT, 1.0, 'bold')
        bx = x + w - 30                                                   # 닫기 X (눌리지 않는 장식)
        draw_line(bx, y + h - 22, bx + 10, y + h - 12, 1, config.HUD_LABEL)
        draw_line(bx, y + h - 12, bx + 10, y + h - 22, 1, config.HUD_LABEL)
        info = self.info
        line = '%s  →  %s' % (info.get('from', ''), info.get('to', ''))
        draw_static_text(x + 24, y + h - 70, line, 15, config.WIKI_TEXT)   # (→는 고정폭 글꼴에 없어 일반 글꼴)
        # 두 폴더 + 날아가는 종이 (포물선, 차례로)
        fy = y + h - 150
        lx, rx = x + 60, x + w - 120
        for px in (lx, rx):
            fill_rect(px, fy, 60, 42, (200, 160, 60))
            fill_rect(px, fy + 42, 24, 8, (200, 160, 60))
        if k < 1:
            for i in range(4):
                u = (self.time * 0.9 + i / 4) % 1.0
                px = lx + 30 + (rx - lx) * u
                py = fy + 40 + 46 * 4 * u * (1 - u)                         # 포물선: 가운데서 가장 높이
                fill_rect(px - 8, py - 10, 16, 20, config.WIKI_TEXT, 0.9)
                for j in range(3):
                    fill_rect(px - 5, py + 4 - j * 5, 10, 1, config.HUD_LABEL)
        # 퍼센트 + 진행 막대 (초록, 위로 흐르는 줄무늬)
        pct = '%d%% 완료' % round(k * 100)
        draw_static_text(x + 24, fy - 40, pct, 20, config.WIKI_TEXT, 1.0, 'bold')
        by, bw = fy - 72, w - 48
        fill_rect(x + 24, by, bw, 18, config.HUD_BAR_BG)
        fill_rect(x + 24, by, bw * k, 18, (60, 190, 90))
        for sx in range(0, int(bw * k), 16):                               # 흐르는 줄무늬
            off = (self.time * 40) % 16
            fill_rect(x + 24 + sx + off, by, 6, 18, (120, 230, 140), 0.35)
        draw_rect(x + 24, by, bw, 18, 1, config.WIKI_BORDER_STRONG)
        # 이름 · 남은 시간 · 남은 항목
        names = info.get('names') or ['-']
        name = names[min(len(names) - 1, int(k * len(names)))]
        items = info.get('items', 0)
        left_t = max(0.0, config.TRANSFER_TIME - self.time)
        rows = [('이름', name), ('남은 시간', '약 %d초' % (left_t + 0.99) if k < 1 else '완료'),
                ('남은 항목', '%d개 (데이터 조각)' % round(items * (1 - k)))]
        for i, (label, value) in enumerate(rows):
            ry = by - 32 - i * 24
            draw_static_text(x + 24, ry, label, 13, config.HUD_LABEL)
            draw_static_text(x + 130, ry, value[:46], 13, config.WIKI_TEXT)

    def draw_report(self, camera, fill):
        # 오류 보고서: 고정폭 글씨의 충돌 로그. 제목 줄 → 구분선 → 항목들(한 줄씩 나타남) → 구분선 → 버튼 칸
        x, right = config.REPORT_X, config.SCREEN_W - config.REPORT_X
        y = self.height - config.REPORT_TOP - camera.y
        for gy in range(0, self.height, 4):                               # 아주 옅은 가로줄 (오래된 화면 느낌)
            fill_rect(0, gy - camera.y, config.SCREEN_W, 1, config.HUD_BAR_BG, 0.5)
        draw_static_text(x, y, 'CRAWL.EXE — 오류 보고서', 22, config.COLOR_RED, 1.0, 'bold')
        tag = 'crawl://' + self.title
        draw_static_text(right - text_width(tag, 13, 'mono'), y + 4, tag, 13, config.HUD_LABEL, 1.0, 'mono')
        y -= 18
        draw_line(x, y, right, y, 1, config.WIKI_BORDER_STRONG)
        shown = int(self.time / config.REPORT_TYPE)                       # 지금까지 나타난 줄 수
        for i, (label, value, color) in enumerate(self.lines[:shown]):
            ly = y - 36 - i * config.REPORT_LINE
            draw_static_text(x, ly, label, 15, config.HUD_LABEL, 1.0, 'mono')
            draw_static_text(x + config.REPORT_LABEL_W, ly, value, 15, color, 1.0, 'mono')
        if shown >= len(self.lines):
            ly = y - 36 - len(self.lines) * config.REPORT_LINE + 12
            draw_line(x, ly, right, ly, 1, config.WIKI_BORDER_STRONG)
        # 버튼 칸: 대화상자 버튼처럼 (열린 칸은 밝은 테두리, 잠긴 칸은 회색). 밟은 만큼 차오름
        size = config.WIKI_FONT_H3
        for (sx, sy, w, h), slot in zip(self.slot_rects(), self.slots):
            color = config.WIKI_TEXT if slot['enabled'] else config.COLOR_GRAY
            fill_rect(sx, sy - camera.y, w, h, config.HUD_FIELD_BG)
            if slot['key'] == fill[0]:
                fill_rect(sx, sy - camera.y, w * fill[1], h, config.COLOR_RED, 0.35)
            draw_rect(sx, sy - camera.y, w, h, 2 if slot['enabled'] else 1, color)
            label = '[ %s ]' % slot['label']
            tw = text_width(label, size, 'mono')
            draw_static_text(sx + (w - tw) / 2, sy - camera.y + h / 2 - 10, label, size, color, 1.0, 'mono')
