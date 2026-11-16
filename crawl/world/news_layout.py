# 뉴스 사이트 레이아웃 — BBC 뉴스 기사 페이지의 화면 구성을 레퍼런스로, 어두운(블랙) 테마로 배치한다 (PRD 10.1, S10-2).
# 이름·로고는 실제 언론사가 아닌 가상의 'W·E·B 뉴스'. 글 배치·링크·문단·출구는 PageLayout 공통.
#
# 기사 문서 (data/pages/news/*.json):
#   title, section(분야), time(올린 시각 글), author, role(직함)
#   lead: {image, caption, credit}           대표 사진 (16:9)
#   blocks: ['p', 글] / ['h2', 소제목] / ['img', {image, caption, credit}] / ['quote', 글]
#   related: [{title, image}, ...]           관련 기사 카드 (제목이 그 기사로 가는 링크)
import config
from ui.draw import text_width
from world.page_layout import PageLayout

NEWS_DEFAULTS = {
    'section': '기술',
    'time': '3시간 전',
    'author': '김웹 기자',
    'role': '기술 담당',
    'blocks': [],
    'related': [],
}

BLACK = (0, 0, 0)
BAR = (22, 22, 22)           # 분야 띠
RULE = (60, 60, 60)          # 구분선
SUBTLE = (150, 150, 150)     # 시각·캡션·직함
WHITE = (240, 240, 240)
NAV = ['홈', '뉴스', '스포츠', '비즈니스', '기술', '문화', '여행', '영상', '라이브']
SUB = ['기술', '과학', '세계', '사회', '정치', '건강']
IMG_W, IMG_H = 680, 383      # 대표 사진·본문 사진 (16:9)


class NewsLayout(PageLayout):
    BODY_SIZE = 16
    LINE_H = 28
    TEXT = (225, 225, 225)
    LINK = (110, 190, 255)            # 먹을 수 있는 링크: 밝은 하늘색 + 밑줄 (BBC처럼 밑줄 링크)
    VISITED = (170, 150, 220)
    REDLINK = (235, 120, 105)
    ALPHA = 0.6
    CONTENT_X = 300                   # 가운데 680px 기사 단
    CONTENT_W = IMG_W
    LINK_UNDERLINE = True
    HEADER_H = 56
    SECTION_H = 52

    def build(self, doc):
        doc = dict(NEWS_DEFAULTS, **doc)
        top = self.height
        self.header(top)
        y = self.section_bar(doc, top - self.HEADER_H)
        y = self.title_area(doc, y - 36)
        if 'lead' in doc:
            y = self.photo(doc['lead'], y)
        y = self.body(doc, y)
        y = self.related(doc, y)
        y = self.exit_box(y)
        return self.footer(y)

    def logo(self, x, mid, size):
        # 블록 로고: 흰 사각형 세 개에 W·E·B (BBC식 블록 글자 — 가상의 언론사)
        for i, ch in enumerate('WEB'):
            bx = x + i * (size + 4)
            self.fill(bx, mid - size / 2, size, size, WHITE)
            self.text_mid(bx + (size - text_width(ch, int(size * 0.7), 'bold')) / 2, mid, ch, int(size * 0.7), 'bold', BLACK)
        return x + 3 * (size + 4)

    def header(self, top):
        # 검은 머리글: 로고 · 메뉴 · 로그인 · 검색
        mid = top - self.HEADER_H / 2
        self.fill(0, top - self.HEADER_H, config.SCREEN_W, self.HEADER_H, BLACK)
        cx = self.logo(40, mid, 26) + 24
        self.line(cx - 12, mid - 16, cx - 12, mid + 16, 1, RULE)
        for item in NAV:
            cx += self.text_mid(cx, mid, item, 14, 'bold', WHITE) + 22
        r = config.SCREEN_W - 40
        self.rect(r - 150, mid - 14, 90, 28, RULE)
        self.text_mid(r - 140, mid, '로그인', 13, 'bold', WHITE)
        self.text_mid(r - 44, mid, '검색', 13, 'ui', SUBTLE)
        self.line(0, top - self.HEADER_H, config.SCREEN_W, top - self.HEADER_H, 1, RULE)

    def section_bar(self, doc, y):
        # 분야 띠: 큰 '뉴스' + 하위 분야 탭 (지금 분야는 흰 글 + 밑줄)
        h = self.SECTION_H
        self.fill(0, y - h, config.SCREEN_W, h, BAR)
        mid = y - h / 2
        cx = 40 + self.text_mid(40, mid, '뉴스', 24, 'bold', WHITE) + 30
        for s in SUB:
            active = s == doc['section']
            w = self.text_mid(cx, mid, s, 14, 'bold' if active else 'ui', WHITE if active else SUBTLE)
            if active:
                self.line(cx, y - h + 2, cx + w, y - h + 2, 3, WHITE)
            cx += w + 24
        self.line(0, y - h, config.SCREEN_W, y - h, 1, RULE)
        return y - h

    def title_area(self, doc, y):
        # 큰 제목(여러 줄) → 시각·공유·저장 → 기자 이름과 직함
        x, w = self.left, self.CONTENT_W
        y = self.paragraph('**' + doc['title'] + '**', x, y, w, 30, WHITE, 40)
        y -= 14
        mid = y - 10
        cx = x + self.text_mid(x, mid, doc['time'], 13, 'ui', SUBTLE) + 18
        self.share_icon(cx + 6, mid)
        cx += 20
        cx += self.text_mid(cx, mid, '공유', 13, 'ui', SUBTLE) + 16
        self.rect(cx, mid - 6, 9, 12, SUBTLE)                       # 저장(책갈피) 자리
        self.text_mid(cx + 16, mid, '저장', 13, 'ui', SUBTLE)
        y -= 34
        self.fill(x, y - 36, 3, 36, WHITE)                          # 기자 줄 왼쪽 막대
        self.text_mid(x + 14, y - 10, doc['author'], 14, 'bold', WHITE)
        self.text_mid(x + 14, y - 28, doc['role'], 13, 'ui', SUBTLE)
        return y - 56

    def share_icon(self, x, y):
        # 공유: 점 세 개를 잇는 모양
        for (ax, ay), (bx, by) in [((-5, 0), (4, 5)), ((-5, 0), (4, -5))]:
            self.line(x + ax, y + ay, x + bx, y + by, 1, SUBTLE)
        for px, py in [(-5, 0), (4, 5), (4, -5)]:
            self.fill(x + px - 2, y + py - 2, 4, 4, SUBTLE)

    def photo(self, ph, y):
        # 16:9 사진 + 왼쪽 아래 출처 글 + 아래 캡션
        x = self.left
        self.image(x, y - IMG_H, IMG_W, IMG_H, ph['image'])
        if ph.get('credit'):
            cw = text_width(ph['credit'], 11) + 12
            self.fill(x, y - IMG_H, cw, 20, BLACK)
            self.text_mid(x + 6, y - IMG_H + 10, ph['credit'], 11, 'ui', SUBTLE)
        y -= IMG_H + 8
        if ph.get('caption'):
            y = self.paragraph(ph['caption'], x, y, IMG_W, 13, SUBTLE, 20)
        return y - 20

    def body(self, doc, y):
        x, w = self.left, self.CONTENT_W
        for block in doc['blocks']:
            kind = block[0]
            if kind == 'p':
                y = self.body_paragraph(block[1], x, y, w) - 14
            elif kind == 'h2':
                y -= 10
                y = self.paragraph('**' + block[1] + '**', x, y, w, 20, WHITE, 30) - 10
            elif kind == 'img':
                y = self.photo(block[1], y - 6)
            elif kind == 'quote':
                top = y
                y = self.paragraph(block[1], x + 22, y, w - 22, 19, WHITE, 32)
                self.fill(x, y, 4, top - y, self.LINK)               # 인용 왼쪽 굵은 막대
                y -= 18
        return y

    def related(self, doc, y):
        # 관련 기사: 구분선 + 제목 + 카드 3장 (썸네일 + 제목 링크)
        if not doc['related']:
            return y
        x, w = self.left, self.CONTENT_W
        y -= 10
        self.line(x, y, x + w, y, 2, WHITE)
        y -= 14
        self.text_mid(x, y - 12, '관련 기사', 20, 'bold', WHITE)
        y -= 40
        gap = 20
        cw = (w - gap * 2) / 3
        th = int(cw * 9 / 16)
        lowest = y
        for i, card in enumerate(doc['related'][:3]):
            cx = x + i * (cw + gap)
            self.image(cx, y - th, cw, th, card['image'])
            bottom = self.paragraph('[[' + card['title'] + ']]', cx, y - th - 8, cw, 14, WHITE, 22)
            lowest = min(lowest, bottom)
        return lowest - 16

    def exit_box(self, y):
        # 출구 상자는 기사 단(680)보다 넓게 — 칸 5개에 기사 제목이 들어가도록
        left, right = self.left, self.right
        self.left, self.right = 160, config.SCREEN_W - 160
        y = super().exit_box(y)
        self.left, self.right = left, right
        return y

    def footer(self, y):
        # 검은 바닥글: 로고 · 링크들 · 저작권과 가상 사이트 안내
        h = 140
        top = y - 10
        self.fill(0, top - h, config.SCREEN_W, h, BLACK)
        self.line(0, top, config.SCREEN_W, top, 1, RULE)
        self.logo(40, top - 32, 20)
        cx = 40
        for s in ['이용 약관', '회사 소개', '개인정보 처리방침', '쿠키', '접근성 도움말', '문의하기']:
            cx += self.text_mid(cx, top - 72, s, 13, 'ui', WHITE) + 24
        self.text_mid(40, top - 104, '© 2026 W·E·B 뉴스. 이 사이트는 CRAWL.EXE 속 가상의 뉴스 사이트이며 실제 언론사가 아닙니다.', 12, 'ui', SUBTLE)
        return top - h
