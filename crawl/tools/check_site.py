# 사이트 설계 검사 (PRD 11.3-6, 11.3-7): 문서별 파란 링크 수, 시작 문서에서의 거리, 목표 후보가 쓸 수 있는지
# 실행: crawl 폴더에서  python tools/check_site.py wiki
import json
import os
import re
import sys
from collections import deque

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
LINK = re.compile(r'\[\[(!?)([^\]|]+?)(?:\|(.+?))?\]\]')
SLOT = re.compile(r'\{\{(.+?)\|(.+?)\}\}')


def all_text(doc):
    # 문서에서 링크가 들어갈 수 있는 모든 글 (안내문 + 본문 블록 + 사진 캡션 + 뉴스 관련 기사 카드)
    texts = [doc.get('hatnote', '')]
    for block in doc['blocks']:
        if isinstance(block[1], str):
            texts.append(block[1])
        elif isinstance(block[1], dict):
            texts.append(block[1].get('caption', ''))
        else:
            texts.extend(block[1])
    texts += ['[[%s]]' % card['title'] for card in doc.get('related', [])]
    return ' '.join(texts)


def main(site_id):
    with open(os.path.join(BASE, 'data', 'stages', site_id + '.json'), encoding='utf-8') as f:
        site = json.load(f)
    folder = os.path.join(BASE, 'data', 'pages', site['pages_dir'])
    docs = {}
    for name in sorted(os.listdir(folder)):
        if name.endswith('.json'):
            with open(os.path.join(folder, name), encoding='utf-8') as f:
                doc = json.load(f)
            docs[doc['title']] = doc
    titles = set(docs)

    # 문서 → 파란 링크가 가리키는 문서들 (자기 자신 제외, 중복 제외)
    graph = {}
    for title, doc in docs.items():
        blue = []
        for m in LINK.finditer(all_text(doc)):
            target = m.group(2)
            if not m.group(1) and target in titles and target != title and target not in blue:
                blue.append(target)
        graph[title] = blue

    # 시작 문서에서 링크 몇 번 만에 가는지 (너비 우선 탐색)
    hops = {site['start']: 0}
    queue = deque([site['start']])
    while queue:
        cur = queue.popleft()
        for nxt in graph[cur]:
            if nxt not in hops:
                hops[nxt] = hops[cur] + 1
                queue.append(nxt)

    problems = 0
    print('문서 %d장, 시작: %s' % (len(docs), site['start']))
    for title in sorted(docs, key=lambda t: hops.get(t, 99)):
        n = len(graph[title])
        warn = '' if 4 <= n <= 8 else '  ← 파란 링크 4–8개 권장'
        if title not in hops:
            warn += '  ← 시작에서 갈 수 없음'
            problems += 1
        if n < site.get('page_quota', 3):
            warn += '  ← page_quota보다 적어 출구가 안 열림'
            problems += 1
        print('  %s단계  %-10s 파란 링크 %d: %s%s' % (hops.get(title, '-'), title, n, ', '.join(graph[title]), warn))

    print('목표 후보 (min_hops %d):' % site.get('min_hops', 2))
    usable = 0
    for t in site['targets']:
        page, key = t['page'], t['keyword']
        slots = [m.group(1) for m in SLOT.finditer(all_text(docs[page]))] if page in docs else []
        ok_slot = key in slots
        h = hops.get(page)
        ok = h is not None and h >= site.get('min_hops', 2) and ok_slot
        usable += ok
        print('  %-3s %s / %s  (%s단계, 키워드 자리 %d개)%s' % ('O' if ok else 'X', page, key, h, slots.count(key),
                                                          '' if ok_slot else '  ← 문서에 {{%s|…}} 자리 없음' % key))
    print('뽑을 수 있는 목표 %d개' % usable)

    # 새로 고침 띠 간격: 띠는 WAVE로만 넘을 수 있으니, 한 문서의 띠가 너무 촘촘하면 못 넘는다
    sys.path.insert(0, BASE)
    import config
    for title, cfg in site.get('pages', {}).items():
        times = []                                   # 한 주기(공배수 대신 20초) 동안 띠가 시작하는 시각들
        for b in cfg.get('beams', []):
            period, offset = b.get('period', config.BAND_PERIOD), b.get('offset', 0.0)
            t = -offset
            while t < 20:
                if t >= 0:
                    times.append(t)
                t += period
        times.sort()
        gaps = [b - a for a, b in zip(times, times[1:])]
        if gaps and min(gaps) < config.BAND_MIN_GAP:
            print('  ← %s: 띠 간격 %.1f초 (최소 %.1f초) — WAVE로 매번 넘을 수 없음' % (title, min(gaps), config.BAND_MIN_GAP))
            problems += 1
    if usable == 0:
        problems += 1
    return problems


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'wiki'))
