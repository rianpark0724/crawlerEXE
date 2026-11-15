# 위키 페이지용 그림을 코드로 그려 PNG로 저장한다 (표준 라이브러리만 사용).
#   assets/images/wiki_logo.png     36×36   머리글 로고 — 선으로 된 지구본 위의 작은 크롤러
#   assets/images/wiki_crawler.png  220×150 도입부 사진 — "페이지 위에서 처음 촬영된 개체"
# 실행: crawl 폴더에서  python tools/make_wiki_images.py
#
# 그림 좌표는 PNG 기준(원점 왼쪽 위, y 아래로 증가). 가장자리를 부드럽게 하려고
# SS배 크게 그린 뒤 줄여서 저장한다(슈퍼샘플링).
import math
import os
import random
import struct
import zlib

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'images')
LIGHT = (-0.7071, -0.7071)    # 빛이 오는 방향 (왼쪽 위; 이 그림 좌표는 y가 아래로 증가)


class Canvas:
    def __init__(self, w, h, ss, bg=None):
        self.w, self.h, self.ss = w, h, ss
        self.W, self.H = w * ss, h * ss
        r, g, b, a = bg if bg else (0, 0, 0, 0)
        self.px = [[r, g, b, a] for _ in range(self.W * self.H)]   # 실수 RGBA (0~255, 알파 0~1)

    def blend(self, i, color, alpha):
        # 알파 합성: 위에 color를 alpha만큼 덮는다
        p = self.px[i]
        out_a = alpha + p[3] * (1 - alpha)
        if out_a <= 0:
            return
        for k in range(3):
            p[k] = (color[k] * alpha + p[k] * p[3] * (1 - alpha)) / out_a
        p[3] = out_a

    def bbox(self, xs, ys, pad):
        s = self.ss
        x0 = max(0, int((min(xs) - pad) * s)); x1 = min(self.W, int((max(xs) + pad) * s) + 1)
        y0 = max(0, int((min(ys) - pad) * s)); y1 = min(self.H, int((max(ys) + pad) * s) + 1)
        return x0, x1, y0, y1

    def poly(self, pts, color, alpha=1.0):
        # 볼록 다각형 채우기: 모든 변의 같은 쪽에 있으면 안쪽
        x0, x1, y0, y1 = self.bbox([p[0] for p in pts], [p[1] for p in pts], 1)
        n = len(pts)
        for Y in range(y0, y1):
            y = (Y + 0.5) / self.ss
            for X in range(x0, x1):
                x = (X + 0.5) / self.ss
                pos = neg = False
                for k in range(n):
                    ax, ay = pts[k]; bx, by = pts[(k + 1) % n]
                    c = (bx - ax) * (y - ay) - (by - ay) * (x - ax)    # 외적 부호 = 변의 어느 쪽인지
                    pos |= c > 0; neg |= c < 0
                if not (pos and neg):
                    self.blend(Y * self.W + X, color, alpha)

    def line(self, x1, y1, x2, y2, width, color, alpha=1.0):
        # 굵은 선: 선분까지 거리가 두께의 절반 이하인 점
        x0, xe, y0, ye = self.bbox([x1, x2], [y1, y2], width)
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy or 1e-9
        for Y in range(y0, ye):
            y = (Y + 0.5) / self.ss
            for X in range(x0, xe):
                x = (X + 0.5) / self.ss
                t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / L2))   # 선분 위 가장 가까운 점 비율
                if math.hypot(x - x1 - t * dx, y - y1 - t * dy) <= width / 2:
                    self.blend(Y * self.W + X, color, alpha)

    def circle(self, cx, cy, r, color, alpha=1.0):
        x0, x1, y0, y1 = self.bbox([cx], [cy], r + 1)
        for Y in range(y0, y1):
            for X in range(x0, x1):
                if math.hypot((X + 0.5) / self.ss - cx, (Y + 0.5) / self.ss - cy) <= r:
                    self.blend(Y * self.W + X, color, alpha)

    def polyline(self, pts, width, color, alpha=1.0):
        for k in range(len(pts) - 1):
            self.line(pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1], width, color, alpha)

    def save(self, path, post=None):
        # SS×SS 칸을 평균내 원래 크기로 줄이고 PNG로 저장. post(x, y, rgba)로 픽셀 후처리 가능
        s = self.ss
        rows = []
        for y in range(self.h):
            row = bytearray(b'\x00')
            for x in range(self.w):
                acc = [0.0, 0.0, 0.0, 0.0]
                for yy in range(y * s, y * s + s):
                    for xx in range(x * s, x * s + s):
                        p = self.px[yy * self.W + xx]
                        for k in range(3):
                            acc[k] += p[k] * p[3]       # 알파를 곱해 평균 (가장자리 색 번짐 방지)
                        acc[3] += p[3]
                a = acc[3] / (s * s)
                rgb = [acc[k] / acc[3] if acc[3] > 0 else 0 for k in range(3)]
                rgba = rgb + [a * 255]
                if post:
                    rgba = post(x, y, rgba)
                row += bytes(max(0, min(255, int(v + 0.5))) for v in rgba)
            rows.append(bytes(row))
        chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
        png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', self.w, self.h, 8, 6, 0, 0, 0))
               + chunk(b'IDAT', zlib.compress(b''.join(rows), 9)) + chunk(b'IEND', b''))
        with open(path, 'wb') as f:
            f.write(png)
        print('saved', os.path.normpath(path))


def square(cx, cy, size, angle):
    # 회전한 정사각형의 네 꼭짓점 (시계 방향, 이 그림 좌표 기준)
    c, s, h = math.cos(angle), math.sin(angle), size / 2
    return [(cx + px * c - py * s, cy + px * s + py * c) for px, py in [(-h, -h), (h, -h), (h, h), (-h, h)]]


def segment(cv, cx, cy, size, angle, body=(34, 42, 70), edge=(225, 230, 238)):
    # 게임 속 마디와 같은 그림체: 반투명 몸 + 은은한 하이라이트 + 빛 방향 테두리
    cv.poly(square(cx, cy, size, angle), body, 0.92)
    lx, ly = LIGHT
    cv.poly(square(cx + lx * size * 0.1, cy + ly * size * 0.1, size * 0.7, angle), (90, 108, 160), 0.22)
    pts = square(cx, cy, size, angle)
    for k in range(4):
        (x1, y1), (x2, y2) = pts[k], pts[(k + 1) % 4]
        nx, ny = -(y2 - y1) / size, (x2 - x1) / size        # 변의 바깥쪽 방향 (시계 방향 꼭짓점 기준)
        lit = (nx * lx + ny * ly + 1) / 2
        f = 0.35 + 0.65 * lit
        cv.line(x1, y1, x2, y2, max(1.0, size / 14), tuple(v * f for v in edge))


def leg(cv, sx, sy, fx, fy, l1, l2, side, width, color):
    # 2관절 다리: 어깨(sx,sy) → 무릎 → 발(fx,fy). 무릎은 side(+1/-1) 쪽 바깥으로 꺾인다
    d = max(abs(l1 - l2) + 0.01, min(l1 + l2 - 0.01, math.hypot(fx - sx, fy - sy)))
    theta = math.atan2(fy - sy, fx - sx)
    alpha = math.acos((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))     # 코사인 법칙
    kx = sx + l1 * math.cos(theta + side * alpha)
    ky = sy + l1 * math.sin(theta + side * alpha)
    cv.line(sx, sy, kx, ky, width, color)
    cv.line(kx, ky, fx, fy, width * 0.75, color)
    cv.circle(fx, fy, width * 0.7, color)


def make_logo():
    # 선으로 된 지구본 + 위쪽 둘레를 기어가는 작은 크롤러
    cv = Canvas(36, 36, 6)
    cx, cy, r = 18, 22, 12
    ring = (200, 205, 215)
    circle_pts = [(cx + r * math.cos(t / 48 * 2 * math.pi), cy + r * math.sin(t / 48 * 2 * math.pi)) for t in range(49)]
    cv.polyline(circle_pts, 1.6, ring)
    for k in (0.42, 0.82):                                   # 경선 (세로 타원)
        pts = [(cx + r * k * math.sin(t / 48 * 2 * math.pi), cy + r * math.cos(t / 48 * 2 * math.pi)) for t in range(49)]
        cv.polyline(pts, 0.9, ring, 0.8)
    cv.line(cx, cy - r, cx, cy + r, 0.9, ring, 0.8)
    for dy in (-6, 0, 6):                                    # 위선 (가로줄)
        half = math.sqrt(r * r - dy * dy)
        cv.line(cx - half, cy + dy, cx + half, cy + dy, 0.9, ring, 0.8)
    # 둘레 위쪽에 마디 3개짜리 크롤러 (둘레를 따라 기울어짐)
    for i, t in enumerate([-1.25, -1.62, -1.99]):            # 둘레 위 각도 (라디안, 위쪽)
        px, py = cx + (r + 2.6) * math.cos(t), cy + (r + 2.6) * math.sin(t)
        ang = t + math.pi / 2
        for side in (1, -1):                                 # 다리 한 쌍 (짧게)
            fx, fy = cx + (r + 5.5) * math.cos(t + side * 0.2), cy + (r + 5.5) * math.sin(t + side * 0.2)
            cv.line(px, py, fx, fy, 0.8, (210, 214, 222))
        segment(cv, px, py, 4.6 if i else 5.2, ang)
    hx, hy = cx + (r + 2.6) * math.cos(-1.25), cy + (r + 2.6) * math.sin(-1.25)
    cv.circle(hx + 1.6, hy + 0.2, 0.9, (255, 150, 40))       # 머리 주황 점
    cv.save(os.path.join(OUT_DIR, 'wiki_logo.png'))


def make_photo():
    # 어두운 페이지 위를 기어가는 개체를 찍은 흐릿한 사진
    W, H = 220, 150
    cv = Canvas(W, H, 3, bg=(22, 26, 32, 1))
    rng = random.Random(3)
    # 초점이 나간 배경 글줄 (같은 막대를 조금씩 어긋나게 여러 번 → 번진 느낌)
    for row in range(9):
        y = 12 + row * 15
        x = 10
        while x < W - 20:
            length = rng.randint(18, 60)
            color, a = ((136, 163, 232), 0.35) if rng.random() < 0.12 else ((90, 96, 108), 0.22)   # 가끔 파란 링크 단어
            for ox, oy in [(0, 0), (1.2, 0.6), (-1.2, -0.6)]:
                cv.line(x + ox, y + oy, x + length + ox, y + oy, 4.5, color, a)
            x += length + rng.randint(6, 12)
    # 크롤러: 마디 3개가 비스듬히, 다리 6개
    angle = -0.42                                            # 몸 방향 (오른쪽 위로)
    spacing, size = 31, 22
    cxh, cyh = 150, 62                                       # 머리 위치
    segs = [(cxh - math.cos(angle) * spacing * i, cyh - math.sin(angle) * spacing * i) for i in range(3)]
    fwd = (math.cos(angle), math.sin(angle))
    nrm = (-fwd[1], fwd[0])                                  # 몸의 옆 방향
    for x, y in segs:                                        # 그림자
        cv.poly(square(x + 5, y + 6, size + 3, angle), (0, 0, 0), 0.45)
    reach = [(14, 30), (-4, 34), (-16, 30)]                  # 마디별 발 위치 (앞뒤, 옆) — 같은 걸음이 없게 제각각
    for i, (x, y) in enumerate(segs):
        for side in (1, -1):
            fwd_off, side_off = reach[i]
            fwd_off += rng.uniform(-5, 5) + (6 if side < 0 else 0)
            sx, sy = x + nrm[0] * size / 2 * side, y + nrm[1] * size / 2 * side
            fx = x + fwd[0] * fwd_off + nrm[0] * side_off * side
            fy = y + fwd[1] * fwd_off + nrm[1] * side_off * side
            cv.circle(fx + 3, fy + 4, 2.2, (0, 0, 0), 0.35)  # 발 그림자
            leg(cv, sx, sy, fx, fy, 19, 24, side, 2.4, (205, 210, 220))
    for i in range(2, -1, -1):                               # 꼬리부터 마디
        segment(cv, segs[i][0], segs[i][1], size + (2 if i == 0 else 0), angle)
    hx, hy = segs[0]
    cv.circle(hx + fwd[0] * 7, hy + fwd[1] * 7, 2.6, (255, 150, 40))   # 머리 주황 점

    def post(x, y, rgba):
        # 사진 느낌: 크롤러 쪽은 밝게(조명), 가장자리는 어둡게(비네트), 입자 노이즈
        d = math.hypot((x - 120) / W, (y - 75) / H)
        f = 1.15 - 0.9 * d * d
        n = rng.uniform(-7, 7)
        return [rgba[0] * f + n, rgba[1] * f + n, rgba[2] * f + n * 1.1, rgba[3]]
    cv.save(os.path.join(OUT_DIR, 'wiki_crawler.png'), post)


if __name__ == '__main__':
    make_logo()
    make_photo()
