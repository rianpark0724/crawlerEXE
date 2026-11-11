# CRAWL.EXE 시작점 — 창을 열고 play_mode로 게임 루프 실행
from pico2d import open_canvas, close_canvas, hide_lattice

import config
import game_framework
from modes import play_mode
from ui import draw

open_canvas(config.SCREEN_W, config.SCREEN_H, sync=config.VSYNC)
hide_lattice()   # pico2d 기본 격자 끄기
draw.load()   # 이미지는 창이 열린 뒤에만 읽을 수 있다
try:
    game_framework.run(play_mode)
finally:
    close_canvas()   # 에러가 나도 창·오디오 정리
