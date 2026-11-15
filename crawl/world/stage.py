# 페이지(스테이지 하나) — 폭 1280, 세로로 긴 웹페이지 (PRD 10.1)
# 배경은 실제로 읽을 수 있는 흐린 글. 글줄 하나 = (x, y, 글, 종류), y는 글의 아래쪽(월드 좌표).
# 스테이지 JSON에 "text"가 있으면 그것을 쓰고(S05), 없으면 시드 고정으로 위키 문서를 자동 생성한다.
# 외전(PRD 21장)에서는 실제 웹페이지 글이 이 자리에 들어간다.
import random

import config
from ui.draw import draw_rect, draw_static_text, text_width

# 자동 생성용 위키 문서 재료
TITLE = '웹 크롤러'
HEADINGS = ['개요', '동작 방식', '수집하는 정보', '크롤링 정책', '로봇 배제 표준', '차단과 격리', '같이 보기']
SENTENCES = [
    '웹 크롤러는 월드 와이드 웹을 체계적으로 탐색하는 컴퓨터 프로그램이다.',
    '크롤러는 시작 주소 목록에서 출발해 페이지 안의 하이퍼링크를 따라 다음 페이지로 이동한다.',
    '방문한 페이지의 내용은 색인을 만들기 위해 저장되고, 새로 발견한 링크는 방문 대기열에 추가된다.',
    '검색 엔진은 크롤러가 모은 데이터를 바탕으로 사용자의 질문에 맞는 문서를 찾아 준다.',
    '대부분의 사이트는 robots.txt 파일로 크롤러가 방문해도 되는 경로를 알려 준다.',
    '너무 빠르게 요청을 보내는 크롤러는 서버에 부담을 주기 때문에 차단될 수 있다.',
    '일부 보안 프로그램은 수상한 크롤러를 감지하면 접근을 막거나 격리한다.',
    '크롤러가 수집하는 정보에는 텍스트, 이미지 주소, 메타 데이터, 링크 구조 등이 있다.',
    '같은 페이지를 여러 번 방문하지 않도록 크롤러는 방문 기록을 관리한다.',
    '동적으로 생성되는 페이지는 스크립트를 실행해야 내용이 보여서 크롤링이 어렵다.',
    '크롤러는 스파이더, 봇, 웹 로봇이라고도 불린다.',
    '수집한 링크마다 우선순위를 매겨 중요한 페이지부터 방문하기도 한다.',
]
INFOBOX = ['웹 크롤러', '종류      소프트웨어 봇', '다른 이름  스파이더, 봇', '용도      색인, 수집', '천적      백신']


class Page:
    def __init__(self, height, lines=None):
        self.height = height
        self.boxes = []          # 테두리 상자 (x, y, w, h) — 정보 상자
        if lines is not None:
            self.lines = lines   # 스테이지 JSON의 글줄 (S05)
        else:
            self.lines = self.make_wiki()
            self.add_infobox()

    def make_wiki(self):
        # 제목 → (소제목 → 문단 1~2개) 반복. 문단은 문장 여러 개를 본문 폭에 맞춰 줄바꿈
        rng = random.Random(config.PAGE_SEED)      # 시드 고정 → 매번 같은 문서
        m = config.PAGE_MARGIN
        step = config.PAGE_LINE_STEP
        lines = []
        pool = []                                  # 문장 대기열 — 섞어서 차례로 쓰고, 다 쓰면 다시 섞음 (반복 줄이기)
        y = self.height - config.PAGE_TOP_GAP
        lines.append((m, y, TITLE, 'title'))
        y -= step * 2
        h = 0
        while y > 60:
            lines.append((m, y, HEADINGS[h % len(HEADINGS)], 'h'))
            h += 1
            y -= step * 1.5
            for _ in range(rng.randint(1, 2)):                     # 문단 1~2개
                picked = []
                for _ in range(rng.randint(2, 4)):                 # 문장 2~4개로 문단 하나
                    if not pool:
                        pool = SENTENCES[:]
                        rng.shuffle(pool)
                    picked.append(pool.pop())
                text = ' '.join(picked)
                for row in self.wrap(text, config.PAGE_TEXT_W, config.PAGE_FONT_P):
                    if y <= 60:
                        break
                    lines.append((m, y, row, 'p'))
                    y -= step
                y -= step * 0.6                                    # 문단 사이 여백
            y -= step * 0.6
        return lines

    def wrap(self, text, max_w, size):
        # 단어 단위로 붙여 가다가 폭을 넘으면 다음 줄로
        rows, row = [], ''
        for word in text.split(' '):
            test = word if row == '' else row + ' ' + word
            if text_width(test, size) > max_w and row != '':
                rows.append(row)
                row = word
            else:
                row = test
        if row != '':
            rows.append(row)
        return rows

    def add_infobox(self):
        # 오른쪽 위 정보 상자: 테두리 + 안쪽 글줄
        x = config.PAGE_MARGIN + config.PAGE_TEXT_W + 60
        top = self.height - config.PAGE_TOP_GAP + 24
        self.boxes.append((x, top - 150, 260, 150))
        for i, text in enumerate(INFOBOX):
            self.lines.append((x + 14, top - 34 - i * 26, text, 'h' if i == 0 else 'box'))

    def draw(self, camera):
        bottom, top = camera.y - 40, camera.y + config.SCREEN_H   # 화면에 보이는 월드 y 범위 (글 높이만큼 여유)
        for x, y, w, h in self.boxes:
            if y + h >= bottom and y <= top:
                sx, sy = camera.to_screen(x, y)
                draw_rect(sx, sy, w, h, 2, config.COLOR_PAGE_HEAD)
        for x, y, text, kind in self.lines:
            if y < bottom or y > top:                # 화면 밖 글줄은 그리지 않는다
                continue
            sx, sy = camera.to_screen(x, y)
            if kind == 'title':
                draw_static_text(sx, sy, text, config.PAGE_FONT_TITLE, config.COLOR_PAGE_HEAD)
            elif kind == 'h':
                draw_static_text(sx, sy, text, config.PAGE_FONT_H, config.COLOR_PAGE_HEAD)
            else:
                draw_static_text(sx, sy, text, config.PAGE_FONT_P, config.COLOR_PAGE_TEXT)
