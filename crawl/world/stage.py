# 페이지(스테이지 하나) — 폭 1280, 세로로 긴 웹페이지 (PRD 10.1)
# 배경은 위키 문서(data/pages/*.json)를 위키백과 모양으로 배치한 것 (world/wiki_layout.py).
# 외전(PRD 21장)에서는 실제 웹페이지 글이 같은 형식으로 들어간다.
import copy
import json
import math
import os
import random
import re
from collections import deque

import config
from ui.draw import draw_line, draw_rect, draw_circle, fill_rect, draw_static_text, get_image, text_width
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


LINK = re.compile(r'\[\[(!?)([^\]|]+?)(?:\|(.+?))?\]\]')   # [[제목]] [[제목|표시]] [[!빨간]]


def doc_texts(doc):
    # 문서에서 표기가 들어갈 수 있는 글 전부 (안내문 + 본문 블록), 배치되는 순서대로
    texts = [doc.get('hatnote', '')]
    for block in doc['blocks']:
        texts.extend([block[1]] if isinstance(block[1], str) else block[1])
    return texts


def link_hops(site):
    # 시작 문서에서 파란 링크 몇 번 만에 갈 수 있는지 {제목: 단계} — 너비 우선 탐색 (PRD 11.3-7)
    docs = site['docs']
    hops = {site['start']: 0}
    queue = deque([site['start']])
    while queue:
        cur = queue.popleft()
        for text in doc_texts(docs[cur]):
            for m in LINK.finditer(text):
                nxt = m.group(2)
                if not m.group(1) and nxt in docs and nxt not in hops:   # 파란 링크이고 처음 닿는 문서
                    hops[nxt] = hops[cur] + 1
                    queue.append(nxt)
    return hops


def pick_goal(site):
    # 목표 후보 중 시작에서 갈 수 있고 min_hops단계 이상 떨어진 것 하나를 무작위로. {'page', 'keyword', 'hops'}
    hops = link_hops(site)
    usable = [t for t in site['targets'] if hops.get(t['page'], -1) >= site['min_hops']]
    goal = dict(random.choice(usable))
    goal['hops'] = hops[goal['page']]
    return goal


def mark_goal(doc, keyword):
    # 목표 문서의 {{키워드|대체어}} 자리 중 하나를 뽑아 <<키워드>>로 바꾼 사본 (나머지 자리는 그대로 → 대체어로 보임)
    slot = re.compile(r'\{\{' + re.escape(keyword) + r'\|(.+?)\}\}')
    count = sum(len(slot.findall(t)) for t in doc_texts(doc))
    chosen = random.randrange(count)            # 몇 번째 자리를 쓸지
    seen = [0]

    def replace(m):
        hit = seen[0] == chosen
        seen[0] += 1
        return '<<' + keyword + '>>' if hit else m.group(0)

    doc = copy.deepcopy(doc)
    if doc.get('hatnote'):
        doc['hatnote'] = slot.sub(replace, doc['hatnote'])
    for block in doc['blocks']:
        if isinstance(block[1], str):
            block[1] = slot.sub(replace, block[1])
        else:
            block[1] = [slot.sub(replace, t) for t in block[1]]
    return doc


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
        self.links = layout.links      # 파란 링크 조각 (x, y, w, h, 글, 대상 문서, 링크 번호) — 데이터 조각
        self.exit_rect = layout.exit_rect   # 다음 문서 상자 (x, 아래 y, w, h) — 페이지 출구
        self.goals = layout.goals           # 목표 키워드 조각 (x, y, w, h) — 목표 문서에만 있음
        self.time = 0.0                     # 키워드 반짝임용
        # 링크 하나(여러 조각일 수 있음)마다: 가리키는 문서, 먹었는지, 먹은 뒤 지난 시간(번쩍임용)
        self.groups = {}
        for x, y, w, h, text, target, lid in self.links:
            self.groups.setdefault(lid, {'target': target, 'eaten': False, 'age': 0.0})
        self.bursts = []               # 수집 이펙트 [x, y, 나이]

    def eat_at(self, x, y):
        # 발이 (x, y)에 착지: 아직 안 먹은 링크 조각 상자(+여유) 안이면 그 링크를 먹고 돌려준다
        m = config.COLLECT_MARGIN
        for px, py, w, h, text, target, lid in self.links:
            group = self.groups[lid]
            if not group['eaten'] and px - m <= x <= px + w + m and py - m <= y <= py + h + m:
                group['eaten'] = True
                group['age'] = 0.0
                self.bursts.append([x, y, 0.0])
                return group
        return None

    def goal_at(self, x, y):
        # 발이 목표 키워드 상자(+여유) 안에 착지했는지 — 링크와 같은 판정
        m = config.COLLECT_MARGIN
        return any(px - m <= x <= px + w + m and py - m <= y <= py + h + m for px, py, w, h in self.goals)

    def eaten_count(self):
        # 이 문서에서 먹은 링크 수 (HUD '이 문서 n/N', 출구 조건)
        return sum(group['eaten'] for group in self.groups.values())

    def slot_rects(self, n):
        # 다음 문서 상자 안 칸 n개의 위치 [(x, y, w, h)] — 왼쪽 위부터 한 줄에 EXIT_COLS칸
        bx, by, bw, bh = self.exit_rect
        pad, gap, cols = config.EXIT_PAD, config.EXIT_GAP, config.EXIT_COLS
        w = (bw - pad * 2 - gap * (cols - 1)) / cols
        h = config.EXIT_SLOT_H
        top = by + bh - pad - config.EXIT_TITLE_H              # 제목 줄 아래부터
        return [(bx + pad + (i % cols) * (w + gap), top - (i // cols + 1) * h - (i // cols) * gap, w, h)
                for i in range(n)]

    def update(self, dt):
        self.time += dt
        for group in self.groups.values():
            group['age'] += dt
        for b in self.bursts:
            b[2] += dt
        self.bursts = [b for b in self.bursts if b[2] < config.COLLECT_FX_TIME]

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
            elif kind == 'link':
                x, y, text, size, lid = item[3:]
                group = self.groups[lid]
                if group['eaten']:
                    # 먹은 링크: 하얗게 번쩍였다가 방문한 링크 색(보라)으로, 페이지 밝기로 가라앉음
                    k = min(1.0, group['age'] / config.COLLECT_FX_TIME)
                    color = tuple(int(w + (v - w) * k) for w, v in zip(config.COLOR_WHITE, config.WIKI_VISITED))
                    draw_static_text(x, y - camera.y, text, size, color, 1 + (a - 1) * k)
                else:
                    # 먹을 수 있는 링크: 페이지 글보다 밝게 (밟을 수 있다는 표시)
                    draw_static_text(x, y - camera.y, text, size, config.WIKI_LINK, config.LINK_ALPHA)
            elif kind == 'goal':
                # 목표 키워드: 금색, 밝기가 숨쉬듯 오르내리고 아래에 금색 밑줄
                x, y, text, size = item[3:]
                glow = 0.75 + 0.25 * math.sin(self.time * config.GOAL_PULSE)
                draw_static_text(x, y - camera.y, text, size, config.COLOR_GOLD, glow, 'bold')
                draw_line(x, y - camera.y - 2, x + text_width(text, size, 'bold'), y - camera.y - 2, 2, config.COLOR_GOLD, glow)
        # 수집 이펙트: 착지한 자리에서 링크 색 원이 퍼지며 사라짐
        for x, y, age in self.bursts:
            k = age / config.COLLECT_FX_TIME
            draw_circle(x, y - camera.y, 4 + config.COLLECT_FX_R * k, 2, config.WIKI_LINK, 1 - k)

    def draw_exit(self, camera, choices, need, time, fill):
        # 다음 문서 상자. need = 출구가 열리려면 더 먹어야 할 링크 수 (0이면 열림)
        # choices = [(칸에 쓸 글, 갈 문서, 뒤로인지)] — play_mode가 방문 대기열과 뒤로 기록으로 만든다
        # fill = (밟고 있는 칸의 문서, 0~1) — 그 칸이 왼쪽부터 주황으로 차오른다
        bx, by, bw, bh = self.exit_rect
        y = by - camera.y
        if y > config.SCREEN_H or y + bh < 0:
            return
        size = config.WIKI_FONT_BODY
        title_y = y + bh - config.EXIT_PAD - 18
        if need > 0:
            # 잠김: 회색 점선 상자 + 남은 수
            self.draw_dashed(bx, y, bw, bh, config.COLOR_GRAY)
            draw_static_text(bx + config.EXIT_PAD, title_y, '다음 문서', config.WIKI_FONT_H3, config.COLOR_GRAY, 1.0, 'bold')
            draw_static_text(bx + config.EXIT_PAD, y + bh / 2 - 20, '이 문서에서 링크를 %d개 더 먹으면 열립니다.' % need,
                             size, config.COLOR_GRAY)
            return
        # 열림: 주황 테두리가 깜빡이고, 칸마다 갈 문서
        glow = 0.6 + 0.4 * math.sin(time * config.EXIT_PULSE)       # 0.2 ~ 1.0 사이로 숨쉬듯
        fill_rect(bx, y, bw, bh, config.WIKI_BOX_BG, 0.8)
        draw_rect(bx, y, bw, bh, 2, config.COLOR_ORANGE, glow)
        draw_static_text(bx + config.EXIT_PAD, title_y, '다음 문서', config.WIKI_FONT_H3, config.COLOR_ORANGE, 1.0, 'bold')
        if not choices:
            draw_static_text(bx + config.EXIT_PAD, y + bh / 2 - 20, '갈 수 있는 문서가 없습니다. 링크를 더 먹어 보세요.',
                             size, config.WIKI_SUBTLE)
        for (sx, sy, w, h), (label, title, back) in zip(self.slot_rects(len(choices)), choices):
            color = config.WIKI_SUBTLE if back else config.WIKI_LINK        # 뒤로 칸은 회색, 새 문서 칸은 링크 색
            fill_rect(sx, sy - camera.y, w, h, config.COLOR_BG)
            if title == fill[0]:
                fill_rect(sx, sy - camera.y, w * fill[1], h, config.COLOR_ORANGE, 0.35)   # 연속으로 밟은 만큼 차오름
            draw_rect(sx, sy - camera.y, w, h, 1, color)
            draw_static_text(sx + 12, sy - camera.y + h / 2 - 9, label, size, color)

    def draw_dashed(self, x, y, w, h, color):
        # 점선 사각형 — EXIT_DASH 길이 토막을 한 칸씩 건너뛰며 긋는다
        d = config.EXIT_DASH
        for i in range(0, int(w), d * 2):
            draw_line(x + i, y, x + min(w, i + d), y, 1, color)
            draw_line(x + i, y + h, x + min(w, i + d), y + h, 1, color)
        for i in range(0, int(h), d * 2):
            draw_line(x, y + i, x, y + min(h, i + d), 1, color)
            draw_line(x + w, y + i, x + w, y + min(h, i + d), 1, color)

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
