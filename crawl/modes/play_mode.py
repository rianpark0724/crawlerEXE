# 플레이 화면 — 사이트(스테이지)를 읽어 시작 문서를 페이지로 만들고, 크롤러가 커서를 따라 걷는다. F1 디버그 뷰.
# 문서 이동: 페이지 끝 '다음 문서' 상자의 칸을 발로 밟는다 (PRD 11.3-3). 모든 상호작용은 크롤러로.
# 클리어: 키워드 자리에서 창이 열려 crawl://complete 결과 페이지로 — 크롤러는 화면에서 사라지지 않는다 (PRD 12).
import copy
import math
import random

from pico2d import get_events
from sdl2 import (SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE, SDLK_F1, SDLK_F2, SDL_MOUSEMOTION,
                  SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT)

import config
import game_framework
from crawler.body import Body
from crawler.ingest import Ingest
from world.camera import Camera
from world.stage import Page, load_site, pick_goal, mark_goal, LAYOUTS, fit_text
from world.crawl_page import CrawlPage
from world.objects import place_parts
from world.enemies import place_enemies, place_walls, draw_revert_arrow, RefreshBand, RevertBot, ProtectedBlock
from world.collision import leg_hit, circle_circle, circle_rect, leg_hit_rect
from world.hole import draw_hole, BitLeak
from world.comments import CommentNest
from world.ads import AdSpawner
from world.shop_enemies import Captcha, Vaccine, StarThrower, StarShot, TimeDeal, Recommender, Cart, CartRush
from ui.hud import draw_scrollbar, draw_bar
from ui.draw import draw_line, draw_rect, draw_circle, fill_circle, fill_rect, draw_static_text, text_width, begin_zoom, end_zoom
from ui import debug_view

mouse_x, mouse_y = 0.0, 0.0   # 커서 위치 (화면 좌표, y 위로 증가) — 커서 그리기용
target_x, target_y = 0.0, 0.0 # 커서 위치 (월드 좌표) — 크롤러 목표
body = None                   # 크롤러 몸
left_down = False             # 좌클릭을 누르고 있는지 (질주)
camera = None
page = None
site = None                   # 지금 사이트 (설정 + 문서들, dict)
data_count = 0                # 먹은 데이터(링크) 수 — 문서를 넘어가도 유지
ingest = Ingest()             # 링크 섭취 연출 + 몸에 저장된 단어 (문서를 넘어가도 유지)
frontier = []                 # 방문 대기열: 먹었지만 아직 안 간 문서 제목들 (PRD 11.3)
visited = []                  # 방문한 문서 제목들 (순서대로)
goal = None                   # 이번 판 목표 {'page': 문서, 'keyword': 키워드, 'hops': 시작에서 몇 단계}
cleared = False               # 목표 키워드를 먹고 탈출했는지
clear_timer = 0.0             # 키워드를 먹은 뒤 탈출 창이 열리기까지 남은 시간
clear_spot = None             # 먹은 키워드 상자 (x, y, w, h) — 탈출 창이 여기서 열린다
lost = False                  # 다리를 모두 잃었는지 (GAME OVER)
lost_timer = 0.0              # 다리를 모두 잃은 뒤 crawl://lost 창이 열리기까지 남은 시간
lost_doc = ''                 # 다리를 모두 잃은 문서 (결과 페이지 표시용)
frozen = [False]              # '응답 없음' — 화면이 굳어 크롤러·카메라가 움직이지 않음
arrive_hole = [0.0]           # 구멍으로 들어온 새 문서 맨 위의 도착 구멍이 메워지기까지 남은 시간
chew_ready = [None]           # 이 문서에서 껍데기를 갉을 수 있게 되는 시각 (링크를 다 먹은 순간 + CHEW_UNLOCK)
leak = BitLeak()              # 구멍에서 새어 나오는 0·1 조각
leak_timer = [0.0]
chew_jolt = [0.0]             # 갉을 때마다 구멍이 흔들리는 남은 시간
death_spot = (0.0, 0.0)       # 확대된 화면에서 머리가 보이는 위치 (빨간 창이 여기서 열림)
messages = []                 # 떠오르는 글 [x, y, 글, 나이] (월드 좌표) — '크롤링이 부족합니다'
pages = {}                    # 한 번 연 문서의 Page (제목 → Page) — 다시 와도 먹은 링크가 보라로 남게
history = []                  # 지나온 문서 제목들 — '뒤로' 칸이 마지막 것으로 간다
footprints = []               # 이 문서의 발자국 [(x, y) 또는 None(WAVE로 끊김)] — 되돌리기 봇이 따라옴
next_doc = None               # 이번 프레임에 다 채운 칸 (할 일, 칸 위치) — 걷기 처리가 끝난 뒤 창 열기 시작
opening = None                # 새 창이 열리는 중: {'action', 'name'(창 제목), 'url', 'rect'(시작 칸, 월드), 'color', 't'}
checkpoint = None             # 지금 사이트에 들어올 때의 {몸, 데이터, 저장 조각} — 죽으면 여기서 다시
play_time = 0.0               # 플레이 시간 (출구 깜빡임 등)
fade = 0.0                    # 문서를 옮긴 뒤 남은 밝아짐 시간
hit_stop = 0.0                # 피격 순간 멈칫이 남은 시간 (이동안 게임이 멈춤)
shake = 0.0                   # 화면 흔들림이 남은 시간
data_flash = 0.0              # 데이터를 잃어 띠의 DATA가 빨갛게 깜빡이는 시간
charge = {'key': None, 'n': 0, 'time': 0.0}     # 칸 채우기: 어느 칸을, 몇 번 연속 밟았는지, 마지막 착지 시각


def init(start='home'):
    # 새 판: crawl://home에서 시작 (개발용으로 사이트 이름을 주면 그 사이트부터).
    # 몸·데이터·시간은 판 전체에 이어진다 — 사이트를 넘어가도 그대로 (S10-7)
    global mouse_x, mouse_y, left_down, body, data_count, ingest, play_time
    left_down = False
    body = None                                     # 새 판: 시작 마디 수로
    data_count, play_time = 0, 0.0
    ingest = Ingest()                               # 새 판: 몸은 비어서 시작
    random.seed(config.RANDOM_SEED)                 # None이면 매번 다른 판
    mouse_x, mouse_y = config.SCREEN_W / 2, config.SCREEN_H / 2   # 첫 마우스 이벤트 전에는 화면 가운데
    if start == 'home':
        open_home()
    else:
        enter_site(start)


def reset_site(site_id):
    # 사이트 하나의 상태를 새로 (몸·데이터·시간은 건드리지 않음)
    global site, frontier, visited, pages, history, next_doc, opening, cleared, messages, clear_timer, clear_spot, lost, lost_timer
    chew_jolt[0] = 0.0
    site = load_site(site_id)
    frontier, visited, pages, history, next_doc, opening = [], [], {}, [], None, None
    cleared, messages, clear_timer, clear_spot = False, [], 0.0, None
    lost, lost_timer = False, 0.0
    frozen[0] = False


def enter_site(site_id):
    # 사이트에 들어간다: 목표를 새로 뽑고, 들어오는 순간의 몸·데이터를 체크포인트로 (죽으면 여기서 다시)
    global goal, checkpoint
    reset_site(site_id)
    goal = pick_goal(site)                          # 시작에서 min_hops단계 이상 떨어진 후보 중 하나
    checkpoint = {'body': copy.deepcopy(body), 'data': data_count, 'stored': list(ingest.stored)}
    open_doc(site['start'])                         # 시작 문서 맨 위에서 출발


def restart_site():
    # 다시 크롤링: 이 사이트에 들어올 때의 몸·데이터로 처음부터 (시간은 계속 흐름)
    global body, data_count, ingest
    body = copy.deepcopy(checkpoint['body'])        # None이면 시작 몸
    data_count = checkpoint['data']
    ingest = Ingest()
    ingest.stored = list(checkpoint['stored'])
    enter_site(site['id'])


def next_site():
    # 다음 사이트로: 몸·데이터를 그대로 가지고 (STAGE_ORDER 순서)
    order = config.STAGE_ORDER
    enter_site(order[order.index(site['id']) + 1])


def open_home():
    # crawl://home — 게임의 시작 페이지. 크롤러가 걸어 다니며 '크롤링 시작'이나 '종료' 칸을 밟는다
    global goal
    reset_site(config.STAGE_ORDER[0])               # 띠(HUD)가 쓰는 사이트 값 (홈 자체는 사이트가 아님)
    goal = {'page': None, 'keyword': '-', 'hops': 0}
    names = [load_site(s)['name'] for s in config.STAGE_ORDER]
    lines = [('CRAWL.EXE', 52, config.COLOR_ORANGE, True),
             ('웹페이지 위를 기어 다니며 링크를 먹고 사는 크롤러', 16, config.WIKI_TEXT, False),
             ('  →  '.join(names), 20, config.COLOR_SKY, True),
             ('사이트마다 목표 키워드를 찾아 먹으면 다음 사이트로 — 몸과 데이터는 이어집니다', 14, config.HUD_LABEL, False),
             ('마우스 이동 · 좌클릭 질주 · 우클릭 WAVE 돌진 · 발로 링크를 밟아 먹기', 13, config.HUD_LABEL, False)]
    slots = [{'label': '크롤링 시작', 'key': 'start', 'action': ('start',), 'enabled': True},
             {'label': '종료', 'key': 'quit', 'action': ('quit',), 'enabled': True}]
    show_page(CrawlPage('home', lines, slots))


def show_page(new_page):
    # 페이지를 화면에 띄우고 그 페이지 맨 위에 크롤러를 세운다 (문서·crawl:// 페이지 공통)
    global page, camera, body, target_x, target_y, fade, charge, footprints
    charge = {'key': None, 'n': 0, 'time': 0.0}
    chew_ready[0] = None                            # 새 문서는 다시 링크를 먹어야 갉을 수 있음
    leak.bits.clear()
    footprints = []                                 # 발자국은 문서마다 새로
    page = new_page
    camera = Camera(page.height)                    # 페이지 맨 위에서 시작
    target_x, target_y = camera.to_world(mouse_x, mouse_y)
    if body is None:
        body = Body(*page.spawn())                  # 새 판: 시작 몸
    else:
        body.place(*page.spawn())                   # 문서 이동: 같은 몸을 맨 위에 다시 세움 (자란 마디·잃은 다리 유지)
    body.on_land = on_land                          # 착지 이벤트 연결
    fade = config.PAGE_FADE_TIME


def open_doc(title):
    # 사이트 문서를 연다. 처음 여는 문서면 Page를 만들어 보관
    if title not in pages:
        doc = site['docs'][title]
        if title == goal['page']:
            doc = mark_goal(doc, goal['keyword'])   # 목표 문서: 키워드 자리 중 하나를 뽑아 금색 키워드로
        pages[title] = Page(doc, set(site['docs']), LAYOUTS[site['layout']])  # 링크 색은 사이트의 문서 제목으로, 모양은 사이트 layout으로
        counts = site['pages'].get(title, {}).get('parts', {})   # 이 문서의 파츠 종류별 개수 (사이트 JSON)
        pages[title].parts = place_parts(pages[title], counts)  # 위치는 무작위 (처음 열 때 한 번)
        enemies = site['pages'].get(title, {}).get('enemies', {})   # 이 문서의 적 종류별 개수
        pages[title].enemies = place_enemies(pages[title], enemies)
        pages[title].enemies += place_walls(pages[title], site['pages'].get(title, {}).get('protect', 0))   # 보호된 문단
        for beam in site['pages'].get(title, {}).get('beams', []):   # 새로 고침 띠 (주기·어긋남은 문서 설정)
            pages[title].enemies.append(RefreshBand(beam.get('period', config.BAND_PERIOD), beam.get('offset', 0.0)))
    if title not in visited:
        visited.append(title)                       # 방문 수 (HUD 방문 k/K)
    if title in frontier:
        frontier.remove(title)                      # 갔으니 방문 대기열에서 뺀다
    for enemy in pages[title].enemies:
        if isinstance(enemy, RefreshBand):
            enemy.reset()                           # 띠는 들어올 때마다 처음부터 (경고 없이 오지 않게)
    show_page(pages[title])


def open_complete():
    # 결과 페이지 crawl://complete — 크롤러가 걸어 다니며 다음 사이트·다시·홈 칸을 밟는다. 마지막 사이트면 판 끝
    order = config.STAGE_ORDER
    last = site['id'] not in order or order.index(site['id']) == len(order) - 1
    lines = [('ALL SITES CRAWLED' if last else 'CRAWL COMPLETE', 34, config.COLOR_GOLD, True),
             ('"%s" — %s%s 에서 찾음' % (goal['keyword'], site['url'], goal['page']), 16, config.WIKI_TEXT, False),
             ('전체 시간 %d:%02d  ·  데이터 %d  ·  방문 %d' % (play_time // 60, play_time % 60, data_count, len(visited)), 16, config.WIKI_TEXT, False),
             ('경로  ' + ' → '.join(visited), 13, config.HUD_LABEL, False)]
    if last:
        slots = [{'label': '처음부터', 'key': 'start', 'action': ('start',), 'enabled': True},
                 {'label': '홈', 'key': 'home', 'action': ('home',), 'enabled': True}]
    else:
        nxt = load_site(order[order.index(site['id']) + 1])['name']
        slots = [{'label': '다음: ' + nxt, 'key': 'next', 'action': ('next',), 'enabled': True},
                 {'label': '다시 크롤링', 'key': 'restart', 'action': ('restart',), 'enabled': True},
                 {'label': '홈', 'key': 'home', 'action': ('home',), 'enabled': True}]
    show_page(CrawlPage('complete', lines, slots))


def open_lost():
    # 결과 페이지 crawl://lost — 크롤러는 시작 몸으로 다시 나타나 '다시 크롤링' 칸을 밟는다 (사라지지 않음)
    global body
    lines = [('예외', 'LegNotFound: 남은 다리 0개', config.COLOR_RED),
             ('상태', 'CRAWL.EXE가 응답하지 않아 종료되었습니다', config.WIKI_TEXT),
             ('위치', site['url'] + lost_doc, config.WIKI_TEXT),
             ('시간', '%d:%02d' % (play_time // 60, play_time % 60), config.WIKI_TEXT),
             ('데이터', '%d개 유실' % data_count, config.COLOR_SKY),
             ('경로', ' → '.join(visited), config.HUD_LABEL)]
    slots = [{'label': '다시 크롤링', 'key': 'restart', 'action': ('restart',), 'enabled': True},
             {'label': '홈', 'key': 'home', 'action': ('home',), 'enabled': True}]
    body = None                                     # 시작 몸으로 다시 나타남
    frozen[0] = False                               # '응답 없음' 풀림
    show_page(CrawlPage('lost', lines, slots, 'report'))
    global fade
    fade = 0.0                                      # 찢어진 화면 뒤 곧바로 (밝아지는 연출 없이)


def exit_need():
    # 출구가 열리려면 이 문서에서 더 먹어야 할 링크 수 (문서의 링크가 page_quota보다 적으면 전부)
    quota = min(site['page_quota'], len(page.groups))
    return max(0, quota - page.eaten_count())


def exit_choices():
    # 다음 문서 상자의 칸들 [(글, 문서, 뒤로인지)]: 방문 대기열(먹은 순서) + 뒤로(지나온 문서가 있으면)
    n = config.EXIT_ROWS * config.EXIT_COLS
    choices = [('→ ' + t, t, False) for t in frontier[:n - 1]]
    if history:
        choices.append(('← 뒤로: ' + history[-1], history[-1], True))
    return choices


def slot_list():
    # 지금 페이지에서 밟을 수 있는 칸들 → ([(구분 이름, 할 일, 열렸는지)], [칸 위치]) — crawl:// 페이지의 메뉴 칸
    if isinstance(page, CrawlPage):
        return [(s['key'], s['action'], s['enabled']) for s in page.slots], page.slot_rects()
    return [], []


def chew_spots():
    # 갉을 수 있는 곳 [(구분 이름, 상자 (x, y, w, h), 할 일, 보일 글)]: 이 문서에서 링크를 page_quota개 먹으면
    # 먹은 링크 껍데기마다 그 링크의 문서로 가는 구멍 자리가 된다. 지나온 문서가 있으면 왼쪽 위에 '← 뒤로' 껍데기
    if isinstance(page, CrawlPage) or exit_need() > 0 or chew_ready[0] is None or play_time < chew_ready[0]:
        return []                                    # 아직 덜 먹었거나, 다 먹은 직후의 텀 (먹자마자 떠나지 않게)
    if robot_check() is not None:
        return []                                    # 로봇 확인 중엔 갉을 수도 없음
    boxes = {}
    for x, y, w, h, text, target, lid in page.links:
        group = page.groups[lid]
        if group['eaten'] and group['age'] >= config.CHEW_FRESH and target != page.title:   # 막 먹은 링크는 아직
            if lid in boxes:                         # 여러 조각 링크: 상자를 합침
                bx, by, bw, bh, t, tg = boxes[lid]
                x2, y2 = max(bx + bw, x + w), max(by + bh, y + h)
                bx, by = min(bx, x), min(by, y)
                boxes[lid] = (bx, by, x2 - bx, y2 - by, t + ' ' + text, tg)
            else:
                boxes[lid] = (x, y, w, h, text, target)
    spots = [(lid, (x, y, w, h), ('doc', target, False), text) for lid, (x, y, w, h, text, target) in boxes.items()]
    if history:
        bx, from_top, bw, bh = config.BACK_SPOT
        spots.append(('back', (bx, page.height - from_top, bw, bh), ('doc', history[-1], True), '← 뒤로: ' + history[-1]))
    return spots


def finish():
    global body, camera, page, site
    body = None
    camera = None
    page = None
    site = None


def handle_events():
    global mouse_x, mouse_y, left_down
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_F1:
            debug_view.toggle()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_F2:
            toggle_hazard(*camera.to_world(mouse_x, mouse_y))   # 시험용 위험 지점 만들기/지우기 (S08) — 누른 순간의 커서 자리
        elif event.type == SDL_MOUSEMOTION:
            # 마우스 이벤트 y는 위가 0 → 아래가 0인 pico2d 좌표로 뒤집는다
            mouse_x = event.x
            mouse_y = config.SCREEN_H - 1 - event.y
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            left_down = True
        elif event.type == SDL_MOUSEBUTTONUP and event.button == SDL_BUTTON_LEFT:
            left_down = False
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_RIGHT:
            if body.start_wave(target_x, target_y):   # □ WAVE 점프 돌진 (재사용 대기 중이면 무시)
                footprints.append(None)               # 뛰면 발자국이 끊긴다 (되돌리기 봇이 길을 잃음)


def check_hits():
    # 위험 지점에 닿은 다리를 자르거나(−1) 마디에 닿으면 다리 2개를 잃는다 (PRD 5.4)
    # 한 번 맞으면 멈칫 + 화면 흔들림 + 1초 무적(깜빡임) — 무적 동안·WAVE 공중 마디는 안 맞음
    global hit_stop, shake
    # 위험한 것: 원 (x, y, r) — F2 위험 지점·되돌리기 봇 / 사각형 (x, y, w, h) — 새로 고침 띠
    dangers = [('circle', (x, y, r), None) for x, y, r in page.hazards]
    for e in page.enemies:
        if isinstance(e, RevertBot):
            dangers.append(('circle', (e.x, e.y, config.REVERT_R), e))
        elif isinstance(e, (RefreshBand, ProtectedBlock)) and e.rect(camera) is not None:
            dangers.append(('rect', e.rect(camera), e))
        elif isinstance(e, AdSpawner):
            dangers += [('rect', ad.rect(), ad) for ad in e.slamming()]   # 광고가 떨어지는 순간만 맞음
        elif isinstance(e, StarThrower):
            dangers += [('circle', (s.x, s.y, config.STAR_R), s) for s in e.shots]   # 날아오는 화난 별
        elif isinstance(e, CartRush):
            dangers += [('rect', c.rect(), c) for c in e.rolling()]     # 굴러오는 카트
        elif isinstance(e, Captcha):
            dangers += [('circle', (*v.tip(), config.VAC_TIP_R), v) for v in e.stabbing()]   # 찌르러 오는 백신 바늘
    for shape, d, enemy in dangers:
        if shape == 'circle':
            hit_seg = lambda seg, r_seg, d=d: circle_circle(d[0], d[1], d[2], seg.x, seg.y, r_seg)
            hit_leg = lambda leg, d=d: leg_hit(leg, *d)
            cx, cy = d[0], d[1]                             # 잘린 다리가 튕겨 나갈 기준
        else:
            hit_seg = lambda seg, r_seg, d=d: circle_rect(seg.x, seg.y, r_seg, *d)
            hit_leg = lambda leg, d=d: leg_hit_rect(leg, *d)
            cx, cy = None, d[1] + d[3] / 2                  # 띠: 위아래 방향으로 튕김
        for i, seg in enumerate(body.segs):
            if not body.hit_ok(i):
                continue
            fx = seg.x if cx is None else cx
            if hit_seg(seg, body.seg_size(i) / 2):
                body.lose_legs(config.BODY_HIT_LEGS, fx, cy)  # 몸통 피격: 꼬리 쪽 다리부터 2개
                seg.flash = config.HIT_FLASH                # 맞은 마디가 번쩍
            else:
                legs = [leg for leg in seg.legs if hit_leg(leg)]
                if not legs:
                    continue
                body.cut_leg(legs[0], legs[0].knee_x if cx is None else cx, cy)   # 다리 피격: 닿은 다리 하나
            body.iframe = config.HIT_IFRAME
            hit_stop, shake = config.HIT_STOP, config.SHAKE_TIME
            if isinstance(enemy, RevertBot):
                enemy.react(config.REVERT_HIT_PAUSE)        # 봇: 잘라 낸 뒤 한동안 멈춤
            if isinstance(enemy, ProtectedBlock):
                body.knock(*enemy.push_dir(seg.x, seg.y))   # 보호된 문단: 바깥쪽으로 튕겨 나감
            if isinstance(enemy, StarShot):
                enemy.dead = True                           # 맞힌 별은 사라짐
            if isinstance(enemy, Cart):
                enemy.grab()                                # 카트에 실려 화면 끝까지 밀려감
            if isinstance(enemy, Vaccine):
                enemy.hit()                                 # 찌른 백신은 멈칫
            return                                          # 한 번에 한 번만 맞음


def push_out_walls():
    # 보호된 문단은 벽: 무적 중이라도 머리가 안으로 파고들면 가장 가까운 변 바깥으로 밀어낸다
    head = body.segs[0]
    r = body.seg_size(0) / 2
    walls = [e for e in page.enemies if isinstance(e, ProtectedBlock)]
    for e in page.enemies:
        if isinstance(e, (AdSpawner, Recommender)):
            walls += e.walls()                        # 떨어진 광고·추천 상품 카드도 벽
    for e in walls:
        if circle_rect(head.x, head.y, r, *e.rect()):
            dx, dy = e.push_dir(head.x, head.y)
            if dx:
                head.x = e.x - r if dx < 0 else e.x + e.w + r
            else:
                head.y = e.y - r if dy < 0 else e.y + e.h + r


def link_pieces(group):
    # 링크 하나(여러 조각일 수 있음)의 조각들 [(x, y, 글, 크기)] — 섭취·되돌림 글자 연출용
    lids = [lid for lid, g in page.groups.items() if g is group]
    sizes = {item[7]: item[6] for item in page.items if item[0] == 'link'}
    return [(x, y, text, sizes.get(lid, config.WIKI_FONT_BODY)) for x, y, w, h, text, target, lid in page.links if lid in lids]


def robot_check():
    # 이 문서에 떠 있는 캡차 판 (없으면 None)
    for e in page.enemies:
        if isinstance(e, Captcha) and e.blocking():
            return e
    return None


def shop_eat(group):
    # 쇼핑몰 적이 링크 먹기에 반응: 캡차는 먹은 시각을 세고, 타임딜 링크면 보너스
    global data_count
    for e in page.enemies:
        if isinstance(e, Captcha):
            e.note_eat(play_time, body, page)
        elif isinstance(e, TimeDeal) and not e.done and page.groups[e.lid] is group:
            e.done = True
            data_count += config.DEAL_BONUS
            messages.append([e.x + 40, e.y + 24, '타임딜! +%d' % (1 + config.DEAL_BONUS), 0.0])


def bitten(leg):
    # 낚시 링크를 밟음 (PRD 9 뉴스): 턱이 다물려 그 다리가 잘리고, 이 문서에서 먹은 링크 하나를 토해 낸다 (데이터 -1)
    global hit_stop, shake
    seg_i = next((i for i, seg in enumerate(body.segs) if leg in seg.legs), 0)
    if body.hit_ok(seg_i):                            # 무적·공중이면 다리는 무사 (데이터는 그래도 뺏김)
        body.cut_leg(leg, leg.foot_x, leg.foot_y + 10)
        body.iframe = config.HIT_IFRAME
        hit_stop, shake = config.HIT_STOP, config.SHAKE_TIME
    eaten = [g for g in page.groups.values() if g['eaten']]
    if eaten:
        lose_link(min(eaten, key=lambda g: g['age']))   # 가장 최근에 먹은 링크
        messages.append([leg.foot_x, leg.foot_y + 20, '낚였다! -1', 0.0])
    else:
        messages.append([leg.foot_x, leg.foot_y + 20, '낚였다!', 0.0])


def lose_link(group):
    # 먹은 링크를 잃음 (되돌리기 봇·낚시 링크): 다시 파란 링크로, 데이터 -1, 몸에서 그 단어가 빠져나가 링크로 돌아감
    global data_count, data_flash
    page.revert(group)
    data_count = max(0, data_count - 1)
    head = body.segs[0]
    ingest.spit(link_pieces(group), head.x, head.y)
    data_flash = config.DATA_FLASH
    # 같은 문서를 가리키는 먹힌 링크가 어디에도 없으면 방문 대기열에서 뺀다
    still = any(g['eaten'] and g['target'] == group['target'] for p in pages.values() for g in p.groups.values())
    if not still and group['target'] in frontier:
        frontier.remove(group['target'])


def check_reverts():
    # 추적 중인 되돌리기 봇이 먹힌 링크 근처를 지나면 그 링크를 되돌린다 (PRD 9): 데이터 −1, 이 문서 수집 −1
    m = config.REVERT_LINK_R
    for enemy in page.enemies:
        if not isinstance(enemy, RevertBot) or enemy.state != 'track' or enemy.pause > 0:
            continue
        for x, y, w, h, text, target, lid in page.links:
            group = page.groups[lid]
            if group['eaten'] and x - m <= enemy.x <= x + w + m and y - m <= enemy.y <= y + h + m:
                lose_link(group)                      # 데이터 -1, 몸에서 그 단어가 빠져나가 링크로 돌아감
                enemy.react()
                messages.append([x + w / 2, y + h + 10, '되돌림 -1', 0.0])   # (− 기호는 굵은 글꼴에 없어 -)
                break


def toggle_hazard(x, y):
    # F2: (x, y)에 위험 지점이 있으면 지우고, 없으면 만든다 — 적이 생기기 전(S09) 피격 시험용
    r = config.HIT_TEST_R
    for h in page.hazards:
        if math.hypot(h[0] - x, h[1] - y) <= h[2]:
            page.hazards.remove(h)
            return
    page.hazards.append([x, y, r])


def draw_hazards():
    # 위험 지점: 빨간 원 두 겹이 숨쉬듯 (바닥에 그려진 판정 범위 그대로)
    pulse = 0.5 + 0.5 * math.sin(play_time * 5)
    for x, y, r in page.hazards:
        sx, sy = camera.to_screen(x, y)
        fill_rect(sx - 2, sy - 2, 4, 4, config.COLOR_RED)
        draw_circle(sx, sy, r, 2, config.COLOR_RED, 0.8)
        draw_circle(sx, sy, r + 3 * pulse, 1, config.COLOR_RED, 0.3)


def on_land(leg):
    # 발이 착지한 순간 한 번: 그 자리의 파란 링크를 먹는다 (몸통은 먹지 못함 — 발 착지만 판정)
    global data_count, next_doc, cleared, clear_timer, clear_spot, shake
    debug_view.note_landing(leg.foot_x, leg.foot_y)
    # 발자국 = 지나간 길: 착지할 때 머리 자리를, 마지막 발자국에서 FOOTPRINT_GAP 이상 움직였으면 기록
    head = body.segs[0]
    last = footprints[-1] if footprints else None
    if last is None or math.hypot(head.x - last[0], head.y - last[1]) >= config.FOOTPRINT_GAP:
        footprints.append((head.x, head.y))           # (WAVE 끊김 뒤 첫 발자국도 새로 시작)
    for enemy in page.enemies:                        # 떨어져 어리둥절한 댓글 벌레를 밟으면 터짐
        if isinstance(enemy, CommentNest) and enemy.stomp(leg.foot_x, leg.foot_y):
            leak.emit(leg.foot_x, leg.foot_y, 4)
            break
    for enemy in page.enemies:                        # 광고 닫기 칸을 디딤
        if isinstance(enemy, AdSpawner) and any(ad.step_close(leg.foot_x, leg.foot_y) for ad in enemy.ads):
            return
    if len(footprints) > config.FOOTPRINT_MAX:
        del footprints[0]
        for enemy in page.enemies:                    # 버린 만큼 봇이 읽을 번호도 당긴다
            if isinstance(enemy, RevertBot):
                enemy.step = max(0, enemy.step - 1)
    if page.goal_at(leg.foot_x, leg.foot_y) and not cleared:
        if len(visited) >= site['min_pages']:
            cleared = True                            # 탈출! (PRD 11.3-4) — 잠시 뒤 키워드 자리에서 창이 열린다
            clear_timer, clear_spot = config.CLEAR_DELAY, page.goals[0]
        elif not messages:                            # 모자라면 알림만 (키워드는 남아 다시 먹을 수 있음)
            messages.append([leg.foot_x, leg.foot_y + 20, '크롤링이 부족합니다 (방문 %d/%d)' % (len(visited), site['min_pages']), 0.0])
        return
    part = page.part_at(leg.foot_x, leg.foot_y)
    if part is not None and body.can_grow():         # 최대(마디 6)면 줍지 않고 남겨 둔다
        part.taken = True                             # 다리 파츠 획득 → 꼬리에 마디 1 + 다리 2
        body.grow()
        page.bursts.append([part.x, part.y, 0.0])
        return
    if not isinstance(page, CrawlPage) and page.bait_at(leg.foot_x, leg.foot_y) is not None:
        bitten(leg)                                   # 낚시 링크에 물림
        return
    if robot_check() is not None:
        return                                        # 로봇 확인 중: 링크를 먹을 수 없음 (판의 칸을 골라 풀어야 함)
    group = page.eat_at(leg.foot_x, leg.foot_y)
    if group is not None:
        data_count += 1
        shop_eat(group)
        ingest.eat(link_pieces(group), leg.foot_x, leg.foot_y)   # 글자가 떨어져 나와 머리로 빨려 들어감
        for enemy in page.enemies:                    # 링크를 먹으면 되돌리기 봇이 깨어나 지금 발자국부터 따라옴
            if isinstance(enemy, RevertBot):
                enemy.wake(len(footprints) - 1)
        if group['target'] not in visited and group['target'] not in frontier:
            frontier.append(group['target'])          # 먹은 링크의 문서 → 방문 대기열
        return
    if next_doc is not None or opening is not None or ((cleared or lost) and not isinstance(page, CrawlPage)):
        return                                        # 탈출 창이 열리기 직전에는 다른 칸을 밟지 않게
    # 먹은 링크 껍데기 갉기: 같은 껍데기를 CHEW_STEPS번 이어서 디디면 구멍이 뚫려 그 문서로 떨어진다
    m = config.CHEW_MARGIN
    for key, (x, y, w, h), action, text in chew_spots():
        if x - m <= leg.foot_x <= x + w + m and y - m <= leg.foot_y <= y + h + m:
            if charge['key'] == key and play_time - charge['time'] < config.CHEW_FORGET:
                charge['n'] += 1
            else:
                charge['key'], charge['n'] = key, 1
            charge['time'] = play_time
            ingest.crumbs(text, x + w / 2, y + h / 2, leg.foot_x, leg.foot_y, 3)   # 부스러기가 머리로
            chew_jolt[0] = config.CHEW_JOLT               # 뜯길 때마다 구멍이 흔들리고
            shake = max(shake, config.CHEW_JOLT)          # 화면도 살짝 (흔들림 폭은 남은 시간에 비례 → 피격보다 약함)
            leak.emit(x + w / 2, y + h / 2, config.CHEW_BURST)   # 0·1이 확 튀어 나옴
            if charge['n'] >= config.CHEW_STEPS:
                next_doc = (action, (x, y, w, h))
            return
    # 칸(crawl:// 페이지의 메뉴 칸)에 착지했는지
    slots, rects = slot_list()
    for (key, action, enabled), (sx, sy, w, h) in zip(slots, rects):
        if enabled and sx <= leg.foot_x <= sx + w and sy <= leg.foot_y <= sy + h:   # 여유 없이 칸 안
            if charge['key'] == key and play_time - charge['time'] < config.EXIT_FORGET:
                charge['n'] += 1                      # 같은 칸을 이어서 밟음
            else:
                charge['key'], charge['n'] = key, 1   # 다른 칸이거나 한참 만에 → 처음부터
            charge['time'] = play_time
            if charge['n'] >= config.EXIT_STEPS:
                next_doc = (action, (sx, sy, w, h))   # 걷기 처리 중이므로 프레임 끝에 창 열기 시작
            return


def exit_fill():
    # 밟고 있는 칸이 얼마나 찼는지: (구분 이름, 0~1). 한참 안 밟았으면 비워짐
    if charge['key'] is None or play_time - charge['time'] >= config.EXIT_FORGET:
        return None, 0.0
    return charge['key'], charge['n'] / config.EXIT_STEPS


def chew_fill():
    # 갉고 있는 껍데기와 구멍 크기 0~1 (한참 안 디디면 비워짐)
    if charge['key'] is None or play_time - charge['time'] >= config.CHEW_FORGET:
        return None, 0.0
    return charge['key'], min(1.0, charge['n'] / config.CHEW_STEPS)


def update_leak():
    # 갉는 중인 구멍·도착 구멍에서 0·1이 조금씩 새어 나온다
    leak.update(game_framework.frame_time)
    leak_timer[0] -= game_framework.frame_time
    if leak_timer[0] > 0:
        return
    leak_timer[0] = config.LEAK_RATE
    key, k = chew_fill()
    for skey, (x, y, w, h), action, text in chew_spots():
        if skey == key and k > 0:
            leak.emit(x + w / 2, y + h / 2, 1 + int(k * 2))
    if arrive_hole[0] > 0 and not isinstance(page, CrawlPage):
        sx, sy = page.spawn()
        leak.emit(sx, sy, 2)


def draw_chew_spots():
    # 갉을 수 있는 껍데기: 주황 점선 테두리가 숨쉬듯 / 갉는 중이면 껍데기 가운데 검은 구멍이 커짐 (가장자리는 들쭉날쭉)
    spots = chew_spots()
    key, k = chew_fill()
    pulse = 0.5 + 0.5 * math.sin(play_time * 5)
    for n, (skey, (x, y, w, h), action, text) in enumerate(spots):
        sy = y - camera.y
        reveal = (play_time - chew_ready[0]) / config.CHEW_REVEAL - n * 0.25   # 열릴 때 껍데기마다 차례로 나타남
        if reveal <= 0:
            continue
        if skey == 'back':                          # '← 뒤로' 껍데기 글
            draw_static_text(x + 4, sy + 2, fit_text(text, 13, w - 8), 13, config.WIKI_SUBTLE)
        for i in range(0, int(w) + 8, 8):           # 점선 테두리 (위·아래)
            a = (0.4 + 0.5 * pulse) * min(1.0, reveal)
            fill_rect(x - 4 + i, sy - 4, 4, 1.5, config.COLOR_ORANGE, a)
            fill_rect(x - 4 + i, sy + h + 3, 4, 1.5, config.COLOR_ORANGE, a)
        if skey == key and k > 0:                   # 갉는 중: 찢긴 구멍 (0·1이 보이고 불씨가 깜빡임)
            j = config.CHEW_JOLT_AMP * chew_jolt[0] / config.CHEW_JOLT     # 막 뜯겼으면 덜덜
            jx, jy = random.uniform(-j, j), random.uniform(-j, j)
            draw_hole(x + w / 2 + jx, sy + h / 2 + jy, config.CHEW_HOLE_R * k, play_time, hash(str(skey)) % 1000)


def start_opening(action, rect, color):
    # 새 창 열기 시작: rect(월드)에서 창이 화면 가득 커진다. 다 열리면 action을 한다
    global opening
    if action[0] == 'doc':
        name, url = action[1], site['url'] + action[1]
    elif action[0] == 'complete':
        name, url = 'CRAWL COMPLETE', '/complete'
    elif action[0] == 'lost':
        name, url = 'CRAWL FAILED', '/lost'
    elif action[0] == 'quit':
        game_framework.quit()                         # 종료 칸: 창 없이 바로 끝
        return
    elif action[0] == 'home':
        name, url = 'HOME', '/home'
    elif action[0] in ('next', 'start'):              # 다음 사이트 / 처음부터 (첫 사이트)
        order = config.STAGE_ORDER
        sid = order[0] if action[0] == 'start' else order[order.index(site['id']) + 1]
        nxt = load_site(sid)
        name, url = nxt['start'], nxt['url'] + nxt['start']
    else:                                             # restart: 같은 사이트 처음 문서
        name, url = site['start'], site['url'] + site['start']
    duration = config.LOST_OPEN_TIME if action[0] == 'lost' else config.OPEN_TIME   # 죽음의 창은 천천히
    hole = action[0] == 'doc' and not isinstance(page, CrawlPage)           # 문서 사이는 갉은 구멍으로 빨려 들어감
    if hole:
        duration = config.HOLE_TIME
    opening = {'action': action, 'name': name, 'url': url, 'rect': rect, 'color': color, 't': 0.0, 'time': duration,
               'hole': hole}


def do_action(action):
    # 창이 다 열린 뒤 할 일
    if action[0] == 'doc':
        go_to(action[1], action[2])
        body.drop()                                   # 구멍으로 떨어져 들어옴
        arrive_hole[0] = config.ARRIVE_HOLE_TIME
    elif action[0] == 'complete':
        open_complete()
    elif action[0] == 'lost':
        open_lost()
    elif action[0] == 'restart':
        restart_site()                                # 이 사이트에 들어올 때의 몸·데이터로 처음부터 (목표는 새로 뽑음)
    elif action[0] == 'next':
        next_site()                                   # 몸·데이터를 가지고 다음 사이트로
    elif action[0] == 'home':
        open_home()
    elif action[0] == 'start':
        init(config.STAGE_ORDER[0])                   # 새 판: 새 몸으로 첫 사이트부터


def go_to(title, back):
    # 다음 문서로: 앞으로 가면 지금 문서를 기록에 쌓고, 뒤로 가면 기록에서 꺼낸다
    if back:
        history.pop()
    else:
        history.append(page.title)
    open_doc(title)


def update():
    global target_x, target_y, next_doc, play_time, fade, opening, messages, clear_timer, hit_stop, shake, data_flash
    shake = max(0.0, shake - game_framework.frame_time)
    data_flash = max(0.0, data_flash - game_framework.frame_time)
    arrive_hole[0] = max(0.0, arrive_hole[0] - game_framework.frame_time)
    chew_jolt[0] = max(0.0, chew_jolt[0] - game_framework.frame_time)
    if not isinstance(page, CrawlPage):
        if exit_need() > 0:
            chew_ready[0] = None                      # 모자람 (처음이거나 봇이 되돌림)
        elif chew_ready[0] is None:
            chew_ready[0] = play_time + config.CHEW_UNLOCK   # 다 먹은 순간부터 텀
    update_leak()
    if hit_stop > 0:
        hit_stop -= game_framework.frame_time           # 피격 멈칫: 이 동안 아무것도 움직이지 않음
        return
    if opening is not None:
        # 새 창이 열리는 동안은 게임이 멈춘다. 다 열리면 할 일(문서 옮기기 등)을 한다
        opening['t'] += game_framework.frame_time
        if opening['t'] >= opening['time']:
            action = opening['action']
            opening = None
            do_action(action)
        return
    if frozen[0]:
        check_lost()                                  # 응답 없음: 아무것도 움직이지 않고 창이 열릴 때만 기다림
        return
    # 커서의 월드 좌표는 매 프레임 다시 계산한다 — 마우스를 가만히 둬도 카메라가 움직이면 가리키는 곳이 바뀐다
    target_x, target_y = camera.to_world(mouse_x, mouse_y)
    body.update(target_x, target_y, game_framework.frame_time, left_down)
    camera.update(body.segs[0].y, game_framework.frame_time)
    page.update(game_framework.frame_time)
    for enemy in page.enemies:
        if enemy.active(camera):                      # 화면 ± ENEMY_ACTIVE_PAD 안의 적만 움직임
            enemy.update(game_framework.frame_time, footprints)
            if isinstance(enemy, CommentNest):
                enemy.swarm(game_framework.frame_time, body)   # 댓글 벌레: 쫓아가 달라붙기·떨쳐지기
            if isinstance(enemy, AdSpawner) and not cleared:
                enemy.drop(game_framework.frame_time, body, page)   # 광고: 가는 길 앞에 떨어뜨림
            if hasattr(enemy, 'watch'):
                enemy.watch(game_framework.frame_time, body)   # 쇼핑몰 적: 크롤러를 보고 움직임
    body.burden = sum(e.stuck_count() for e in page.enemies if isinstance(e, CommentNest))
    ingest.update(game_framework.frame_time, body)    # 날아가는 글자, 도착하면 꿀꺽·저장
    body.stored = len(ingest.stored)
    check_reverts()
    push_out_walls()
    check_hits()
    for part in page.parts:
        part.locked = not body.can_grow()             # 최대면 파츠를 흐리게 (주울 수 없음)
    debug_view.update(game_framework.frame_time)
    play_time += game_framework.frame_time
    for m in messages:
        m[3] += game_framework.frame_time
    messages = [m for m in messages if m[3] < config.SHORT_MSG_TIME]
    fade = max(0.0, fade - game_framework.frame_time)
    if next_doc is not None:                          # 이번 프레임에 칸을 다 채웠으면 새 창 열기 시작
        action, rect = next_doc
        next_doc = None
        start_opening(action, rect, config.COLOR_ORANGE)
    if cleared and clear_spot is not None and not isinstance(page, CrawlPage):
        clear_timer -= game_framework.frame_time      # 키워드를 먹고 잠시 뒤 그 자리에서 탈출 창
        if clear_timer <= 0:
            start_opening(('complete',), clear_spot, config.COLOR_GOLD)
            clear_timer = 0.0
    check_lost()


def check_lost():
    # 다리 0개 → GAME OVER (PRD 5.4): 데이터 유출 → 글리치 → 응답 없음(화면이 굳음) → 머리 자리에서 빨간 창 → crawl://lost
    global lost, lost_timer, lost_doc
    if isinstance(page, CrawlPage) or cleared or opening is not None:
        return
    global hit_stop, shake
    if not lost and not body.all_legs():
        lost, lost_timer, lost_doc = True, config.LOST_DELAY, page.title
        body.stun = config.LOST_DELAY + config.LOST_OPEN_TIME   # 움직이지 못하고 눈을 감음
        body.start_dying(data_count)                        # 데이터 유출 → 글리치 → 응답 없음
        hit_stop, shake = config.DEATH_STOP, config.SHAKE_TIME   # 쿵: 길게 멈칫 + 크게 흔들림
        return
    if lost:
        lost_timer -= game_framework.frame_time
        if dead_time() >= config.DIE_FREEZE:
            frozen[0] = True                                # 응답 없음: 이제부터 화면이 멈춤
        if lost_timer <= 0:
            # 확대된 화면 속 머리 자리에서 빨간 창 (창은 확대하지 않고 화면 위에 그린다)
            s = config.BOX_HEAD_SIZE * config.DEATH_ZOOM
            x, y = death_spot
            start_opening(('lost',), (x - s / 2, y - s / 2 + camera.y, s, s), config.COLOR_RED)


def dead_time():
    # 다리를 모두 잃은 뒤 지난 시간 (살아 있으면 −1)
    if not lost or isinstance(page, CrawlPage):
        return -1.0
    return config.LOST_DELAY - lost_timer


def shown_data():
    # 띠에 보이는 DATA: 죽는 중엔 쏟아지는 만큼 0으로 줄어듦 (결과 페이지엔 원래 수)
    t = dead_time()
    if t < 0:
        return data_count
    return round(data_count * max(0.0, 1 - t / config.DIE_SPILL_TIME))


def death_zoom():
    # 죽는 중 확대 배율 1 → DEATH_ZOOM (처음 빠르고 끝에 느리게), 붉어지는 정도 0 → 1
    if not lost or isinstance(page, CrawlPage):
        return 1.0, 0.0
    u = 1.0 if opening is not None else min(1.0, dead_time() / config.DIE_SPILL_TIME)   # 데이터 유출 동안 다가감
    k = 1 - (1 - u) ** 3
    return 1 + (config.DEATH_ZOOM - 1) * k, k


def tear_amount():
    # 죽음 창의 티어링 정도 0 → 1 (대화상자 뒤 LOST_OPEN_TIME까지, 갈수록 세게)
    if opening is None or opening['action'][0] != 'lost' or opening['t'] < config.LOST_DIALOG_TIME:
        return 0.0
    u = (opening['t'] - config.LOST_DIALOG_TIME) / (opening['time'] - config.LOST_DIALOG_TIME)
    return min(1.0, u) ** 2


def open_progress():
    # 창 열기 진행 0~1, 끝으로 갈수록 느려지게 (ease-out: 1 - (1-u)³)
    u = min(1.0, opening['t'] / opening['time'])
    return 1 - (1 - u) ** 3


def draw_error_dialog(x, y, k):
    # 오류 대화상자 (왼쪽 아래 (x, y)): 제목 줄 + 빨간 ✕ 아이콘 + 문구 + 보고서 작성 막대(k = 0~1)
    w, h, t = config.ERR_W, config.ERR_H, config.ERR_TITLE_H
    fill_rect(x + 6, y - 6, w, h, (0, 0, 0), 0.5)                         # 그림자
    fill_rect(x, y, w, h, config.HUD_BAR_BG)
    fill_rect(x, y + h - t, w, t, config.HUD_FIELD_BG)
    draw_rect(x, y, w, h, 1, config.WIKI_BORDER_STRONG)
    draw_static_text(x + 10, y + h - t + 5, 'CRAWL.EXE', 13, config.WIKI_TEXT, 1.0, 'bold')
    qx, qy = x + w - 16, y + h - t / 2                                   # 닫기 단추 ✕ (선 두 개)
    draw_line(qx - 4, qy - 4, qx + 4, qy + 4, 1.5, config.HUD_LABEL)
    draw_line(qx - 4, qy + 4, qx + 4, qy - 4, 1.5, config.HUD_LABEL)
    cx, cy = x + 34, y + h - t - 34                                       # ✕ 아이콘
    draw_circle(cx, cy, 13, 3, config.COLOR_RED)
    draw_line(cx - 6, cy - 6, cx + 6, cy + 6, 3, config.COLOR_RED)
    draw_line(cx - 6, cy + 6, cx + 6, cy - 6, 3, config.COLOR_RED)
    draw_static_text(x + 60, cy + 2, 'CRAWL.EXE에 문제가 있어', 14, config.WIKI_TEXT)
    draw_static_text(x + 60, cy - 18, '종료해야 합니다.', 14, config.WIKI_TEXT)
    draw_static_text(x + 18, y + 38, '오류 보고서를 작성하는 중...', 12, config.HUD_LABEL)
    fill_rect(x + 18, y + 16, w - 36, 12, config.HUD_FIELD_BG)
    fill_rect(x + 18, y + 16, (w - 36) * k, 12, config.COLOR_RED)
    draw_rect(x + 18, y + 16, w - 36, 12, 1, config.WIKI_BORDER)


def draw_opening():
    # 구멍(문서 사이): 갉은 구멍이 검게 화면 전체로 번지며 빨려 들어간다
    if opening.get('hole'):
        x, y, w, h = opening['rect']
        cx, cy = x + w / 2, y + h / 2 - camera.y
        k = open_progress()
        r = config.CHEW_HOLE_R + (config.SCREEN_W * 1.2) * k * k
        draw_hole(cx, cy, r, play_time + opening['t'], 3)
        return
    # 밟은 칸 자리에서 새 창 테두리가 페이지 창 전체로 커지며 이전 문서를 덮는다
    # 죽음(lost)은 먼저 오류 대화상자가 떠서 보고서 막대가 찬 뒤, 그 대화상자가 화면 가득 커진다
    if opening['action'][0] == 'lost':
        dw, dh = config.ERR_W, config.ERR_H
        bx = max(10, min(config.SCREEN_W - dw - 20, death_spot[0] - dw / 2))     # 머리 자리, 화면 안으로
        by = max(10, min(config.SCREEN_H - config.HUD_BAR_H - dh - 10, death_spot[1] - dh / 2))
        t = opening['t']
        if t < config.LOST_DIALOG_TIME:
            pop = min(1.0, t / 0.08)                                       # 툭 튀어나옴: 0.08초에 커짐
            if pop < 1:
                s = 0.6 + 0.4 * pop
                fill_rect(bx + dw * (1 - s) / 2, by + dh * (1 - s) / 2, dw * s, dh * s, config.HUD_BAR_BG)
                return
            draw_error_dialog(bx, by, min(1.0, t / (config.LOST_DIALOG_TIME * 0.85)))
            return
        # 티어링: 대화상자도 좌우로 찢겨 흔들리고, 가로로 잘린 틈이 생긴다 (화면 띠는 end_zoom이 찢음)
        k = tear_amount()
        jx = random.uniform(-1, 1) * k * config.TEAR_PX * 0.6
        draw_error_dialog(bx + jx, by, 1.0)
        for _ in range(int(3 + 6 * k)):
            cy = random.uniform(by, by + dh)
            fill_rect(bx + jx - 20, cy, dw + 40, random.uniform(2, 8), config.COLOR_BG)
        return
    k = open_progress()
    sx, sy, sw, sh = opening['rect']
    sy -= camera.y                                    # 칸의 화면 위치에서 시작
    view_w, view_h = config.SCREEN_W - config.SCROLL_W, config.SCREEN_H - config.HUD_BAR_H
    x, y = sx + (0 - sx) * k, sy + (0 - sy) * k       # 칸 → 창 전체로 보간
    w, h = sw + (view_w - sw) * k, sh + (view_h - sh) * k
    fill_rect(x, y, w, h, config.COLOR_BG)
    draw_rect(x, y, w, h, 2, opening['color'], 1 - k * 0.6)
    if h > config.OPEN_TITLE_H * 2:                   # 충분히 커지면 창 위쪽에 제목 줄
        fill_rect(x, y + h - config.OPEN_TITLE_H, w, config.OPEN_TITLE_H, config.HUD_BAR_BG)
        draw_static_text(x + 12, y + h - config.OPEN_TITLE_H + 7, opening['name'], config.HUD_FONT, config.WIKI_TEXT)
        # 로딩 중인 페이지처럼 회색 글줄 자리 (창 안에 들어가는 줄만)
        top = y + h - config.OPEN_TITLE_H - 40
        for i, frac in enumerate(config.OPEN_SKELETON):
            ly = top - i * 34
            if ly < y + 10:
                break
            fill_rect(x + 24, ly, (w - 48) * frac, 12 if i else 20, config.WIKI_BOX_BG)


def draw_cursor():
    s = config.CURSOR_SIZE
    draw_line(mouse_x - s, mouse_y, mouse_x + s, mouse_y, 1, config.COLOR_YELLOW)
    draw_line(mouse_x, mouse_y - s, mouse_x, mouse_y + s, 1, config.COLOR_YELLOW)


def draw():
    # 화면 지우기·표시는 game_framework가 한다. 여기서는 그리기만.
    global death_spot
    zoom, tint = death_zoom()
    if zoom > 1:
        begin_zoom()                                  # 죽는 중: 페이지·크롤러를 텍스처에 그렸다가 확대해서 보여 줌
    fill_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_BG)   # 남색 배경
    # 화면 흔들림: 그리는 동안만 카메라를 위아래로 흔들고 HUD 전에 되돌린다 (갈수록 잦아듦)
    camera_y = camera.y
    if shake > 0:
        camera.y += math.sin(shake * config.SHAKE_FREQ) * config.SHAKE_AMP * shake / config.SHAKE_TIME
    if isinstance(page, CrawlPage):
        page.draw(camera, exit_fill())                # crawl:// 페이지: 글줄 + 메뉴 칸
    else:
        page.draw(camera)
        draw_chew_spots()                             # 먹은 링크 껍데기 = 다음 문서로 가는 구멍 자리
        if arrive_hole[0] > 0:                        # 새 문서 맨 위의 도착 구멍이 메워지는 중
            sx, sy = camera.to_screen(*page.spawn())
            draw_hole(sx, sy, config.CHEW_HOLE_R * 1.6 * arrive_hole[0] / config.ARRIVE_HOLE_TIME, play_time, 7)
    leak.draw(camera)                                 # 구멍에서 새어 나오는 0·1
    draw_hazards()
    for enemy in page.enemies:
        enemy.draw(camera)
    if cleared and clear_spot is not None and clear_timer > 0:
        # 키워드를 먹은 순간: 키워드 자리에서 금색 원 두 겹이 퍼진다
        x, y, w, h = clear_spot
        k = 1 - clear_timer / config.CLEAR_DELAY
        for r in (k, k * 0.6):
            draw_circle(x + w / 2, y + h / 2 - camera.y, 6 + config.CLEAR_FX_R * r, 3, config.COLOR_GOLD, 1 - k)
    body.draw(camera)
    for enemy in page.enemies:
        if isinstance(enemy, CommentNest):
            enemy.draw_stuck(camera)                  # 몸에 붙은 댓글 벌레는 크롤러 위에
    ingest.draw(camera)                               # 날아가는 링크 글자 (몸 위에)
    for x, y, text, age in messages:                  # 떠오르며 흐려지는 알림
        k = age / config.SHORT_MSG_TIME
        w = text_width(text, config.HUD_FONT, 'bold')
        mx, my = x - w / 2, y + config.SHORT_MSG_RISE * k - camera.y
        color = config.COLOR_ORANGE if text.startswith('먹은 링크') else config.COLOR_RED   # 안내는 주황, 경고는 빨강
        draw_static_text(mx, my, text, config.HUD_FONT, color, 1 - k * k, 'bold')
        if text.startswith('되돌림'):                  # 되돌림 알림 앞에 ↺ 아이콘
            draw_revert_arrow(mx - 12, my + 9, 6, -age * 8, config.COLOR_RED)
    if zoom > 1:
        fill_rect(0, 0, config.SCREEN_W, config.SCREEN_H, (60, 0, 0), config.DEATH_TINT * tint)   # 붉게 어두워짐
        if frozen[0]:
            fill_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_WHITE, config.DIE_FREEZE_WHITE)   # 응답 없음: 하얗게 굳음
        head = body.segs[0]
        hx, hy = camera.to_screen(head.x, head.y)
        death_spot = end_zoom(hx, hy + body.seg_h(0) * config.VIEW_TILT, zoom, tear_amount())   # 머리 중심 확대 (+티어링)
    if opening is not None:
        draw_opening()
    if fade > 0:                          # 문서를 막 옮겼으면 배경색에서 밝아진다
        fill_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_BG, fade / config.PAGE_FADE_TIME)
    camera.y = camera_y                               # 흔들림 되돌림 (HUD·스크롤바는 흔들지 않음)
    for enemy in page.enemies:
        if isinstance(enemy, RefreshBand):
            enemy.draw_warning()                      # 새로 고침 띠 경고는 덮개 위에 (놓치지 않게)
    markers = [(y + h / 2, config.COLOR_ORANGE) for key, (x, y, w, h), a, t in chew_spots()]   # 갉을 수 있는 곳 (주황 점)
    draw_scrollbar(camera, page.height, markers)    # HUD — 화면 좌표
    goal_text = goal['keyword'] + ('  (찾음)' if cleared else '')
    url = page.url if isinstance(page, CrawlPage) else site['url'] + page.title
    loading, loading_color = None, config.COLOR_ORANGE
    lost_dialog = opening is not None and opening['action'][0] == 'lost' and opening['t'] < config.LOST_DIALOG_TIME
    if opening is not None and not lost_dialog:
        # 여는 중: 주소칸에 새 주소가 한 글자씩 입력되고, 띠 아래 로딩 막대가 찬다
        t, total = opening['t'], opening['time']
        if opening['action'][0] == 'lost':          # 죽음 창은 대화상자가 커지기 시작할 때부터 입력
            t, total = t - config.LOST_DIALOG_TIME, total - config.LOST_DIALOG_TIME
        url = opening['url'][:int(len(opening['url']) * min(1.0, t / (total * config.OPEN_TYPE_PART)))]
        loading, loading_color = min(1.0, t / total), opening['color']
    eaten = None if isinstance(page, CrawlPage) else page.eaten_count()   # crawl:// 페이지에는 '이 문서' 수가 없음
    if frozen[0] and (opening is None or lost_dialog):
        url += '   (응답 없음)'                         # 윈도우가 멈췄을 때처럼 (오류 대화상자가 떠 있는 동안에도)
    flash = data_flash > 0 and int(data_flash / 0.1) % 2 == 0      # 데이터를 잃으면 DATA가 빨갛게 깜빡
    draw_bar(url, goal_text, len(visited), site['min_pages'], eaten, site['page_quota'], shown_data(), loading, loading_color,
             config.COLOR_RED if flash else config.COLOR_SKY)

    debug_view.draw(camera, body, (mouse_x, mouse_y), (target_x, target_y), page,
                    'goal %s/%s (%d hops)  data %d  queue %s  back %s' % (goal['page'], goal['keyword'], goal['hops'], data_count,
                                                                           ', '.join(frontier) or '-', ', '.join(history) or '-'))   # F1
    draw_cursor()


def pause():
    pass


def resume():
    pass
