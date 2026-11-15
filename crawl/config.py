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
COLOR_BG     = (16, 20, 24)      # 배경 (위키백과 어두운 테마 #101418)
COLOR_WHITE  = (235, 238, 245)   # 크롤러 몸·다리 기본 선
COLOR_GRAY   = (110, 116, 135)   # 비활성(잠긴 출구, 흐린 글줄)
COLOR_ORANGE = (255, 150, 40)    # 머리 표식, 출구 링크
COLOR_SKY    = (90, 200, 255)    # 데이터 조각
COLOR_RED    = (240, 70, 70)     # 피격, 잃은 다리
COLOR_GREEN  = (90, 220, 120)    # 디버그: 무적, 착지
COLOR_YELLOW = (250, 220, 80)    # 디버그: 목표 지점
COLOR_BODY   = (34, 42, 70)      # 크롤러 마디 안쪽 채움
COLOR_BODY_LIGHT = (90, 108, 160)  # 마디 윗면 하이라이트

# ── 위키 페이지 (위키백과 Vector 2022 어두운 테마를 레퍼런스로) ──
WIKI_TEXT    = (234, 236, 240)   # #eaecf0 본문
WIKI_SUBTLE  = (162, 169, 177)   # #a2a9b1 보조 글 (안내문·캡션)
WIKI_LINK    = (136, 163, 232)   # #88a3e8 링크
WIKI_VISITED = (167, 153, 205)   # #a799cd 방문한 링크 — 수집한 데이터 조각 (S05)
WIKI_REDLINK = (253, 120, 101)   # #fd7865 아직 없는 문서 링크
WIKI_BORDER  = (84, 89, 93)      # #54595d 구분선
WIKI_BORDER_STRONG = (114, 119, 125)  # #72777d 상자·검색창 테두리
WIKI_BOX_BG  = (32, 33, 34)      # 그림 틀·분류 상자 안쪽
WIKI_ALPHA   = 0.55              # 페이지 전체 밝기 (1.0 = 위키백과 그대로, 낮을수록 크롤러가 잘 보임)

# ── 커서 ──────────────────────────────
CURSOR_SIZE = 8           # 커서 십자 팔 길이

# ── □ 사각형 BOX (PRD 6.1) ────────────
BOX_TURN_SPEED = 3.5      # 머리 최대 회전 속도 (rad/s)
BOX_BASE_SPEED = 120      # 기본 이동 속도 (px/s)
BOX_SPEED_PER_PAIR = 8    # 다리 한 쌍당 추가 속도 (px/s)
BOX_SLOW_FACTOR = 2.2     # 커서 근처 감속: 속도 상한 = 커서까지 거리 × 이 값
BOX_STOP_DIST = 3         # 커서와 이 거리 안이면 멈춤 (떨림 방지)
BOX_MIN_FACING = 0.2      # 커서와 다른 방향을 볼 때 속도 배율 하한 (속도 × max(이 값, cos(각도 차)))
BOX_START_LEGS = 6        # 시작 다리 수 (S04 다리가 생기기 전까지 속도 계산에 사용)
BOX_START_SEGS = 3        # 시작 마디 수 (머리 포함)
BOX_SEG_SIZE = 14         # 몸통 마디 한 변
BOX_HEAD_SIZE = 16        # 머리 한 변
BOX_EYE_SIZE = 4          # 머리 앞쪽 주황 점 한 변
BOX_BODY_ALPHA = 0.55     # 마디 채움 투명도 (1 = 불투명) — 아래 페이지 글이 비침
BOX_HIGHLIGHT_ALPHA = 0.18  # 윗면 하이라이트 투명도 (은은하게)
BOX_HIGHLIGHT_SIZE = 0.7  # 하이라이트 크기 (마디 한 변 대비) — 크게 해서 몸 색과 섞이게
BOX_HIGHLIGHT_SHIFT = 0.1 # 하이라이트를 빛 쪽으로 옮기는 정도 (마디 한 변 대비)

# ── 입체감 (빛·그림자) ────────────────
LIGHT_DIR = (-0.7071, 0.7071)   # 빛이 오는 방향 (왼쪽 위, 단위 벡터)
EDGE_DARK = 0.35          # 빛을 등진 테두리 밝기 배율 (빛 정면 = 1.0)
SHADOW_DX = 3             # 그림자 어긋남 (오른쪽 아래)
SHADOW_DY = -4
SHADOW_ALPHA = 0.45       # 그림자 진하기

# ── 페이지 (PRD 10.1) ─────────────────
TEST_PAGE_HEIGHT = 1440   # S05 스테이지 JSON 전까지 쓰는 임시 페이지 높이 (wiki.json과 같음)
TEST_SPAWN = (640, 1300)  # 임시 시작 위치 (wiki.json과 같음)
WIKI_HEADER_H = 56        # 맨 위 머리글(로고·검색창) 높이
WIKI_TOC_X = 24           # 왼쪽 목차 x
WIKI_CONTENT_X = 240      # 본문 왼쪽 x
WIKI_CONTENT_W = 900      # 본문 폭
WIKI_LINE_H = 22          # 본문 줄 높이 (14px × 1.6)
WIKI_FONT_BODY = 14       # 본문 글자
WIKI_FONT_SMALL = 12      # 캡션·각주·바닥글
WIKI_FONT_REF = 10        # 각주 번호 [1]
WIKI_FONT_H2 = 22         # 큰 소제목
WIKI_FONT_H3 = 16         # 작은 소제목
WIKI_FONT_TITLE = 28      # 문서 제목

# ── 카메라 (PRD 10.2) ─────────────────
CAM_DEADZONE = 0.4        # 화면 가운데 이 비율 구간에서는 카메라가 움직이지 않음
CAM_SMOOTH = 6            # 따라가는 부드러움: 매 초 남은 거리의 이 배수만큼 (클수록 빨리 붙음)

# ── HUD 스크롤바 (PRD 10.4) ───────────
SCROLL_W = 12             # 스크롤바 폭 (화면 오른쪽 끝)
SCROLL_PAD = 2            # 막대와 트랙 사이 여백
SCROLL_MIN_THUMB = 24     # 막대 최소 길이 (아주 긴 페이지에서도 보이게)
SCROLL_TRACK = (28, 31, 36)    # 트랙 색
SCROLL_THUMB = (110, 116, 126) # 막대 색

# ── 몸통 공통 (PRD 5.1) ───────────────
SEG_SPACING = 19          # 마디 사이 거리

# ── 그리기 ────────────────────────────
CIRCLE_SIDES = 24         # 원 윤곽을 몇 개의 선으로 근사할지
FONT_SIZE = 14            # 디버그 글자 크기
FONT_UI_PATH = r'C:\Windows\Fonts\malgun.ttf'      # 맑은 고딕 — 없으면 pico2d 기본 글꼴로 대체
FONT_BOLD_PATH = r'C:\Windows\Fonts\malgunbd.ttf'  # 맑은 고딕 굵게

# ── 경로 ──────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))     # crawl/ 폴더 (어디서 실행해도 같은 경로)
IMAGE_DIR = os.path.join(BASE_DIR, 'assets', 'images')
PAGE_DIR = os.path.join(BASE_DIR, 'data', 'pages')       # 페이지 문서(글) JSON
