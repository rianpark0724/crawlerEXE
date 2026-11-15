# 카메라 — 페이지를 세로로만 스크롤한다 (PRD 10.2, 10.3)
# y = 화면 아래쪽 가장자리의 월드 y. 화면 y = 월드 y − camera.y
# 게임 로직은 전부 월드 좌표, 그리기 직전에만 to_screen으로 바꾼다.
import config


class Camera:
    def __init__(self, page_height):
        # 페이지가 보이는 창 = 화면에서 위쪽 HUD 띠를 뺀 부분
        view_h = config.SCREEN_H - config.HUD_BAR_H
        self.max_y = max(0, page_height - view_h)             # 카메라가 갈 수 있는 가장 위 (페이지 맨 위가 띠 바로 아래)
        self.y = self.max_y                                   # 페이지 맨 위에서 시작
        # 데드존: 창 가운데 CAM_DEADZONE 비율 구간 (화면 y). 머리가 이 안에 있으면 카메라는 가만히
        margin = view_h * (1 - config.CAM_DEADZONE) / 2
        self.dead_low = margin                                # 데드존 아래 경계
        self.dead_high = view_h - margin                      # 데드존 위 경계

    def update(self, head_y, dt):
        # 머리가 데드존을 벗어나면, 머리가 데드존 경계에 오도록 하는 카메라 위치를 목표로 부드럽게 따라간다
        screen_y = head_y - self.y
        if screen_y < self.dead_low:
            target = head_y - self.dead_low       # 머리가 아래로 벗어남 → 카메라 내려감
        elif screen_y > self.dead_high:
            target = head_y - self.dead_high      # 머리가 위로 벗어남 → 카메라 올라감
        else:
            target = self.y
        self.y += (target - self.y) * min(1, config.CAM_SMOOTH * dt)   # 남은 거리의 일정 비율만큼 → 부드럽게 감속
        self.y = max(0, min(self.max_y, self.y))                       # 페이지 밖은 보이지 않게

    def to_screen(self, x, y):
        # 월드 → 화면. x는 가로 스크롤이 없어서 그대로
        return x, y - self.y

    def to_world(self, x, y):
        # 화면 → 월드
        return x, y + self.y
