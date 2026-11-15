# 크롤러 브라우저 자체 페이지 (crawl://complete 등) — 사이트 문서가 아니라 CRAWL.EXE의 페이지 (PRD 12)
# 메뉴·결과도 크롤러가 걸어 다니는 페이지다. 선택은 칸을 밟아서 (출구 칸과 같은 판정·채우기).
# play_mode가 위키 Page와 똑같이 다룰 수 있게 같은 이름의 속성·함수를 둔다 (링크·키워드는 없음).
import config
from ui.draw import fill_rect, draw_rect, draw_static_text, text_width


class CrawlPage:
    def __init__(self, name, lines, slots):
        # name: 주소 이름 (crawl://<name>), lines: [(글, 크기, 색, 굵게?)] 가운데 정렬 글줄
        # slots: [{'label': 칸 글, 'key': 구분 이름, 'action': 밟으면 할 일, 'enabled': 열렸는지}]
        self.title = name
        self.url = '/' + name                      # 띠 주소칸: crawl:/ + /complete
        self.height = config.SCREEN_H - config.HUD_BAR_H   # 한 화면 (스크롤 없음)
        self.lines = lines
        self.slots = slots
        # 위키 Page와 같은 이름 — 이 페이지에는 먹을 링크·키워드가 없다
        self.links, self.groups, self.goals = [], {}, []
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
        return [(x0 + i * (w + gap), config.CRAWL_SLOT_Y, w, h) for i in range(n)]

    def draw(self, camera, fill=(None, 0.0)):
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
        hint = '칸을 세 번 밟으면 이동합니다'
        draw_static_text((config.SCREEN_W - text_width(hint, 12)) / 2, config.CRAWL_SLOT_Y - 34 - camera.y, hint, 12, config.HUD_LABEL)
