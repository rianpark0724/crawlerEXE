# HUD — 화면 좌표에 고정해서 그리는 정보 (스크롤과 무관). PRD 12장
# 화면 맨 위 '브라우저 띠': 사이트가 바뀌어도 모양이 같다. 페이지는 띠 아래 창으로 보인다.
import config
from ui.draw import fill_rect, draw_rect, draw_line, draw_circle, draw_static_text, text_width, text_height


def view_h():
    # 페이지가 보이는 창의 높이 (화면 − 위쪽 띠)
    return config.SCREEN_H - config.HUD_BAR_H


def draw_scrollbar(camera, page_height, markers=()):
    # 오른쪽 끝 세로 스크롤바 (PRD 10.4). 트랙 = 페이지 전체, 막대 = 지금 보이는 구간 (띠 아래 창 높이만큼)
    # markers: [(월드 y, 색)] — 출구·남은 데이터 위치 점 (S05부터)
    w = config.SCROLL_W
    x = config.SCREEN_W - w
    track_h = view_h()
    scale = track_h / page_height                       # 월드 1px → 스크롤바 몇 px
    fill_rect(x, 0, w, track_h, config.SCROLL_TRACK)    # 트랙
    thumb_h = max(config.SCROLL_MIN_THUMB, track_h * scale)   # 창 높이 / 페이지 높이 비율만큼
    thumb_y = camera.y * scale                          # 화면 아래 가장자리(camera.y)의 위치
    pad = config.SCROLL_PAD
    fill_rect(x + pad, thumb_y + pad, w - pad * 2, thumb_h - pad * 2, config.SCROLL_THUMB)
    for world_y, color in markers:
        dot = w - pad * 4
        fill_rect(x + pad * 2, world_y * scale - dot / 2, dot, dot, color)


def draw_words(x, cy, parts):
    # [(글, 색, 굵게?)] 조각을 x부터 이어 그린다. cy = 띠의 세로 가운데. 끝난 x를 돌려준다
    for text, color, bold in parts:
        if not text:                                    # 빈 글(주소를 막 입력하기 시작할 때)은 건너뜀
            continue
        kind = 'bold' if bold else 'ui'
        draw_static_text(x, cy - text_height(config.HUD_FONT, kind) / 2, text, config.HUD_FONT, color, 1.0, kind)
        x += text_width(text, config.HUD_FONT, kind)
    return x


def draw_field(x, w, cy):
    # 입력칸 모양 (주소칸·목표칸)
    h = config.HUD_FIELD_H
    fill_rect(x, cy - h / 2, w, h, config.HUD_FIELD_BG)
    draw_rect(x, cy - h / 2, w, h, 1, config.HUD_BAR_LINE)


def draw_bar(url, goal, visited, min_pages, eaten, quota, data, loading=None):
    # 위쪽 띠: [CRAWL.EXE] [crawl:// 주소] [🔍 목표 키워드]  ……  방문 k/K  문서 n/N  DATA 07
    # loading: 새 창을 여는 중이면 0~1 — 띠 아래에 로딩 막대
    bottom = view_h()
    cy = bottom + config.HUD_BAR_H / 2                  # 띠의 세로 가운데
    fill_rect(0, bottom, config.SCREEN_W, config.HUD_BAR_H, config.HUD_BAR_BG)
    draw_line(0, bottom, config.SCREEN_W, bottom, 1, config.HUD_BAR_LINE)
    draw_words(14, cy, [('CRAWL.EXE', config.COLOR_ORANGE, True)])

    # 주소칸: 회색 crawl:/ + 사이트 주소와 문서 제목
    draw_field(config.HUD_URL_X, config.HUD_URL_W, cy)
    draw_words(config.HUD_URL_X + 10, cy, [('crawl:/', config.HUD_LABEL, False), (url, config.WIKI_TEXT, False)])

    # 목표칸: 돋보기 + 찾는 키워드 (검색어처럼)
    gx = config.HUD_GOAL_X
    draw_field(gx, config.HUD_GOAL_W, cy)
    draw_circle(gx + 15, cy + 2, 5, 1.5, config.HUD_LABEL)               # 돋보기 알
    draw_line(gx + 18.5, cy - 1.5, gx + 23, cy - 6, 1.5, config.HUD_LABEL)  # 돋보기 손잡이
    draw_words(gx + 32, cy, [('목표  ', config.HUD_LABEL, False), (goal, config.COLOR_ORANGE, True)])

    # 오른쪽: 진행 수치 — 채운 조건은 초록. 오른쪽 정렬이라 폭을 먼저 잰다
    def count(label, n, need):
        return [(label + ' ', config.HUD_LABEL, False),
                ('%d/%d' % (n, need), config.HUD_DONE if n >= need else config.WIKI_TEXT, True), ('     ', None, False)]
    parts = count('방문', visited, min_pages) + count('문서', eaten, quota) + \
        [('DATA ', config.HUD_LABEL, False), ('%02d' % data, config.COLOR_SKY, True)]
    width = sum(text_width(t, config.HUD_FONT, 'bold' if b else 'ui') for t, c, b in parts)
    x = config.SCREEN_W - config.SCROLL_W - 16 - width
    for part in parts:
        if part[1] is None:                             # 칸 띄우기
            x += text_width(part[0], config.HUD_FONT)
        else:
            x = draw_words(x, cy, [part])
    if loading is not None:
        fill_rect(0, bottom - 2, config.SCREEN_W * loading, 3, config.COLOR_ORANGE)   # 로딩 막대
