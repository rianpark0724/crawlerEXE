# 페이지(스테이지 하나) — 폭 1280, 세로로 긴 웹페이지 (PRD 10.1)
# 배경은 위키 문서(data/pages/*.json)를 위키백과 모양으로 배치한 것 (world/wiki_layout.py).
# 외전(PRD 21장)에서는 실제 웹페이지 글이 같은 형식으로 들어간다.
import json
import os

import config
from ui.draw import draw_line, draw_rect, fill_rect, draw_static_text, get_image
from world.wiki_layout import WikiLayout


def load_doc(name):
    # data/pages/<name>.json 문서 읽기
    with open(os.path.join(config.PAGE_DIR, name + '.json'), encoding='utf-8') as f:
        return json.load(f)


class Page:
    def __init__(self, height, doc):
        self.height = height
        layout = WikiLayout(height)
        layout.build(doc)
        self.items = layout.items      # 그리기 목록 (월드 좌표)
        self.links = layout.links      # 파란 링크 단어 위치 — S05 데이터 조각 후보

    def draw(self, camera):
        bottom, top = camera.y, camera.y + config.SCREEN_H   # 화면에 보이는 월드 y 범위
        a = config.WIKI_ALPHA
        for item in self.items:
            kind, lo, hi = item[0], item[1], item[2]
            if hi < bottom or lo > top:            # 화면 밖은 그리지 않는다
                continue
            if kind == 'text':
                x, y, text, size, font, color = item[3:]
                sx, sy = camera.to_screen(x, y)
                draw_static_text(sx, sy, text, size, color, a, font)
            elif kind == 'line':
                x1, y1, x2, y2, width, color = item[3:]
                draw_line(x1, y1 - camera.y, x2, y2 - camera.y, width, color, a)
            elif kind == 'rect':
                x, y, w, h, color = item[3:]
                draw_rect(x, y - camera.y, w, h, 1, color, a)
            elif kind == 'fill':
                x, y, w, h, color = item[3:]
                fill_rect(x, y - camera.y, w, h, color)
            elif kind == 'image':
                x, y, w, h, name = item[3:]
                self.draw_image(x, y - camera.y, w, h, name, a)

    def draw_image(self, x, y, w, h, name, alpha):
        # 직접 만든 그림이 assets/images/에 있으면 그리고, 없으면 빈 자리 표시
        image = get_image(name)
        if image is not None:
            image.opacify(alpha)
            image.draw_to_origin(x, y, w, h)
        else:
            draw_rect(x, y, w, h, 1, config.WIKI_BORDER, alpha)
            draw_line(x, y, x + w, y + h, 1, config.WIKI_BORDER, alpha)     # X 표시 = 그림 들어갈 자리
            draw_line(x, y + h, x + w, y, 1, config.WIKI_BORDER, alpha)
