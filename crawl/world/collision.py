# 충돌 판정 — 월드 좌표, 높이(z)는 보지 않고 바닥에 비친 위치로 판정한다 (PRD 5.4)
import math


def circle_circle(x1, y1, r1, x2, y2, r2):
    # 두 원이 겹치는지: 중심 거리 ≤ 반지름 합
    return math.hypot(x2 - x1, y2 - y1) <= r1 + r2


def circle_segment(cx, cy, r, x1, y1, x2, y2):
    # 원(cx, cy, r)과 선분 (x1, y1)–(x2, y2)가 겹치는지:
    # 원 중심에서 선분 위 가장 가까운 점까지 거리 ≤ r
    dx, dy = x2 - x1, y2 - y1
    length2 = dx * dx + dy * dy
    if length2 == 0:
        t = 0.0
    else:
        t = ((cx - x1) * dx + (cy - y1) * dy) / length2   # 중심을 선분 방향으로 투영한 위치 (0 = 시작점, 1 = 끝점)
        t = max(0.0, min(1.0, t))                          # 선분 밖이면 가까운 끝점으로
    px, py = x1 + dx * t, y1 + dy * t                      # 선분 위 가장 가까운 점
    return math.hypot(cx - px, cy - py) <= r


def leg_hit(leg, cx, cy, r):
    # 다리의 두 선분(어깨–무릎, 무릎–발) 중 하나라도 원과 겹치면 True
    return (circle_segment(cx, cy, r, leg.shoulder_x, leg.shoulder_y, leg.knee_x, leg.knee_y) or
            circle_segment(cx, cy, r, leg.knee_x, leg.knee_y, leg.foot_x, leg.foot_y))


def circle_rect(cx, cy, r, x, y, w, h):
    # 원과 사각형(왼쪽 아래 x, y, 폭 w, 높이 h)이 겹치는지: 사각형 안에서 원 중심에 가장 가까운 점까지 거리 ≤ r
    px = max(x, min(x + w, cx))
    py = max(y, min(y + h, cy))
    return math.hypot(cx - px, cy - py) <= r


def segment_rect(x1, y1, x2, y2, x, y, w, h):
    # 선분이 사각형과 겹치는지 (Liang–Barsky): 선분을 P(t) = 시작 + t·(끝 − 시작), t ∈ [0, 1]로 두고
    # 사각형의 네 경계마다 "안쪽에 있는 t 구간"을 좁혀 간다. 끝까지 구간이 남으면 겹침
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - x), (dx, x + w - x1), (-dy, y1 - y), (dy, y + h - y1)):
        if p == 0:
            if q < 0:
                return False                     # 경계와 나란하고 바깥에 있음
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)                      # 들어가는 경계
        else:
            t1 = min(t1, t)                      # 나가는 경계
        if t0 > t1:
            return False
    return True


def leg_hit_rect(leg, x, y, w, h):
    # 다리의 두 선분 중 하나라도 사각형과 겹치면 True
    return (segment_rect(leg.shoulder_x, leg.shoulder_y, leg.knee_x, leg.knee_y, x, y, w, h) or
            segment_rect(leg.knee_x, leg.knee_y, leg.foot_x, leg.foot_y, x, y, w, h))
