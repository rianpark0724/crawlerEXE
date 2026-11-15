# 페이지(스테이지 하나) — 폭 1280, 세로로 긴 웹페이지 (PRD 10.1)
# 배경은 위키 문서(data/pages/*.json)를 위키백과 모양으로 배치한 것 (world/wiki_layout.py).
# 외전(PRD 21장)에서는 실제 웹페이지 글이 같은 형식으로 들어간다.
import json
import os

import config
from ui.draw import draw_line, draw_rect, fill_rect, draw_static_text, get_image
from world.wiki_layout import WikiLayout


# 사이트(스테이지) JSON에 없는 항목의 기본값 (PRD 11.2 스키마)
SITE_DEFAULTS = {
    'url': '/',
    'targets': [],
    'min_pages': 1,
    'min_hops': 2,
    'page_quota': 3,
    'par_time': 60,
    'autoscroll': 0,
    'dark': False,
    'pages': {},
}


def load_site(site_id):
    # data/stages/<id>.json(사이트 설정) + data/pages/<pages_dir>/*.json(문서들)을 읽는다
    with open(os.path.join(config.STAGE_DIR, site_id + '.json'), encoding='utf-8') as f:
        site = json.load(f)
    for key, value in SITE_DEFAULTS.items():
        site.setdefault(key, value)
    folder = os.path.join(config.PAGE_DIR, site['pages_dir'])
    site['docs'] = {}                                   # 제목 → 문서
    for name in sorted(os.listdir(folder)):
        if name.endswith('.json'):
            with open(os.path.join(folder, name), encoding='utf-8') as f:
                doc = json.load(f)
            site['docs'][doc['title']] = doc
    return site


class Page:
    def __init__(self, doc, titles):
        # 문서 높이는 글 길이로 정한다: 아주 높은 페이지에 한 번 배치해 쓴 높이를 재고, 그 높이로 다시 배치
        trial = WikiLayout(config.PAGE_TRIAL_H, titles)
        used = config.PAGE_TRIAL_H - trial.build(doc)
        self.height = max(config.SCREEN_H, int(used + config.PAGE_BOTTOM_PAD))
        layout = WikiLayout(self.height, titles)
        layout.build(doc)
        self.title = doc['title']
        self.items = layout.items      # 그리기 목록 (월드 좌표)
        self.links = layout.links      # 파란 링크 조각 (x, y, w, h, 글, 대상 문서, 링크 번호) — 데이터 조각 (S05-4)

    def spawn(self):
        # 시작 위치: 문서 맨 위 가운데
        return config.SCREEN_W / 2, self.height - config.SPAWN_FROM_TOP

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
