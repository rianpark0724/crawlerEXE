# 모든 수치 상수 — PRD의 '초기값'은 전부 여기에 둔다.
# 길이 px · 시간 초 · 각도 라디안 · 색 (R, G, B) 0–255
import os

# ── 화면 ──────────────────────────────
SCREEN_W = 1280
SCREEN_H = 720
VSYNC = True              # 모니터 주사율에 맞춤

# ── 프레임 ────────────────────────────
MAX_FRAME_TIME = 0.05     # frame_time 상한. 20fps 이하로 떨어지면 게임이 느려지는 쪽을 택함
DEBUG_START = False       # 시작할 때 F1 디버그 뷰를 켤지
DEBUG_LAND_TIME = 0.3     # 디버그: 착지 원이 퍼지는 시간
DEBUG_LAND_R = 15         # 디버그: 착지 원이 퍼지는 크기 (px)
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
COLOR_GOLD   = (255, 196, 60)    # 목표 키워드 (먹으면 탈출)
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
LINK_ALPHA   = 1.0               # 아직 안 먹은 파란 링크 밝기 — 페이지 글보다 밝게 해서 먹을 수 있음을 표시

# ── 수집 (PRD 5.3, 11.3) ──────────────
COLLECT_MARGIN = 8        # 링크 단어 상자 바깥으로 이만큼까지 착지하면 먹음 (px). 4는 자꾸 빗나가고 12는 너무 넉넉해서 8
COLLECT_FX_TIME = 0.4     # 먹은 링크가 번쩍였다 보라로 가라앉는 시간, 수집 원이 퍼지는 시간
COLLECT_FX_R = 22         # 수집 원이 퍼지는 크기 (px)
GOAL_PULSE = 4.0          # 목표 키워드가 반짝이는 빠르기
SHORT_MSG_TIME = 1.5      # '크롤링이 부족합니다' 글이 떠 있는 시간 (초)
SHORT_MSG_RISE = 30       # 그동안 위로 떠오르는 거리 (px)
CLEAR_W, CLEAR_H = 520, 210   # CLEAR 판 크기

# ── 페이지 출구 = 다음 문서 상자 (PRD 11.3-3) ──
EXIT_ROWS, EXIT_COLS = 1, 5   # 칸 배치: 한 줄 5칸 (방문 대기열 4 + 뒤로). 두 줄이면 아래 칸에 가다 위 칸을 밟게 됨
EXIT_SLOT_H = 48          # 칸 높이 — 링크 단어보다 커서 판정 여유 없이 칸 안에 착지해야 이동
EXIT_GAP = 12             # 칸 사이 간격
EXIT_PAD = 14             # 상자 안쪽 여백
EXIT_TITLE_H = 30         # 상자 제목('다음 문서') 줄 높이
EXIT_DASH = 8             # 잠긴 상자 점선 한 토막 길이
EXIT_PULSE = 3.0          # 열린 상자 테두리가 깜빡이는 빠르기 (초당 라디안 배수)
EXIT_STEPS = 3            # 한 칸에 발이 이만큼 연속 착지하면 그 문서로 이동 (지나가다 밟는 실수 방지)
EXIT_FORGET = 0.8         # 이 시간 동안 그 칸을 안 밟으면 채운 것이 비워짐 (초)
OPEN_TIME = 0.45          # 새 창이 열리는 시간 (밟은 칸 → 화면 가득, 이 동안 게임 멈춤)
OPEN_TYPE_PART = 0.7      # 그중 주소칸에 새 주소가 다 입력되기까지의 비율
OPEN_TITLE_H = 28         # 열리는 창 위쪽 제목 줄 높이
OPEN_SKELETON = (0.35, 0.9, 0.82, 0.88, 0.6, 0.0, 0.9, 0.75, 0.85, 0.5, 0.0, 0.88, 0.8, 0.9, 0.7, 0.86, 0.4, 0.0, 0.9, 0.8)   # 열리는 창 안 회색 글줄 길이 비율 (0 = 빈 줄)
PAGE_FADE_TIME = 0.3      # 문서를 옮긴 뒤 화면이 밝아지는 시간 (초)

# ── 커서 ──────────────────────────────
CURSOR_SIZE = 8           # 커서 십자 팔 길이

# ── □ 사각형 BOX (PRD 6.1) ────────────
BOX_TURN_SPEED = 3.5      # 머리 최대 회전 속도 (rad/s)
BOX_BASE_SPEED = 120      # 기본 이동 속도 (px/s)
BOX_SPEED_PER_PAIR = 8    # 다리 한 쌍당 추가 속도 (px/s)
BOX_SLOW_FACTOR = 2.2     # 커서 근처 감속: 속도 상한 = 커서까지 거리 × 이 값
BOX_STOP_DIST = 3         # 커서와 이 거리 안이면 멈춤 (떨림 방지)
BOX_MIN_FACING = 0.2      # 커서와 다른 방향을 볼 때 속도 배율 하한 (속도 × max(이 값, cos(각도 차)))
BOX_START_SEGS = 3        # 시작 마디 수 (머리 포함)
BOX_SEG_SIZE = 14         # 몸통 마디 한 변
BOX_HEAD_SIZE = 16        # 머리 한 변
BOX_EYE_SIZE = 4          # 머리 앞쪽 주황 점 한 변
BOX_BODY_ALPHA = 0.55     # 마디 채움 투명도 (1 = 불투명) — 아래 페이지 글이 비침
BOX_HIGHLIGHT_ALPHA = 0.18  # 윗면 하이라이트 투명도 (은은하게)
BOX_HIGHLIGHT_SIZE = 0.7  # 하이라이트 크기 (마디 한 변 대비) — 크게 해서 몸 색과 섞이게
BOX_HIGHLIGHT_SHIFT = 0.1 # 하이라이트를 빛 쪽으로 옮기는 정도 (마디 한 변 대비)

# ── 좌클릭 질주 (PRD 4장) ─────────────
SPRINT_SPEED = 1.6        # 질주 중 속도 배율
SPRINT_STRIDE = 1.4       # 질주 중 임계 거리 배율 → 보폭이 커지고 발 위치가 덜 정확해짐
SPRINT_ACCEL = 8          # 관성: 누르면 배율이 매 초 남은 차이의 이 배수만큼 올라감 (약 0.12초)
SPRINT_DECEL = 3          # 관성: 떼면 이 배수로 천천히 내려감 (약 0.33초) → 떼도 한동안 밀려감
SPRINT_TURN_LOSS = 0.6    # 대가: 최고 속도 질주 중 회전 속도 ×(1 − 이 값) = ×0.4
BRAKE_WALK = 3000         # 걸을 때 제동력 (px/s²) — 거의 바로 섬
BRAKE_SPRINT = 250        # 질주 중 제동력 (px/s²) — 약해서 커서를 지나쳐 미끄러짐 (대가)
SPRINT_LAND_KICK = 2.5    # 질주 중 착지 반동 배율
# 질주가 눈에 보이게 (모두 질주 정도에 비례)
SPRINT_CROUCH = 2.5       # 몸을 이만큼 낮춤 (px)
SPRINT_SWEEP = 0.35       # 다리를 뒤로 젖힘 (rad, 약 20°)
SPRINT_LIFT = 0.8         # 발을 ×(1 + 이 값) 높이 차올림
GHOST_INTERVAL = 0.05     # 잔상 남기는 간격 (초)
GHOST_LIFE = 0.2          # 잔상이 사라지는 시간
GHOST_ALPHA = 0.3         # 잔상 진하기
GHOST_MIN_SPRINT = 0.5    # 질주 정도가 이 이상일 때만 잔상
PUFF_LIFE = 0.35          # 흙먼지가 사라지는 시간
PUFF_SPREAD = 9           # 흙먼지가 퍼지는 거리 (px)
PUFF_ALPHA = 0.6          # 흙먼지 진하기
PUFF_MIN_SPRINT = 0.3     # 질주 정도가 이 이상일 때만 흙먼지

# ── 걸음에 맞춘 몸 움직임 ─────────────
BODY_SURGE = 0.5          # 밀려가기: 속도가 ×(1 ± 이 값/2) 사이에서 출렁 (디딘 발 많으면 빠르게, 들린 발 많으면 느리게)
BODY_SWAY = 2.5           # 좌우 쏠림: 한쪽 다리가 들리면 몸이 디딘 쪽으로 최대 이만큼 (px)

LAND_KICK = 18            # 착지 반동: 발 하나가 착지할 때 몸을 아래로 치는 속도 (px/s)
BODY_SPRING = 900         # 몸 높이 용수철 세기 (클수록 빨리 돌아옴, 약 4.8번/초 흔들림)
BODY_DAMP = 20            # 몸 높이 흔들림 감쇠 (작을수록 오래 통통 튐)
BODY_BOUNCE_MAX = 4       # 몸 높이가 원래에서 벗어날 수 있는 최대 (px)

# ── 입체감 (빛·그림자) ────────────────
BODY_HEIGHT = 8           # 몸(어깨)이 바닥에서 떠 있는 높이 (px). 그림자 (SHADOW_DX, SHADOW_DY)는 이 높이 기준
VIEW_TILT = 0.5           # 비스듬한 시점: 높이 z인 점을 화면 위로 z × 이 값만큼 올려 그림
LIGHT_DIR = (-0.7071, 0.7071)   # 빛이 오는 방향 (왼쪽 위, 단위 벡터)
EDGE_DARK = 0.35          # 빛을 등진 테두리 밝기 배율 (빛 정면 = 1.0)
SHADOW_DX = 3             # 그림자 어긋남 (오른쪽 아래)
SHADOW_DY = -4
SHADOW_ALPHA = 0.45       # 그림자 진하기

# ── 페이지 (PRD 10.1) ─────────────────
RANDOM_SEED = None        # 숫자를 넣으면 매번 같은 판(목표·키워드 자리), None이면 매번 다르게 (PRD 11.3-7)
FIRST_STAGE = 'wiki'      # 처음 시작하는 사이트 (data/stages/<id>.json)
PAGE_TRIAL_H = 100000     # 문서 높이를 재려고 한 번 배치해 보는 임시 높이
PAGE_BOTTOM_PAD = 60      # 문서 바닥글 아래 여백
SPAWN_FROM_TOP = 140      # 시작 위치: 문서 맨 위에서 이만큼 아래 (가운데)
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

# ── 다리 (PRD 5.2) ────────────────────
# 다리마다 아래 범위에서 무작위로 정해지는 개성 (실행할 때마다 걸음새가 다름)
LEG_L1_RANGE = (15, 24)          # 허벅지 길이
LEG_L2_RANGE = (17, 30)          # 종아리 길이
LEG_REACH_RANGE = (0.62, 0.78)   # 이상적 발 거리 = (L1+L2) × 이 값
LEG_THRESHOLD_RANGE = (11, 20)   # 임계 거리: 발이 이상적 위치에서 이만큼 벗어나면 걸음
LEG_STEP_TIME_RANGE = (0.07, 0.13)  # 한 걸음 시간 (초)
LEG_TILT_RANDOM = 0.14           # 다리 기울기 무작위 ± (rad, 약 8°)
LEG_TILT = 0.35           # 다리 기울기 (rad, 약 20°): 머리 쪽 다리는 앞으로, 꼬리 쪽은 뒤로
LEG_LEAD = 0.08           # 이상적 위치를 이동 속도 × 이 시간만큼 앞에 (앞으로 미리 딛기)
LEG_TELEPORT = 5          # 임계 거리의 이 배수보다 멀어지면 걷지 않고 바로 옮김 (순간이동 등)
LEG_LIFT = 6              # 걸음 중 발을 들어 올리는 최대 높이 (px)
KNEE_SIDE = 0.6           # 무릎이 솟는 방향: 0 = 바로 위, 클수록 앞/뒤 꺾임 쪽으로 기울어짐 (rad, 약 35°)
KNEE_STYLE = 'centipede'  # 'centipede' 지네형: 모든 무릎이 뒤로 / 'spider' 거미형: 머리 쪽 다리만 무릎이 앞으로
LEG_MAX_STRETCH = 0.97    # 다리를 (L1+L2)의 이 비율까지만 편다 — 발이 더 멀어지면 바로 걸음, 못 걸으면 끌려옴
LEG_TUCK = 0.35           # 걸음 중 다리 오므리기: 걸음 한가운데서 어깨~발 거리를 이 비율만큼 줄임 (무릎이 접혔다 펴짐)
LEG_WIDTH = 2             # 허벅지 선 두께
LEG_WIDTH_SHIN = 1        # 종아리 선 두께
LEG_JOINT = 3             # 무릎 관절 점 크기
COLOR_LEG = (205, 210, 220)   # 다리 색

# ── 카메라 (PRD 10.2) ─────────────────
CAM_DEADZONE = 0.4        # 화면 가운데 이 비율 구간에서는 카메라가 움직이지 않음
CAM_SMOOTH = 6            # 따라가는 부드러움: 매 초 남은 거리의 이 배수만큼 (클수록 빨리 붙음)

# ── HUD 스크롤바 (PRD 10.4) ───────────
SCROLL_W = 12             # 스크롤바 폭 (화면 오른쪽 끝)
SCROLL_PAD = 2            # 막대와 트랙 사이 여백
SCROLL_MIN_THUMB = 24     # 막대 최소 길이 (아주 긴 페이지에서도 보이게)
SCROLL_TRACK = (28, 31, 36)    # 트랙 색
SCROLL_THUMB = (110, 116, 126) # 막대 색

# ── HUD 브라우저 띠 (PRD 12) ──────────
# 화면 맨 위 한 줄. 사이트가 바뀌어도 모양이 같은 '크롤러의 브라우저' — 페이지는 이 띠 아래로 보인다
HUD_BAR_H = 36            # 띠 높이 (이만큼 페이지가 보이는 창이 줄어듦)
HUD_BAR_BG = (24, 26, 30)       # 띠 바탕 (사이트 색과 상관없이 고정)
HUD_BAR_LINE = (58, 62, 70)     # 띠 아래 경계선, 입력칸 테두리
HUD_FIELD_BG = (12, 14, 17)     # 주소칸·목표칸 안쪽
HUD_FIELD_H = 24          # 입력칸 높이
HUD_FONT = 14             # 띠 글자
HUD_URL_X, HUD_URL_W = 118, 430       # 주소칸 위치·폭
HUD_GOAL_X, HUD_GOAL_W = 562, 210     # 목표칸 위치·폭
HUD_LABEL = (130, 136, 148)     # 이름표 글자 (crawl://, 방문 등)
HUD_DONE = COLOR_GREEN    # 채운 조건 (방문 수·이 문서 수집 수)
DEBUG_PANEL_TOP = HUD_BAR_H + 8   # F1 수치 판을 띠 아래부터 그림

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
STAGE_DIR = os.path.join(BASE_DIR, 'data', 'stages')     # 스테이지 배치 JSON (PRD 11.2)
