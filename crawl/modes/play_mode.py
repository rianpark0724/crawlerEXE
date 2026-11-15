# 플레이 화면 — 사이트(스테이지)를 읽어 시작 문서를 페이지로 만들고, 크롤러가 커서를 따라 걷는다. F1 디버그 뷰.
# 문서 이동: 페이지 끝 '다음 문서' 상자의 칸을 발로 밟는다 (PRD 11.3-3). 모든 상호작용은 크롤러로.
# 클리어: 키워드 자리에서 창이 열려 crawl://complete 결과 페이지로 — 크롤러는 화면에서 사라지지 않는다 (PRD 12).
import math
import random

from pico2d import get_events
from sdl2 import (SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE, SDLK_F1, SDLK_F2, SDL_MOUSEMOTION,
                  SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT)

import config
import game_framework
from crawler.body import Body
from world.camera import Camera
from world.stage import Page, load_site, pick_goal, mark_goal
from world.crawl_page import CrawlPage
from world.objects import place_parts
from ui.hud import draw_scrollbar, draw_bar
from ui.draw import draw_line, draw_rect, draw_circle, fill_rect, draw_static_text, text_width
from ui import debug_view

mouse_x, mouse_y = 0.0, 0.0   # 커서 위치 (화면 좌표, y 위로 증가) — 커서 그리기용
target_x, target_y = 0.0, 0.0 # 커서 위치 (월드 좌표) — 크롤러 목표
body = None                   # 크롤러 몸
left_down = False             # 좌클릭을 누르고 있는지 (질주)
camera = None
page = None
site = None                   # 지금 사이트 (설정 + 문서들, dict)
data_count = 0                # 먹은 데이터(링크) 수 — 문서를 넘어가도 유지
frontier = []                 # 방문 대기열: 먹었지만 아직 안 간 문서 제목들 (PRD 11.3)
visited = []                  # 방문한 문서 제목들 (순서대로)
goal = None                   # 이번 판 목표 {'page': 문서, 'keyword': 키워드, 'hops': 시작에서 몇 단계}
cleared = False               # 목표 키워드를 먹고 탈출했는지
clear_timer = 0.0             # 키워드를 먹은 뒤 탈출 창이 열리기까지 남은 시간
clear_spot = None             # 먹은 키워드 상자 (x, y, w, h) — 탈출 창이 여기서 열린다
messages = []                 # 떠오르는 글 [x, y, 글, 나이] (월드 좌표) — '크롤링이 부족합니다'
pages = {}                    # 한 번 연 문서의 Page (제목 → Page) — 다시 와도 먹은 링크가 보라로 남게
history = []                  # 지나온 문서 제목들 — '뒤로' 칸이 마지막 것으로 간다
next_doc = None               # 이번 프레임에 다 채운 칸 (할 일, 칸 위치) — 걷기 처리가 끝난 뒤 창 열기 시작
opening = None                # 새 창이 열리는 중: {'action', 'name'(창 제목), 'url', 'rect'(시작 칸, 월드), 'color', 't'}
play_time = 0.0               # 플레이 시간 (출구 깜빡임 등)
fade = 0.0                    # 문서를 옮긴 뒤 남은 밝아짐 시간
charge = {'key': None, 'n': 0, 'time': 0.0}     # 칸 채우기: 어느 칸을, 몇 번 연속 밟았는지, 마지막 착지 시각


def init(site_id=config.FIRST_STAGE):
    global mouse_x, mouse_y, left_down, body, site, data_count, frontier, visited, goal, pages, history, next_doc, play_time, opening, cleared, messages, clear_timer, clear_spot
    left_down = False
    body = None                                     # 새 판: 시작 마디 수로
    site = load_site(site_id)
    data_count, frontier, visited = 0, [], []
    pages, history, next_doc, play_time, opening = {}, [], None, 0.0, None
    random.seed(config.RANDOM_SEED)                 # None이면 매번 다른 판
    goal = pick_goal(site)                          # 시작에서 min_hops단계 이상 떨어진 후보 중 하나
    cleared, messages, clear_timer, clear_spot = False, [], 0.0, None
    mouse_x, mouse_y = config.SCREEN_W / 2, config.SCREEN_H / 2   # 첫 마우스 이벤트 전에는 화면 가운데
    open_doc(site['start'])                         # 시작 문서 맨 위에서 출발


def show_page(new_page):
    # 페이지를 화면에 띄우고 그 페이지 맨 위에 크롤러를 세운다 (문서·crawl:// 페이지 공통)
    global page, camera, body, target_x, target_y, fade, charge
    charge = {'key': None, 'n': 0, 'time': 0.0}
    page = new_page
    camera = Camera(page.height)                    # 페이지 맨 위에서 시작
    target_x, target_y = camera.to_world(mouse_x, mouse_y)
    count = len(body.segs) if body is not None else config.BOX_START_SEGS
    body = Body(*page.spawn(), count)               # 맨 위에서 다시 나타남 — 자란 마디 수는 유지 (잃은 다리 유지는 S08)
    body.on_land = on_land                          # 착지 이벤트 연결
    fade = config.PAGE_FADE_TIME


def open_doc(title):
    # 사이트 문서를 연다. 처음 여는 문서면 Page를 만들어 보관
    if title not in pages:
        doc = site['docs'][title]
        if title == goal['page']:
            doc = mark_goal(doc, goal['keyword'])   # 목표 문서: 키워드 자리 중 하나를 뽑아 금색 키워드로
        pages[title] = Page(doc, set(site['docs']))  # 링크 색은 사이트의 문서 제목으로 정함
        counts = site['pages'].get(title, {}).get('parts', {})   # 이 문서의 파츠 종류별 개수 (사이트 JSON)
        pages[title].parts = place_parts(pages[title], counts)  # 위치는 무작위 (처음 열 때 한 번)
    if title not in visited:
        visited.append(title)                       # 방문 수 (HUD 방문 k/K)
    if title in frontier:
        frontier.remove(title)                      # 갔으니 방문 대기열에서 뺀다
    show_page(pages[title])


def open_complete():
    # 결과 페이지 crawl://complete — 크롤러가 걸어 다니며 '다시 크롤링' 칸을 밟는다
    lines = [('CRAWL COMPLETE', 34, config.COLOR_GOLD, True),
             ('"%s" — %s%s 에서 찾음' % (goal['keyword'], site['url'], goal['page']), 16, config.WIKI_TEXT, False),
             ('시간 %d:%02d  ·  데이터 %d  ·  방문 %d' % (play_time // 60, play_time % 60, data_count, len(visited)), 16, config.WIKI_TEXT, False),
             ('경로  ' + ' → '.join(visited), 13, config.HUD_LABEL, False)]
    slots = [{'label': '다시 크롤링', 'key': 'restart', 'action': ('restart',), 'enabled': True},
             {'label': '다음 사이트 (준비 중)', 'key': 'next', 'action': None, 'enabled': False}]   # 다음 사이트는 S10-3
    show_page(CrawlPage('complete', lines, slots))


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
    # 지금 페이지에서 밟을 수 있는 칸들 → ([(구분 이름, 할 일, 열렸는지)], [칸 위치])
    if isinstance(page, CrawlPage):
        return [(s['key'], s['action'], s['enabled']) for s in page.slots], page.slot_rects()
    if exit_need() > 0:
        return [], []                               # 출구가 아직 잠김
    choices = exit_choices()
    return [(t, ('doc', t, back), True) for label, t, back in choices], page.slot_rects(len(choices))


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
            body.start_wave(target_x, target_y)       # □ WAVE 점프 돌진 (재사용 대기 중이면 무시)


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
    global data_count, next_doc, cleared, clear_timer, clear_spot
    debug_view.note_landing(leg.foot_x, leg.foot_y)
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
    group = page.eat_at(leg.foot_x, leg.foot_y)
    if group is not None:
        data_count += 1
        if group['target'] not in visited and group['target'] not in frontier:
            frontier.append(group['target'])          # 먹은 링크의 문서 → 방문 대기열
        return
    # 칸(출구 상자의 문서 칸, crawl:// 페이지의 메뉴 칸)에 착지했는지
    if next_doc is not None or opening is not None or (cleared and not isinstance(page, CrawlPage)):
        return                                        # 탈출 창이 열리기 직전에는 다른 칸을 밟지 않게
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


def start_opening(action, rect, color):
    # 새 창 열기 시작: rect(월드)에서 창이 화면 가득 커진다. 다 열리면 action을 한다
    global opening
    if action[0] == 'doc':
        name, url = action[1], site['url'] + action[1]
    elif action[0] == 'complete':
        name, url = 'CRAWL COMPLETE', '/complete'
    else:                                             # restart: 같은 사이트 처음 문서
        name, url = site['start'], site['url'] + site['start']
    opening = {'action': action, 'name': name, 'url': url, 'rect': rect, 'color': color, 't': 0.0}


def do_action(action):
    # 창이 다 열린 뒤 할 일
    if action[0] == 'doc':
        go_to(action[1], action[2])
    elif action[0] == 'complete':
        open_complete()
    elif action[0] == 'restart':
        init(site['id'])                              # 같은 사이트를 처음부터 (목표는 새로 뽑음)


def go_to(title, back):
    # 다음 문서로: 앞으로 가면 지금 문서를 기록에 쌓고, 뒤로 가면 기록에서 꺼낸다
    if back:
        history.pop()
    else:
        history.append(page.title)
    open_doc(title)


def update():
    global target_x, target_y, next_doc, play_time, fade, opening, messages, clear_timer
    if opening is not None:
        # 새 창이 열리는 동안은 게임이 멈춘다. 다 열리면 할 일(문서 옮기기 등)을 한다
        opening['t'] += game_framework.frame_time
        if opening['t'] >= config.OPEN_TIME:
            action = opening['action']
            opening = None
            do_action(action)
        return
    # 커서의 월드 좌표는 매 프레임 다시 계산한다 — 마우스를 가만히 둬도 카메라가 움직이면 가리키는 곳이 바뀐다
    target_x, target_y = camera.to_world(mouse_x, mouse_y)
    body.update(target_x, target_y, game_framework.frame_time, left_down)
    camera.update(body.segs[0].y, game_framework.frame_time)
    page.update(game_framework.frame_time)
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


def open_progress():
    # 창 열기 진행 0~1, 끝으로 갈수록 느려지게 (ease-out: 1 - (1-u)³)
    u = min(1.0, opening['t'] / config.OPEN_TIME)
    return 1 - (1 - u) ** 3


def draw_opening():
    # 밟은 칸 자리에서 새 창 테두리가 페이지 창 전체로 커지며 이전 문서를 덮는다
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
    fill_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_BG)   # 남색 배경
    if isinstance(page, CrawlPage):
        page.draw(camera, exit_fill())                # crawl:// 페이지: 글줄 + 메뉴 칸
    else:
        page.draw(camera)
        page.draw_exit(camera, exit_choices(), exit_need(), play_time, exit_fill())
    draw_hazards()
    if cleared and clear_spot is not None and clear_timer > 0:
        # 키워드를 먹은 순간: 키워드 자리에서 금색 원 두 겹이 퍼진다
        x, y, w, h = clear_spot
        k = 1 - clear_timer / config.CLEAR_DELAY
        for r in (k, k * 0.6):
            draw_circle(x + w / 2, y + h / 2 - camera.y, 6 + config.CLEAR_FX_R * r, 3, config.COLOR_GOLD, 1 - k)
    body.draw(camera)
    for x, y, text, age in messages:                  # 떠오르며 흐려지는 알림
        k = age / config.SHORT_MSG_TIME
        w = text_width(text, config.HUD_FONT, 'bold')
        draw_static_text(x - w / 2, y + config.SHORT_MSG_RISE * k - camera.y, text, config.HUD_FONT, config.COLOR_RED, 1 - k * k, 'bold')
    if opening is not None:
        draw_opening()
    if fade > 0:                          # 문서를 막 옮겼으면 배경색에서 밝아진다
        fill_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_BG, fade / config.PAGE_FADE_TIME)
    markers = []
    if not isinstance(page, CrawlPage):
        exit_y = page.exit_rect[1] + page.exit_rect[3] / 2
        markers = [(exit_y, config.COLOR_ORANGE if exit_need() == 0 else config.COLOR_GRAY)]
    draw_scrollbar(camera, page.height, markers)    # HUD — 화면 좌표
    goal_text = goal['keyword'] + ('  (찾음)' if cleared else '')
    url = page.url if isinstance(page, CrawlPage) else site['url'] + page.title
    loading = None
    if opening is not None:
        # 여는 중: 주소칸에 새 주소가 한 글자씩 입력되고, 띠 아래 로딩 막대가 찬다
        url = opening['url'][:int(len(opening['url']) * min(1.0, opening['t'] / (config.OPEN_TIME * config.OPEN_TYPE_PART)))]
        loading = open_progress()
    eaten = None if isinstance(page, CrawlPage) else page.eaten_count()   # crawl:// 페이지에는 '이 문서' 수가 없음
    draw_bar(url, goal_text, len(visited), site['min_pages'], eaten, site['page_quota'], data_count, loading)

    debug_view.draw(camera, body, (mouse_x, mouse_y), (target_x, target_y), page,
                    'goal %s/%s (%d hops)  data %d  queue %s  back %s' % (goal['page'], goal['keyword'], goal['hops'], data_count,
                                                                           ', '.join(frontier) or '-', ', '.join(history) or '-'))   # F1
    draw_cursor()


def pause():
    pass


def resume():
    pass
