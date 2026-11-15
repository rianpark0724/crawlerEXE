# 모든 수치 상수 — PRD의 '초기값'은 전부 여기에 둔다.
# 길이 px · 시간 초 · 각도 라디안 · 색 (R, G, B) 0–255
import os

# ── 화면 ──────────────────────────────
SCREEN_W = 1280
SCREEN_H = 720
VSYNC = True              # 모니터 주사율에 맞춤

# ── 프레임 ────────────────────────────
MAX_FRAME_TIME = 0.05     # frame_time 상한. 20fps 이하로 떨어지면 게임이 느려지는 쪽을 택함
SHOW_FPS = True           # 왼쪽 위 FPS 표시 (디버그)
FPS_INTERVAL = 0.5        # FPS 숫자를 몇 초마다 갱신할지

# ── 색상 ──────────────────────────────
COLOR_BG     = (16, 20, 38)      # 배경 남색 (S01-5에서 사용)
COLOR_WHITE  = (235, 238, 245)   # 크롤러 몸·다리 기본 선
COLOR_GRAY   = (110, 116, 135)   # 비활성(잠긴 출구, 흐린 글줄)
COLOR_ORANGE = (255, 150, 40)    # 머리 표식, 출구 링크
COLOR_SKY    = (90, 200, 255)    # 데이터 조각
COLOR_RED    = (240, 70, 70)     # 피격, 잃은 다리
COLOR_GREEN  = (90, 220, 120)    # 디버그: 무적, 착지
COLOR_YELLOW = (250, 220, 80)    # 디버그: 목표 지점
COLOR_BODY   = (34, 42, 70)      # 크롤러 마디 안쪽 채움

# ── 커서 ──────────────────────────────
CURSOR_SIZE = 8           # 커서 십자 팔 길이

# ── □ 사각형 BOX (PRD 6.1) ────────────
BOX_TURN_SPEED = 3.5      # 머리 최대 회전 속도 (rad/s)
BOX_BASE_SPEED = 120      # 기본 이동 속도 (px/s)
BOX_SPEED_PER_PAIR = 8    # 다리 한 쌍당 추가 속도 (px/s)
BOX_START_LEGS = 6        # 시작 다리 수 (S04 다리가 생기기 전까지 속도 계산에 사용)
BOX_START_SEGS = 3        # 시작 마디 수 (머리 포함)
BOX_SEG_SIZE = 14         # 몸통 마디 한 변
BOX_HEAD_SIZE = 16        # 머리 한 변
BOX_EYE_SIZE = 4          # 머리 앞쪽 주황 점 한 변

# ── 몸통 공통 (PRD 5.1) ───────────────
SEG_SPACING = 19          # 마디 사이 거리

# ── 그리기 ────────────────────────────
CIRCLE_SIDES = 24         # 원 윤곽을 몇 개의 선으로 근사할지
FONT_SIZE = 14            # 기본 글자 크기

# ── 경로 ──────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))     # crawl/ 폴더 (어디서 실행해도 같은 경로)
IMAGE_DIR = os.path.join(BASE_DIR, 'assets', 'images')
