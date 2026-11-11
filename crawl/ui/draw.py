# 선·도형 그리기 — pico2d에는 선 함수가 없어서 1×1 흰 픽셀 이미지를 늘리고 회전해 그린다.
# 좌표는 화면 좌표(원점 왼쪽 아래, y 위로 증가).
import math
import os
from pico2d import load_image

import config

pixel = None   # 1×1 흰 픽셀 이미지. open_canvas() 뒤 load()에서 읽는다.


def load():
    global pixel
    pixel = load_image(os.path.join(config.IMAGE_DIR, 'pixel.png'))


def draw_line(x1, y1, x2, y2, width=1):
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)          # 선 길이
    if length == 0:
        return
    angle = math.atan2(dy, dx)           # 선 방향(라디안)
    # 중점에 놓고, 가로=길이·세로=두께로 늘린 뒤 angle만큼 회전.
    # pico2d가 크기를 정수로 버림하므로 +1 해서 이어지는 선 사이 틈을 막는다.
    pixel.composite_draw(angle, '', (x1 + x2) / 2, (y1 + y2) / 2, length + 1, width)
