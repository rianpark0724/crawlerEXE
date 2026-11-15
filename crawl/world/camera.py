# 카메라 — 페이지를 세로로만 스크롤한다 (PRD 10.2, 10.3)
# y = 화면 아래쪽 가장자리의 월드 y. 화면 y = 월드 y − camera.y
# 게임 로직은 전부 월드 좌표, 그리기 직전에만 to_screen으로 바꾼다.


class Camera:
    def __init__(self):
        self.y = 0.0     # 지금은 0 고정 (S03-3에서 머리를 따라 움직임)

    def to_screen(self, x, y):
        # 월드 → 화면. x는 가로 스크롤이 없어서 그대로
        return x, y - self.y

    def to_world(self, x, y):
        # 화면 → 월드
        return x, y + self.y
