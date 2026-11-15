# 선·도형 그리기 — pico2d에는 선 함수가 없어서 1×1 흰 픽셀 이미지를 늘리고 회전해 그린다.
# 색은 흰 픽셀에 그릴 때마다 곱해서 입힌다(ColorMod). 투명도는 opacify(0~1).
# 좌표는 화면 좌표(원점 왼쪽 아래, y 위로 증가).
import math
import os
import pico2d
from pico2d import load_image, load_font, SDL_SetTextureColorMod

import config

pixel = None   # 1×1 흰 픽셀 이미지. open_canvas() 뒤 load()에서 읽는다.
font = None    # 기본 글꼴 — pico2d에 함께 설치되는 ConsolaMalgun(영문 고정폭 + 한글)


def load():
    global pixel, font
    pixel = load_image(os.path.join(config.IMAGE_DIR, 'pixel.png'))
    font = load_font(os.path.join(os.path.dirname(pico2d.__file__), 'data', 'ConsolaMalgun.ttf'), config.FONT_SIZE)


def set_color(color, alpha):
    # 흰색(255)에 color를 곱함 → 결과가 color. alpha는 0(투명)~1(불투명)
    r, g, b = color
    SDL_SetTextureColorMod(pixel.texture, r, g, b)
    pixel.opacify(alpha)


def draw_line(x1, y1, x2, y2, width=1, color=config.COLOR_WHITE, alpha=1.0):
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)          # 선 길이
    if length == 0:
        return
    angle = math.atan2(dy, dx)           # 선 방향(라디안)
    set_color(color, alpha)
    # 중점에 놓고, 가로=길이·세로=두께로 늘린 뒤 angle만큼 회전.
    # pico2d가 크기를 정수로 버림하므로 +1 해서 이어지는 선 사이 틈을 막는다.
    pixel.composite_draw(angle, '', (x1 + x2) / 2, (y1 + y2) / 2, length + 1, width)


def draw_circle(x, y, r, width=1, color=config.COLOR_WHITE, alpha=1.0):
    # 원 윤곽 = 둘레 위 CIRCLE_SIDES개의 점을 차례로 잇는 선
    n = config.CIRCLE_SIDES
    for i in range(n):
        a1 = 2 * math.pi * i / n
        a2 = 2 * math.pi * (i + 1) / n
        draw_line(x + r * math.cos(a1), y + r * math.sin(a1),
                  x + r * math.cos(a2), y + r * math.sin(a2), width, color, alpha)


def draw_rect(x, y, w, h, width=1, color=config.COLOR_WHITE, alpha=1.0):
    # 사각 윤곽. (x, y)는 왼쪽 아래 모서리 — 스테이지 JSON의 walls [x, y, w, h]와 같은 기준.
    # 가로 변을 두께의 절반만큼 양옆으로 늘려 모서리가 비지 않게 한다.
    hw = width / 2
    draw_line(x - hw, y, x + w + hw, y, width, color, alpha)            # 아래
    draw_line(x - hw, y + h, x + w + hw, y + h, width, color, alpha)    # 위
    draw_line(x, y, x, y + h, width, color, alpha)                      # 왼쪽
    draw_line(x + w, y, x + w, y + h, width, color, alpha)              # 오른쪽


def fill_rect_rotated(cx, cy, w, h, angle, color=config.COLOR_WHITE, alpha=1.0):
    # 회전한 꽉 찬 사각형. (cx, cy)는 중심, angle은 라디안 — 픽셀을 w×h로 늘려 돌린다
    set_color(color, alpha)
    pixel.composite_draw(angle, '', cx, cy, w, h)


def draw_rect_rotated(cx, cy, w, h, angle, width=1, color=config.COLOR_WHITE, alpha=1.0):
    # 회전한 사각 윤곽. 네 꼭짓점을 중심 기준으로 angle만큼 돌려 잇는다
    c, s = math.cos(angle), math.sin(angle)
    corners = []
    for lx, ly in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]:
        corners.append((cx + lx * c - ly * s, cy + lx * s + ly * c))   # 회전 변환
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i + 1) % 4]
        draw_line(x1, y1, x2, y2, width, color, alpha)


def fill_rect(x, y, w, h, color=config.COLOR_WHITE, alpha=1.0):
    # 꽉 찬 사각형. (x, y)는 왼쪽 아래 모서리
    set_color(color, alpha)
    pixel.draw_to_origin(x, y, w, h)


def draw_text(x, y, text, color=config.COLOR_WHITE):
    # 글자. (x, y)는 글줄의 왼쪽, 세로 가운데
    font.draw(x, y, text, color)
