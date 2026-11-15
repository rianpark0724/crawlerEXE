# HUD — 화면 좌표에 고정해서 그리는 정보 (스크롤과 무관). PRD 12장
import config
from ui.draw import fill_rect


def draw_scrollbar(camera, page_height, markers=()):
    # 오른쪽 끝 세로 스크롤바 (PRD 10.4). 트랙 = 페이지 전체, 막대 = 지금 보이는 구간
    # markers: [(월드 y, 색)] — 출구·남은 데이터 위치 점 (S05부터)
    w = config.SCROLL_W
    x = config.SCREEN_W - w
    track_h = config.SCREEN_H
    scale = track_h / page_height                       # 월드 1px → 스크롤바 몇 px
    fill_rect(x, 0, w, track_h, config.SCROLL_TRACK)    # 트랙
    thumb_h = max(config.SCROLL_MIN_THUMB, config.SCREEN_H * scale)   # 화면 높이 / 페이지 높이 비율만큼
    thumb_y = camera.y * scale                          # 화면 아래 가장자리(camera.y)의 위치
    pad = config.SCROLL_PAD
    fill_rect(x + pad, thumb_y + pad, w - pad * 2, thumb_h - pad * 2, config.SCROLL_THUMB)
    for world_y, color in markers:
        dot = w - pad * 4
        fill_rect(x + pad * 2, world_y * scale - dot / 2, dot, dot, color)
