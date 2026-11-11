# CRAWL.EXE 시작점 — 창을 열고 play_mode로 게임 루프 실행
from pico2d import open_canvas, close_canvas

import game_framework
from modes import play_mode

SCREEN_W = 1280   # S01-2에서 config.py로 옮김
SCREEN_H = 720

open_canvas(SCREEN_W, SCREEN_H)
game_framework.run(play_mode)
close_canvas()
