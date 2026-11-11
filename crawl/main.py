# CRAWL.EXE 시작점 — 창을 열고 play_mode로 게임 루프 실행
from pico2d import open_canvas, close_canvas

import config
import game_framework
from modes import play_mode

open_canvas(config.SCREEN_W, config.SCREEN_H, sync=config.VSYNC)
try:
    game_framework.run(play_mode)
finally:
    close_canvas()   # 에러가 나도 창·오디오 정리
