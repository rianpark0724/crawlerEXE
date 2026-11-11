# 씬(모드) 전환 프레임워크 — 수업 프레임워크 형태
# 모드는 init / finish / handle_events / update / draw / pause / resume 함수를 가진 모듈이다.
import time

running = False
stack = []          # 모드 스택. 맨 위(stack[-1])가 현재 모드
frame_time = 0.0    # 직전 프레임에 걸린 시간(초). 이동량 = 속도 × frame_time


def change_mode(mode):
    # 현재 모드를 끝내고 새 모드로 교체
    if len(stack) > 0:
        stack[-1].finish()
        stack.pop()
    stack.append(mode)
    mode.init()


def push_mode(mode):
    # 현재 모드를 멈춰 두고 새 모드를 위에 올림 (일시정지 화면 등)
    if len(stack) > 0:
        stack[-1].pause()
    stack.append(mode)
    mode.init()


def pop_mode():
    # 맨 위 모드를 끝내고 아래 모드로 복귀
    if len(stack) > 0:
        stack[-1].finish()
        stack.pop()
    if len(stack) > 0:
        stack[-1].resume()


def quit():
    global running
    running = False


def run(start_mode):
    global running, frame_time
    running = True
    stack.append(start_mode)
    start_mode.init()

    current_time = time.time()
    while running:
        stack[-1].handle_events()
        stack[-1].update()
        stack[-1].draw()
        frame_time = time.time() - current_time  # 이번 프레임 소요 시간
        current_time += frame_time

    # 종료 시 남은 모드 모두 정리
    while len(stack) > 0:
        stack[-1].finish()
        stack.pop()
