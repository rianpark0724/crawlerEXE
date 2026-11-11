# 씬(모드) 전환 프레임워크 — 수업 프레임워크를 바탕으로 보강
# 모드는 init / finish / handle_events / update / draw / pause / resume 함수를 가진 모듈이다.
# 수업 원본과 다른 점:
#   1. frame_time 상한 (멈췄다 풀릴 때 순간이동·벽 통과 방지)
#   2. 모드 전환은 예약했다가 프레임 끝에 적용 (update 도중 상태가 지워지는 문제 방지)
#   3. change_mode / push_mode 에 인자를 넘기면 mode.init(인자)로 전달
#   4. 화면 지우기·표시는 프레임워크가 한 번만 → 모드의 draw()는 그리기만
#   5. time.perf_counter() 사용, 에러가 나도 모드 정리
import time
from pico2d import clear_canvas, update_canvas

import config

running = False
stack = []          # 모드 스택. 맨 위(stack[-1])가 현재 모드
frame_time = 0.0    # 직전 프레임에 걸린 시간(초). 이동량 = 속도 × frame_time
pending = []        # 이번 프레임 끝에 적용할 전환 예약 목록


def change_mode(mode, *args):
    # 현재 모드를 끝내고 새 모드로 교체 (프레임 끝에 적용)
    pending.append(('change', mode, args))


def push_mode(mode, *args):
    # 현재 모드를 멈춰 두고 새 모드를 위에 올림 (일시정지 화면 등)
    pending.append(('push', mode, args))


def pop_mode():
    # 맨 위 모드를 끝내고 아래 모드로 복귀
    pending.append(('pop', None, ()))


def quit():
    global running
    running = False


def apply_pending():
    # 예약된 전환을 순서대로 실제로 적용
    while len(pending) > 0:
        kind, mode, args = pending.pop(0)
        if kind == 'change':
            if len(stack) > 0:
                stack[-1].finish()
                stack.pop()
            stack.append(mode)
            mode.init(*args)
        elif kind == 'push':
            if len(stack) > 0:
                stack[-1].pause()
            stack.append(mode)
            mode.init(*args)
        elif kind == 'pop':
            if len(stack) > 0:
                stack[-1].finish()
                stack.pop()
            if len(stack) > 0:
                stack[-1].resume()
            else:
                quit()   # 남은 모드가 없으면 종료


def run(start_mode, *args):
    global running, frame_time
    running = True
    stack.append(start_mode)
    start_mode.init(*args)

    current_time = time.perf_counter()
    try:
        while running:
            mode = stack[-1]
            mode.handle_events()
            if len(pending) == 0:      # 이벤트 처리 중 전환이 예약됐으면 이번 프레임 update 생략
                mode.update()
            clear_canvas()
            mode.draw()
            update_canvas()
            apply_pending()

            now = time.perf_counter()
            frame_time = min(now - current_time, config.MAX_FRAME_TIME)  # 이번 프레임 소요 시간 (상한 적용)
            current_time = now
    finally:
        # 정상 종료든 에러든 남은 모드 모두 정리
        while len(stack) > 0:
            stack[-1].finish()
            stack.pop()
