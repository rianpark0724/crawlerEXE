# 사이트 레이아웃 공통 부분 — 문서(JSON) 글을 페이지 위 그리기 목록으로 바꾼다 (S10-1에서 위키 레이아웃에서 분리).
# 사이트마다 레이아웃 클래스(위키·뉴스·쇼핑)가 PageLayout을 이어받아 머리글·본문 꾸밈·바닥글만 따로 만든다.
# 위에서 아래로 커서(y)를 내려가며 놓는다. 좌표는 월드 좌표, y 위로 증가.
#
# 글 표기 (data/pages/<사이트>/*.json, PRD 11.2):
#   [[제목]]         링크 — 그 제목의 문서가 사이트에 있으면 파랑(데이터 조각), 없으면 빨강
#   [[제목|표시글]]  링크 대상과 화면에 보일 글이 다를 때
#   [[!단어]]        항상 빨간 링크 (없는 문서)
#   [[~말머리|글]]   낚시 링크 (뉴스 적) — '[말머리] 글'로 보이는 파란 링크지만 밟으면 물림. [[~글]]이면 말머리 없이
#   **단어**         굵게
#   [1], [출처 필요]   각주 표시 (작게, 위로)
#   {{키워드|대체어}}  목표 키워드가 들어갈 수 있는 자리. 뽑힌 자리만 키워드, 나머지는 대체어
#   <<키워드>>        뽑힌 목표 키워드 (stage.mark_goal이 뽑힌 자리를 이걸로 바꿔 둔다) — 금색, 먹으면 탈출
#
# 그리기 목록 항목: (종류, 아래 y, 위 y, ...값)  — 아래·위 y는 화면 밖 건너뛰기용
#   ('text', lo, hi, x, y, 글, 크기, 글꼴, 색)    y는 글의 아래
#   ('line', lo, hi, x1, y1, x2, y2, 두께, 색)
#   ('rect', lo, hi, x, y, w, h, 색)            테두리
#   ('fill', lo, hi, x, y, w, h, 색)            채움
#   ('image', lo, hi, x, y, w, h, 파일 이름)
#   ('link', lo, hi, x, y, 글, 크기, 링크 번호)   파란 링크 조각 — 먹었는지에 따라 색이 바뀌어 Page가 그린다
#   ('goal', lo, hi, x, y, 글, 크기)            목표 키워드 — 반짝이게 Page가 그린다
import re

import config
from ui.draw import text_width, text_height

# 링크: [[!?대상(|표시글)?]] / 굵게: **글** / 각주: [숫자] [출처 필요] / 키워드 자리 {{키워드|대체어}} / 뽑힌 키워드 <<키워드>>
TOKEN = re.compile(r'\[\[([!~]?)([^\]|]+?)(?:\|(.+?))?\]\]|\*\*(.+?)\*\*|\[(\d+|출처 필요)\]|\{\{(.+?)\|(.+?)\}\}|<<(.+?)>>')


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
            if m.group(1) == '~':
                if m.group(3):
                    shown = '[' + target + '] ' + m.group(3)       # 말머리: [충격] [단독] …
                spans.append((shown, 'bait', None))             # 낚시 링크
            else:
                spans.append((shown, 'link' if blue else 'red', target))
        elif m.group(4) is not None:
            spans.append((m.group(4), 'b', None))
        elif m.group(5) is not None:
            spans.append(('[' + m.group(5) + ']', 'ref', None))
        elif m.group(8) is not None:
            spans.append((m.group(8), 'goal', None))    # 뽑힌 목표 키워드
        else:
            spans.append((m.group(7), 'n', None))       # 뽑히지 않은 키워드 자리: 대체어로 평범하게
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


class PageLayout:
    # 사이트 공통 레이아웃. 이어받는 클래스가 아래 '꾸밈 값'을 바꾸고 build()를 만든다
    BODY_SIZE = config.WIKI_FONT_BODY      # 본문 글자 크기
    LINE_H = config.WIKI_LINE_H            # 본문 줄 높이
    REF_SIZE = config.WIKI_FONT_REF        # 각주 글자 크기
    TEXT = config.WIKI_TEXT                # 본문 글 색
    LINK = config.WIKI_LINK                # 파란 링크(먹을 수 있는 데이터) 색
    VISITED = config.WIKI_VISITED          # 먹은 링크 색
    REDLINK = config.WIKI_REDLINK          # 빨간 링크(먹을 수 없음) 색
    ALPHA = config.WIKI_ALPHA              # 페이지 글 전체 밝기 (낮을수록 크롤러가 잘 보임)
    BG = config.COLOR_BG                   # 페이지 바탕색
    CONTENT_X = config.WIKI_CONTENT_X      # 본문 왼쪽 x
    CONTENT_W = config.WIKI_CONTENT_W      # 본문 폭
    LINK_UNDERLINE = False                 # 링크에 밑줄 (뉴스처럼)

    def __init__(self, height, titles):
        self.height = height
        self.titles = titles     # 사이트에 있는 문서 제목들 — 링크를 파랑/빨강으로 가르는 기준
        self.items = []
        self.links = []          # 파란 링크 조각 위치 (x, y, w, h, 글, 대상 문서, 링크 번호) — 데이터 조각
        self.goals = []          # 목표 키워드 조각 위치 (x, y, w, h)
        self.baits = []          # 낚시 링크 조각 (x, y, w, h, 낚시 번호)
        self.paragraphs = []     # 본문 문단 (x, 아래 y, w, h, 링크·키워드 없는 평범한 문단인지) — 보호된 문단 후보
        self.exit_rect = None    # 다음 문서 상자 (x, 아래 y, w, h) — 페이지 출구
        self.nest_spot = None    # 댓글 둥지 자리 (x, y) — 댓글란이 있는 사이트(뉴스)만
        self.review_spots = []   # 낮은 별점(1–2점) 리뷰의 별 자리 (x, y) — 쇼핑몰 별점 투척
        self.reco_items = []     # 이 문서에 나온 상품 카드 {name, image} — 쇼핑몰 추천 상품
        self.link_count = 0      # 문단마다 링크 번호가 겹치지 않게 더해 주는 값
        self.float_bottom = None # 오른쪽에 떠 있는 상자(그림 틀 등)의 아래 y (그 위쪽 줄은 폭을 줄인다)
        self.float_w = 0
        self.left = self.CONTENT_X
        self.right = self.CONTENT_X + self.CONTENT_W

    def build(self, doc):
        # 문서 한 장을 배치하고 맨 아래 y를 돌려준다 (페이지 높이 계산용) — 사이트별 클래스가 만든다
        raise NotImplementedError

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
        # 오른쪽에 떠 있는 상자 옆이면 그만큼 좁게
        if self.float_bottom is not None and y > self.float_bottom and x + w > self.right - self.float_w:
            return self.right - self.float_w - x
        return w

    def paragraph(self, markup, x, y, w, size=None, color=None, line_h=None):
        # 단어 단위 줄바꿈. y는 첫 줄의 위, 돌려주는 값은 마지막 줄의 아래 (크기·색·줄 높이를 안 주면 이 사이트 본문 값)
        size = size or self.BODY_SIZE
        color = color or self.TEXT
        line_h = line_h or self.LINE_H
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

    def body_paragraph(self, markup, x, y, w):
        # 본문 문단 하나를 놓고 위치를 기록 (보호된 문단 후보). 돌려주는 값은 문단 아래 y
        top = y
        bottom = self.paragraph(markup, x, y, w)
        plain = '[[' not in markup and '{{' not in markup and '<<' not in markup
        self.paragraphs.append((x, bottom, self.width_at(top - 1, x, w), top - bottom, plain))
        return bottom

    def piece_width(self, text, kind, size):
        if kind == 'ref':
            return text_width(text, self.REF_SIZE)
        return text_width(text, size, 'bold' if kind in ('b', 'goal') else 'ui')

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
                    self.text(cx, base + size * 0.45, text, self.REF_SIZE, 'ui', self.LINK)   # 위첨자
                elif kind == 'link':
                    lid = self.link_count + n
                    self.items.append(('link', base, base + text_height(size), cx, base, text, size, lid))
                    self.links.append((cx, base, pw, text_height(size), text, target, lid))
                elif kind == 'goal':
                    self.items.append(('goal', base, base + text_height(size), cx, base, text, size))
                    self.goals.append((cx, base, pw, text_height(size)))
                elif kind == 'bait':
                    bid = self.link_count + n                 # 여러 단어로 나뉜 낚시 링크도 한 번호
                    self.items.append(('bait', base, base + text_height(size), cx, base, text, size, bid))
                    self.baits.append((cx, base, pw, text_height(size), bid))
                elif kind == 'red':
                    self.text(cx, base, text, size, 'ui', self.REDLINK)
                else:
                    self.text(cx, base, text, size, 'bold' if kind == 'b' else 'ui', color)
                cx += pw

    # ── 페이지 출구 ──
    def exit_box(self, y):
        # 본문 끝 표시 (높이 0). 다음 문서로는 먹은 링크를 갉아 구멍을 내서 간다 — 출구 상자는 없다
        # (무작위 배치·보호된 문단이 '본문이 끝나는 곳'으로 이 자리를 쓴다)
        self.exit_rect = (self.left, y - 8, self.right - self.left, 0)
        return y - 32
