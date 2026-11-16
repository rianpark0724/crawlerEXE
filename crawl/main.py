# CRAWL.EXE 시작점 — 창을 열고 play_mode로 게임 루프 실행
# 보통은 crawl://home에서 시작. 개발용으로 사이트부터 시작하려면:  python main.py news   (data/stages/<id>.json)
import sys

from pico2d import open_canvas, close_canvas, hide_lattice

import config
import game_framework
from modes import play_mode
from ui import draw

open_canvas(config.SCREEN_W, config.SCREEN_H, sync=config.VSYNC)
hide_lattice()   # pico2d 기본 격자 끄기
draw.load()   # 이미지는 창이 열린 뒤에만 읽을 수 있다
try:
    start = sys.argv[1] if len(sys.argv) > 1 else 'home'
    game_framework.run(play_mode, start)
finally:
    close_canvas()   # 에러가 나도 창·오디오 정리
