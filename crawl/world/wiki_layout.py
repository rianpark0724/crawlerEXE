# 위키 문서(JSON) → 페이지 위 그리기 목록 — 위키백과 Vector 2022 어두운 테마를 레퍼런스로 배치한다.
# 위에서 아래로 커서(y)를 내려가며 놓는다. 좌표는 월드 좌표, y 위로 증가.
#
# 글 표기 (data/pages/<사이트>/*.json, PRD 11.2):
#   [[제목]]         링크 — 그 제목의 문서가 사이트에 있으면 파랑(데이터 조각), 없으면 빨강
#   [[제목|표시글]]  링크 대상과 화면에 보일 글이 다를 때
#   [[!단어]]        항상 빨간 링크 (없는 문서)
#   **단어**         굵게
#   [1], [출처 필요]   각주 표시 (작게, 위로)
#   {{키워드|대체어}}  목표 키워드가 들어갈 수 있는 자리. 뽑힌 자리만 키워드(S05-7), 나머지는 대체어
#
# 그리기 목록 항목: (종류, 아래 y, 위 y, ...값)  — 아래·위 y는 화면 밖 건너뛰기용
#   ('text', lo, hi, x, y, 글, 크기, 글꼴, 색)    y는 글의 아래
#   ('line', lo, hi, x1, y1, x2, y2, 두께, 색)
#   ('rect', lo, hi, x, y, w, h, 색)            테두리
#   ('fill', lo, hi, x, y, w, h, 색)            채움
#   ('image', lo, hi, x, y, w, h, 파일 이름)
#   ('link', lo, hi, x, y, 글, 크기, 링크 번호)   파란 링크 조각 — 먹었는지에 따라 색이 바뀌어 Page가 그린다
import re

import config
from ui.draw import text_width, text_height

# 링크: [[!?대상(|표시글)?]] / 굵게: **글** / 각주: [숫자] [출처 필요]
TOKEN = re.compile(r'\[\[(!?)([^\]|]+?)(?:\|(.+?))?\]\]|\*\*(.+?)\*\*|\[(\d+|출처 필요)\]|\{\{(.+?)\|(.+?)\}\}')

# 문서 JSON에서 생략할 수 있는 항목의 기본값
DOC_DEFAULTS = {
    'languages': '1개 언어',
    'hatnote': '',
    'categories': [],
    'edited': '이 문서는 2026년 11월 16일 (월) 03:12에 마지막으로 편집되었습니다.',
    'notice': '이 문서는 CRAWL.EXE 속 가상의 문서이며, 실제 위키백과 문서가 아닙니다.',
    'footer_links': ['개인정보처리방침', '위키백과 소개', '면책 조항', '모바일 보기'],
}


def parse(markup, titles):
    # 표기가 섞인 글 → [(글, 종류, 링크 대상)]. 종류: 'n' 보통, 'b' 굵게, 'link' 파란 링크, 'red' 빨간 링크, 'ref' 각주
    spans, pos = [], 0
    for m in TOKEN.finditer(markup):
        if m.start() > pos:
            spans.append((markup[pos:m.start()], 'n', None))
        if m.group(2) is not None:
            target = m.group(2)
            shown = m.group(3) if m.group(3) else target
            blue = not m.group(1) and target in titles        # 사이트에 그 문서가 있어야 파랑
            spans.append((shown, 'link' if blue else 'red', target))
        elif m.group(4) is not None:
            spans.append((m.group(4), 'b', None))
        elif m.group(5) is not None:
            spans.append(('[' + m.group(5) + ']', 'ref', None))
        else:
            spans.append((m.group(7), 'n', None))       # 키워드 자리: 지금은 대체어로 (S05-7에서 뽑힌 자리만 키워드)
        pos = m.end()
    if pos < len(markup):
        spans.append((markup[pos:], 'n', None))
    return spans


def to_words(spans):
    # 공백 기준으로 단어를 나눈다. 단어 하나 = 붙어 있는 조각들 (예: [[데이터]]+"를")
    # 조각 = (글, 종류, 링크 대상, 링크 번호) — 여러 단어로 나뉜 링크도 같은 번호로 묶인다
    words = [[]]
    for n, (text, kind, target) in enumerate(spans):
        parts = text.split(' ')
        for i, part in enumerate(parts):
            if i > 0:
                words.append([])          # 공백 → 새 단어
            if part != '':
                words[-1].append((part, kind, target, n))
    return [w for w in words if w]


class WikiLayout:
    def __init__(self, height, titles):
        self.height = height
        self.titles = titles     # 사이트에 있는 문서 제목들 — 링크를 파랑/빨강으로 가르는 기준
        self.items = []
        self.links = []          # 파란 링크 조각 위치 (x, y, w, h, 글, 대상 문서, 링크 번호) — 데이터 조각 (S05-4)
        self.link_count = 0      # 문단마다 링크 번호가 겹치지 않게 더해 주는 값
        self.float_bottom = None # 오른쪽 그림 틀의 아래 y (그 위쪽 줄은 폭을 줄인다)
        self.float_w = 0
        self.left = config.WIKI_CONTENT_X
        self.right = config.WIKI_CONTENT_X + config.WIKI_CONTENT_W

    # ── 그리기 목록에 넣기 ──
    def text(self, x, y, s, size, kind, color):
        self.items.append(('text', y, y + text_height(size, kind), x, y, s, size, kind, color))

    def line(self, x1, y1, x2, y2, width, color):
        self.items.append(('line', min(y1, y2) - width, max(y1, y2) + width, x1, y1, x2, y2, width, color))

    def rect(self, x, y, w, h, color):
        self.items.append(('rect', y, y + h, x, y, w, h, color))

    def fill(self, x, y, w, h, color):
        self.items.append(('fill', y, y + h, x, y, w, h, color))

    def image(self, x, y, w, h, name):
        self.items.append(('image', y, y + h, x, y, w, h, name))

    def text_mid(self, x, y_mid, s, size, kind, color):
        # 세로 가운데가 y_mid가 되게 글을 놓고, 글 폭을 돌려준다
        self.text(x, y_mid - text_height(size, kind) / 2, s, size, kind, color)
        return text_width(s, size, kind)

    # ── 문단 ──
    def width_at(self, y, x, w):
        # 오른쪽 그림 틀 옆이면 그만큼 좁게
        if self.float_bottom is not None and y > self.float_bottom and x + w > self.right - self.float_w:
            return self.right - self.float_w - x
        return w

    def paragraph(self, markup, x, y, w, size=config.WIKI_FONT_BODY, color=config.WIKI_TEXT, line_h=config.WIKI_LINE_H):
        # 단어 단위 줄바꿈. y는 첫 줄의 위, 돌려주는 값은 마지막 줄의 아래
        words = to_words(parse(markup, self.titles))
        space = text_width(' ', size)
        line, line_w = [], 0
        for word in words:
            ww = sum(self.piece_width(p[0], p[1], size) for p in word)
            max_w = self.width_at(y, x, w)
            if line and line_w + space + ww > max_w:
                self.flush(line, x, y, size, color, line_h)
                y -= line_h
                line, line_w = [], 0
            line_w += (space if line else 0) + ww
            line.append(word)
        if line:
            self.flush(line, x, y, size, color, line_h)
            y -= line_h
        self.link_count += 1000               # 다음 문단의 링크 번호는 다른 범위로
        return y

    def piece_width(self, text, kind, size):
        if kind == 'ref':
            return text_width(text, config.WIKI_FONT_REF)
        return text_width(text, size, 'bold' if kind == 'b' else 'ui')

    def flush(self, line, x, y_top, size, color, line_h):
        # 한 줄을 실제 위치에 놓는다
        base = y_top - line_h + (line_h - text_height(size)) / 2      # 글 아래 y (줄 안에서 세로 가운데)
        space = text_width(' ', size)
        cx = x
        for i, word in enumerate(line):
            if i > 0:
                cx += space
            for text, kind, target, n in word:
                pw = self.piece_width(text, kind, size)
                if kind == 'ref':
                    self.text(cx, base + size * 0.45, text, config.WIKI_FONT_REF, 'ui', config.WIKI_LINK)   # 위첨자
                elif kind == 'link':
                    lid = self.link_count + n
                    self.items.append(('link', base, base + text_height(size), cx, base, text, size, lid))
                    self.links.append((cx, base, pw, text_height(size), text, target, lid))
                elif kind == 'red':
                    self.text(cx, base, text, size, 'ui', config.WIKI_REDLINK)
                else:
                    self.text(cx, base, text, size, 'bold' if kind == 'b' else 'ui', color)
                cx += pw

    # ── 페이지 전체 ──
    def build(self, doc):
        doc = dict(DOC_DEFAULTS, **doc)            # 생략한 항목은 기본값으로
        top = self.height
        self.header(top)
        self.toc(doc, top - config.WIKI_HEADER_H - 28)
        y = self.title_area(doc, top - config.WIKI_HEADER_H - 20)
        y = self.body(doc, y)
        y = self.footer(doc, y)
        return y                                   # 문서 맨 아래 y (페이지 높이 계산용)

    def header(self, top):
        mid = top - config.WIKI_HEADER_H / 2
        for dy in (-6, 0, 6):                                                    # ≡ 메뉴 버튼
            self.line(24, mid + dy, 42, mid + dy, 2, config.WIKI_TEXT)
        self.image(56, mid - 18, 36, 36, 'wiki_logo.png')                        # 로고 자리 (직접 그린 그림)
        self.text(100, mid - 4, '위키백과', 20, 'bold', config.WIKI_TEXT)
        self.text(100, mid - 20, '우리 모두의 백과사전', 11, 'ui', config.WIKI_SUBTLE)
        # 검색창 + 검색 버튼
        self.fill(280, mid - 16, 400, 32, config.COLOR_BG)
        self.rect(280, mid - 16, 400, 32, config.WIKI_BORDER_STRONG)
        self.text_mid(296, mid, '위키백과 검색', 14, 'ui', config.WIKI_SUBTLE)
        self.fill(688, mid - 16, 56, 32, config.WIKI_BOX_BG)
        self.rect(688, mid - 16, 56, 32, config.WIKI_BORDER_STRONG)
        self.text_mid(700, mid, '검색', 14, 'bold', config.WIKI_TEXT)
        # 오른쪽 사용자 메뉴 (오른쪽 끝에서부터)
        x = config.SCREEN_W - 48
        self.text_mid(x, mid, '···', 14, 'bold', config.WIKI_TEXT)
        for s in ['로그인', '계정 만들기', '기부']:
            x -= text_width(s, 14) + 20
            self.text_mid(x, mid, s, 14, 'ui', config.WIKI_LINK)

    def toc(self, doc, y):
        # 왼쪽 목차 — 소제목에 번호를 붙여 자동으로 만든다
        x = config.WIKI_TOC_X
        w = self.text_mid(x, y, '목차', 14, 'bold', config.WIKI_TEXT)
        self.text_mid(x + w + 10, y, '숨기기', 12, 'ui', config.WIKI_LINK)
        y -= 14
        self.line(x, y, x + 180, y, 1, config.WIKI_BORDER)
        y -= 20
        self.text_mid(x, y, '처음 위치', 13, 'bold', config.WIKI_TEXT)      # 지금 보고 있는 곳 (굵게)
        h2 = h3 = 0
        for block in doc['blocks']:
            if block[0] == 'h2':
                h2, h3 = h2 + 1, 0
                y -= 26
                self.text_mid(x, y, '%d  %s' % (h2, block[1]), 13, 'ui', config.WIKI_LINK)
            elif block[0] == 'h3':
                h3 += 1
                y -= 26
                self.text_mid(x + 14, y, '%d.%d  %s' % (h2, h3, block[1]), 13, 'ui', config.WIKI_LINK)

    def title_area(self, doc, y):
        # 제목 + 언어 버튼 + 밑줄 → 탭 줄 → 표어 → 안내문
        x, r = self.left, self.right
        title_mid = y - 22
        self.text_mid(x, title_mid, doc['title'], config.WIKI_FONT_TITLE, 'ui', config.WIKI_TEXT)
        lang = '文A  ' + doc['languages']
        lw = text_width(lang, 14) + 24
        self.rect(r - lw, title_mid - 15, lw, 30, config.WIKI_BORDER_STRONG)
        self.text_mid(r - lw + 12, title_mid, lang, 14, 'bold', config.WIKI_LINK)
        y -= 48
        self.line(x, y, r, y, 1, config.WIKI_BORDER)
        # 탭: 왼쪽 문서·토론, 오른쪽 읽기·편집·역사 보기·도구. 선택된 탭은 흰 글 + 밑줄
        tab_mid = y - 18
        cx = x
        for s, active in [('문서', True), ('토론', False)]:
            w = self.text_mid(cx, tab_mid, s, 14, 'ui', config.WIKI_TEXT if active else config.WIKI_LINK)
            if active:
                self.line(cx, y - 34, cx + w, y - 34, 2, config.WIKI_TEXT)
            cx += w + 20
        cx = r
        for s, active in [('도구', False), ('역사 보기', False), ('편집', False), ('읽기', True)]:
            w = text_width(s, 14)
            cx -= w
            self.text_mid(cx, tab_mid, s, 14, 'ui', config.WIKI_TEXT if active else config.WIKI_LINK)
            if active:
                self.line(cx, y - 34, cx + w, y - 34, 2, config.WIKI_TEXT)
            cx -= 20
        y -= 36
        self.line(x, y, r, y, 1, config.WIKI_BORDER)
        y -= 8
        self.text(x, y - 16, '위키백과, 우리 모두의 백과사전.', config.WIKI_FONT_SMALL, 'ui', config.WIKI_SUBTLE)
        y -= 28
        if doc['hatnote']:
            y = self.paragraph(doc['hatnote'], x + 24, y, r - x - 24, color=config.WIKI_SUBTLE)   # 안내문 (들여쓰기)
        return y - 10

    def figure(self, fig, y):
        # 오른쪽에 뜨는 그림 틀: 테두리 + 그림(없으면 자리 표시) + 캡션. 이후 본문은 그 옆으로 흐른다
        pad = 4
        fw = fig['w'] + pad * 2
        fx = self.right - fw
        cap_w = fig['w'] - 8
        # 캡션 높이를 먼저 재려고 임시로 배치해 본다
        tmp = WikiLayout(self.height, self.titles)
        cap_bottom = tmp.paragraph(fig['caption'], 0, 0, cap_w, config.WIKI_FONT_SMALL, config.WIKI_TEXT, 18)
        fh = pad + fig['h'] + 6 + (-cap_bottom) + pad
        self.fill(fx, y - fh, fw, fh, config.WIKI_BOX_BG)
        self.rect(fx, y - fh, fw, fh, config.WIKI_BORDER)
        self.image(fx + pad, y - pad - fig['h'], fig['w'], fig['h'], fig['image'])
        self.paragraph(fig['caption'], fx + pad + 4, y - pad - fig['h'] - 6, cap_w, config.WIKI_FONT_SMALL, config.WIKI_TEXT, 18)
        self.float_bottom = y - fh - 8
        self.float_w = fw + 20

    def body(self, doc, y):
        x, w = self.left, config.WIKI_CONTENT_W
        if 'figure' in doc:
            self.figure(doc['figure'], y)
        for block in doc['blocks']:
            kind = block[0]
            if kind == 'p':
                y = self.paragraph(block[1], x, y, w) - 8
            elif kind == 'h2':
                y -= 14
                self.text_mid(x, y - 16, block[1], config.WIKI_FONT_H2, 'ui', config.WIKI_TEXT)
                y -= 36
                self.line(x, y, x + self.width_at(y, x, w), y, 1, config.WIKI_BORDER)   # 큰 소제목 밑줄
                y -= 8
            elif kind == 'h3':
                y -= 8
                self.text_mid(x, y - 12, block[1], config.WIKI_FONT_H3, 'bold', config.WIKI_TEXT)
                y -= 28
            elif kind == 'list':
                for item in block[1]:
                    self.text_mid(x + 8, y - config.WIKI_LINE_H / 2, '•', 14, 'ui', config.WIKI_TEXT)
                    y = self.paragraph(item, x + 24, y, w - 24)
                y -= 8
            elif kind == 'refs':
                for i, ref in enumerate(block[1]):
                    y = self.paragraph('%d. ↑ %s' % (i + 1, ref), x + 8, y, w - 8, config.WIKI_FONT_SMALL, config.WIKI_TEXT, 20)
                y -= 12
            elif kind == 'stub':
                y = self.box(block[1], x, y, w, 13)
        return y

    def box(self, markup, x, y, w, size):
        # 테두리 상자 안의 글 (토막글 알림·분류). 상자는 글 뒤에 그려야 하므로 자리를 먼저 잡아 둔다
        pad = 10
        at = len(self.items)
        bottom = self.paragraph(markup, x + pad, y - pad, w - pad * 2, size) - pad
        self.items.insert(at, ('rect', bottom, y, x, bottom, w, y - bottom, config.WIKI_BORDER))
        self.items.insert(at, ('fill', bottom, y, x, bottom, w, y - bottom, config.WIKI_BOX_BG))
        return bottom - 12

    def footer(self, doc, y):
        x, r = self.left, self.right
        cats = '분류: ' + ' | '.join(doc['categories'])           # 분류는 먹을 수 있는 링크가 아니라 평범한 글
        y = self.box(cats, x, y, r - x, 13)
        y -= 20
        self.line(x, y, r, y, 1, config.WIKI_BORDER)
        y -= 14
        y = self.paragraph(doc['edited'], x, y, r - x, config.WIKI_FONT_SMALL, config.WIKI_TEXT, 20)
        y = self.paragraph(doc['notice'], x, y, r - x, config.WIKI_FONT_SMALL, config.WIKI_SUBTLE, 20)
        y -= 6
        cx = x
        for s in doc['footer_links']:
            cx += self.text_mid(cx, y - 10, s, config.WIKI_FONT_SMALL, 'ui', config.WIKI_LINK) + 18
        return y - 24
