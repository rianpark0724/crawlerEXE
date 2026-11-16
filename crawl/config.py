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
HIT_TEST_R = 16           # F1: 커서 위치 시험 판정 원 반지름 (닿은 다리 선분이 빨갛게) / F2 위험 지점 반지름
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
EATEN_SHELL = 0.55        # 먹은 링크(글자가 빠져나간 껍데기)의 밝기 = 페이지 밝기 × 이 값
INGEST_TIME = 0.4         # 링크 글자 하나가 머리로 빨려 들어가는 시간 (초)
INGEST_STAGGER = 0.03     # 글자마다 출발이 늦어지는 간격 (초) — 줄지어 빨려 들어감
INGEST_ARC = 26           # 글자가 밟은 발 위로 휘어 오르는 높이 (px)
GULP_TIME = 0.08          # 글자가 닿을 때 머리가 꿀꺽 납작해지는 시간 (초)
DIGEST_TIME = 0.45        # 단어를 다 삼키면 빛이 머리에서 꼬리까지 흘러가는 시간 (초)
STORE_PER_SEG = 9         # 마디 하나에 보이는 저장 조각 최대 수 (3 × 3)
STORE_DOT = 3.5           # 저장 조각 한 변 (px)

# ── 다리 파츠 (PRD 7, 8) ──
PART_REACH = 22           # 파츠 다리: 마디 중심에서 발까지 (바닥)
PART_KNEE_Z = 12          # 파츠 다리: 무릎 높이 (크롤러 다리처럼 위로 솟음)
PART_WIGGLE = 6           # 다리 꼼지락 빠르기
PART_WIGGLE_ANGLE = 0.35  # 꼼지락 폭 (rad)
PART_PICK_R = 14          # 발이 상자 중심에서 이 거리 안에 착지하면 주움
# ── 적 (PRD 9) ──
ENEMY_ACTIVE_PAD = 200    # 화면 위아래로 이만큼 안에 있는 적만 움직인다 (활성 범위)
ENEMY_SPAWN_GAP = 260     # 적은 시작 위치에서 이만큼 아래부터 놓는다 (시작하자마자 만나지 않게)
ENEMY_APART = 160         # 적끼리 떨어질 거리
REVERT_R = 12             # 되돌리기 봇 판정 반지름
REVERT_SPEED = 70         # 깨어났을 때 처음 속도 (px/s)
REVERT_GAIN = 4           # 발자국 하나를 읽을 때마다 빨라지는 양 (px/s)
REVERT_MAX = 180          # 최대 속도 (px/s)
REVERT_READ = 4           # 발자국에 이만큼 가까워지면 '읽음' → 다음 발자국으로 (px)
REVERT_LOST_TIME = 1.5    # 발자국이 끊기면(WAVE) 이 시간 동안 두리번거림 (초)
REVERT_HOME_SPEED = 60    # 제자리로 돌아가는 속도 (px/s)
REVERT_TRAIL_LIFE = 0.7   # 읽은 발자국에 남는 diff 줄(빨강·초록)이 사라지는 시간 (초)
FOOTPRINT_GAP = 20        # 발자국 = 착지할 때 머리 자리, 마지막 발자국에서 이만큼 움직였을 때만 기록 (지나간 길)
FOOTPRINT_MAX = 600       # 문서마다 기억하는 발자국 수 (오래된 것부터 버림)
REVERT_LINK_R = 16        # 추적 중인 봇이 먹힌 링크 상자에서 이만큼 안을 지나면 그 링크를 되돌림 (px)
AD_W, AD_H = 240, 150     # 광고 팝업 크기 (px)
AD_FIRST = 4.0            # 문서에 들어와서 첫 광고까지 (초)
AD_PERIOD = 7.0           # 광고가 떨어지는 간격 (초, ±20%)
AD_MAX = 2                # 한 문서에 동시에 떠 있는 광고 수
AD_LEAD = 0.9             # 머리가 이만큼 뒤에 있을 자리에 떨어뜨림 (초) — 가던 길 앞을 막음
AD_WARN = 0.9             # 그림자 경고 시간 (초) — 이 안에 피하거나 WAVE
AD_SLAM = 0.12            # 떨어지는 순간 (맞는 시간, 초)
AD_STAY = 6.0             # 벽으로 남아 있는 시간 (초) — 지나면 저절로 닫힘
AD_CLOSE_SIZE = 26        # 닫기 칸 크기 (px)
AD_CLOSE_MARGIN = 8       # 닫기 칸 바깥으로 이만큼까지 디뎌도 셈 (px)
AD_CLOSE_STEPS = 2        # 닫기 칸을 이만큼 디디면 닫힘
AD_CLOSE_FORGET = 1.2     # 이 시간 안에 이어서 디뎌야 함 (초)
AD_CLOSE_TIME = 0.25      # 닫히는 연출 시간 (초)
COMMENT_TOTAL = 12         # 댓글 둥지 하나에서 나오는 말풍선 벌레 수
COMMENT_ALIVE = 8         # 한 둥지에서 동시에 나와 있을 수 있는 벌레 수
COMMENT_SPAWN = 0.8       # 벌레가 하나씩 나오는 간격 (초)
COMMENT_WAKE = 450        # 머리가 둥지에서 이만큼 안에 오면 벌레가 나오기 시작 (px)
COMMENT_SPEED = 95        # 벌레가 기어 오는 속도 (px/s) — 걷기보다 조금 느리고 질주면 따돌림
COMMENT_R = 6             # 마디에 이만큼 가까이 오면 달라붙음 (px, 마디 반지름에 더함)
COMMENT_SLOW = 0.16       # 붙은 벌레 하나당 느려지는 비율 (6마리면 거의 못 움직임 — 돌아서 떨쳐야 함)
COMMENT_SLOW_MAX = 0.95   # 아무리 많이 붙어도 이만큼까지만 느려짐
COMMENT_GRIP = 1.2        # 버티는 힘 — 몸을 빠르게 돌린 양(rad/s를 넘긴 만큼 × 초)이 이만큼 쌓이면 떨어짐
COMMENT_SPIN = 2.5        # 붙은 마디가 이보다 빠르게 돌아야 (rad/s) 버티는 힘이 줄어듦
COMMENT_REGRIP = 0.6      # 천천히 돌 때 버티는 힘이 다시 차는 속도 (/s)
COMMENT_FLING = 320       # 떨쳐질 때 날아가는 속도 (px/s)
COMMENT_FRICTION = 4.0    # 날아가다 느려지는 정도
COMMENT_DAZE = 1.4        # 떨어진 뒤 어리둥절한 시간 (초) — 이때 밟으면 터짐
COMMENT_STOMP = 6         # 발이 말풍선 바깥으로 이만큼까지 디뎌도 밟힘 (px)
COMMENT_POP_TIME = 0.3    # 터지는 연출 시간 (초)
REVERT_HIT_PAUSE = 1.2    # 다리를 자른 뒤 봇이 멈추는 시간 (초) — 가만히 있어도 바로 또 잘리지 않게
REVERT_PAUSE = 0.5        # 다리를 자르거나 링크를 되돌린 뒤 봇이 멈칫하는 시간 (초)
REVERT_DEL_TIME = 0.35    # 되돌린 링크: 빨간 배경 + 취소선(지워짐) 시간
REVERT_ADD_TIME = 0.8     # 그다음 초록 배경(복구됨)이 사라지는 시간
REVERT_FX_R = 40          # 되돌릴 때 봇에서 퍼지는 원 크기
DATA_FLASH = 0.6          # 데이터를 잃으면 띠의 DATA가 빨갛게 깜빡이는 시간 (초)
BAND_H = 24               # 새로 고침 띠 두께 (px)
BAND_PASS = 1.2           # 화면 위 → 아래를 훑는 시간 (초)
BAND_WARN = 0.5           # 훑기 전 경고 시간 (초) — 화면 맨 위 빨간 점선·↻ 깜빡임
BAND_MIN_GAP = 3.0        # 한 문서에서 띠와 띠 사이 최소 간격 (초) — WAVE 한 주기(파동 + 대기 ≈ 2.15초)보다 길게 (검사기가 확인)
BAND_PERIOD = 4.0         # 기본 주기 (초) — 문서 설정 beams의 period로 바꿀 수 있음
WALL_PAD = 6              # 보호된 문단: 문단 글 바깥으로 판정·테두리를 넓히는 여백 (px)
WALL_KNOCK = 40           # 닿으면 문단 바깥쪽으로 튕겨 나가는 거리 (px)
KNOCK_DECAY = 10          # 튕겨 나가는 속도가 줄어드는 빠르기 (이동 거리 = 처음 속도 / 이 값)
WALL_EXIT_GAP = 120       # 출구 상자 위 이만큼 안의 문단도 보호하지 않음 (출구 가는 길을 막지 않게)
WALL_SPAWN_GAP = 220      # 시작 위치에서 이만큼 안의 문단은 보호하지 않음 (들어오자마자 막히지 않게)
REVERT_IDLE_SPIN = 1.5    # 대기 중 ↺ 화살표가 도는 빠르기 (rad/s)
REVERT_AWAKE_SPIN = 9     # 깨어난 뒤 도는 빠르기
GROW_POP = 0.15           # 새 마디가 붙을 때 납작했다 펴지는 시간 (초) — 붙는 순간이 보이게
PART_AVOID = 40           # 무작위 배치 때 링크·키워드·출구에서 떨어질 거리
PART_SPAWN_GAP = 160      # 시작 위치에서 이만큼 아래부터 배치
GOAL_PULSE = 4.0          # 목표 키워드가 반짝이는 빠르기
SHORT_MSG_TIME = 1.5      # '크롤링이 부족합니다' 글이 떠 있는 시간 (초)
SHORT_MSG_RISE = 30       # 그동안 위로 떠오르는 거리 (px)
CLEAR_DELAY = 0.6         # 키워드를 먹고 탈출 창이 열리기까지 (그동안 금색 원이 퍼지고 크롤러는 계속 걸음)
DEATH_ZOOM = 2.4          # 다리를 모두 잃으면 머리를 중심으로 이만큼까지 확대 (LOST_DELAY 동안)
DEATH_TINT = 0.35         # 확대되는 동안 화면이 붉게 어두워지는 정도 (최대)
DEATH_STOP = 0.2          # 마지막 다리가 잘리는 순간 멈칫 (보통 피격보다 김)
# 죽음 = 데이터 유출 → 프로그램이 뻗음 (머리 하나로도 성립하는 연출)
DIE_SPILL_TIME = 1.6      # 데스 1: 머리에서 데이터 조각이 쏟아지는 시간 (초) — 띠의 DATA가 0으로 줄어듦
DIE_SPILL_MIN, DIE_SPILL_MAX = 14, 60     # 쏟아지는 조각 수 = DATA × 3 (이 범위로)
DIE_GLITCH = 1.4          # 데스 2: 머리 글리치(색 어긋남·끊김) 시작 (초), 눈이 ×
DIE_GLITCH_SHIFT = 4      # 글리치 잔상이 어긋나는 거리 (px)
DIE_FREEZE = 2.2          # 데스 3: '응답 없음' — 화면이 하얗게 굳고 모든 움직임이 멈춤 (초)
DIE_FREEZE_WHITE = 0.35   # 굳은 화면의 하얀 덮개 진하기
BIT_SPEED = 150           # 데이터 조각이 튀는 속도 (px/s)
BIT_LIFE = 1.1            # 조각 수명 (초)
LOST_DIALOG_TIME = 1.0    # 죽음: 오류 대화상자가 떠서 '보고서 작성' 막대가 차는 시간 (초)
LOST_OPEN_TIME = 1.35     # 대화상자 + 티어링까지 합친 시간 — 끝나면 곧바로 crawl://lost (커지는 창 없음)
TEAR_STRIPS = 22          # 티어링: 화면을 가로 띠 몇 개로 가를지
TEAR_PX = 140             # 티어링 최대 어긋남 (px) — 갈수록 커짐
ERR_W, ERR_H = 380, 150   # 오류 대화상자 크기
ERR_TITLE_H = 26          # 대화상자 제목 줄 높이
REPORT_X = 150            # 오류 보고서 페이지: 글 왼쪽 x
REPORT_TOP = 110          # 첫 줄 위치: 맨 위에서 이만큼 아래
REPORT_LINE = 34          # 줄 간격
REPORT_LABEL_W = 90       # 항목 이름 칸 폭
REPORT_TYPE = 0.18        # 줄이 하나씩 나타나는 간격 (초)
LOST_DELAY = 3.0          # 다리를 모두 잃고 crawl://lost 창이 열리기까지 (초) — 그동안 버둥거림
CLEAR_FX_R = 70           # 키워드 자리에서 퍼지는 금색 원 크기

# ── 크롤러 브라우저 자체 페이지 crawl://… (PRD 12) ──
CRAWL_SPAWN_FROM_TOP = 70 # 크롤러가 나타나는 곳: 페이지 맨 위에서 이만큼 아래
CRAWL_TEXT_TOP = 170      # 첫 글줄 위치: 맨 위에서 이만큼 아래
CRAWL_LINE_GAP = 22       # 글줄 사이 간격
CRAWL_GRID = 32           # 바탕 점 격자 간격
CRAWL_SLOT_W, CRAWL_SLOT_H = 260, 64   # 칸 크기
CRAWL_SLOT_GAP = 40       # 칸 사이 간격
CRAWL_SLOT_Y = 150        # 칸 아래 y (페이지 아래쪽)

# ── 페이지 출구 = 다음 문서 상자 (PRD 11.3-3) ──
EXIT_ROWS, EXIT_COLS = 1, 5   # 칸 배치: 한 줄 5칸 (방문 대기열 4 + 뒤로). 두 줄이면 아래 칸에 가다 위 칸을 밟게 됨
EXIT_SLOT_H = 48          # 칸 높이 — 링크 단어보다 커서 판정 여유 없이 칸 안에 착지해야 이동
EXIT_GAP = 12             # 칸 사이 간격
EXIT_PAD = 14             # 상자 안쪽 여백
EXIT_TITLE_H = 30         # 상자 제목('다음 문서') 줄 높이
EXIT_DASH = 8             # 잠긴 상자 점선 한 토막 길이
EXIT_PULSE = 3.0          # 열린 상자 테두리가 깜빡이는 빠르기 (초당 라디안 배수)
CHEW_STEPS = 4            # 먹은 링크 껍데기를 이만큼 연속으로 디디면 구멍이 뚫려 그 문서로 떨어진다
CHEW_FORGET = 1.0         # 이 시간 동안 안 디디면 갉던 구멍이 다시 메워짐 (초)
CHEW_MARGIN = 8           # 껍데기 상자 바깥으로 이만큼까지 디뎌도 갉음 (px)
CHEW_UNLOCK = 1.2         # 링크를 필요한 만큼 먹고 나서 껍데기를 갉을 수 있게 되기까지 (초) — 먹자마자 떠나지 않게
CHEW_FRESH = 1.2          # 막 먹은 링크는 이 시간이 지나야 갉을 수 있음 (초)
CHEW_REVEAL = 0.5         # 갉을 수 있게 될 때 껍데기 점선이 차례로 나타나는 시간 (초)
HOLE_BIG = 150            # 이보다 큰 구멍(화면으로 번질 때)은 단순하게 그림 (느려지지 않게)
HOLE_BIG_BITS = 120       # 큰 구멍 속 0·1 개수
LEAK_LIFE = 0.9           # 구멍에서 새어 나오는 0·1 조각 수명 (초)
LEAK_RATE = 0.05          # 구멍이 있는 동안 0·1이 새어 나오는 간격 (초)
PLANK_STRETCH = 1.5       # 구멍을 가로로 이만큼 길게 (판자는 가로로 부러지니까)
PLANK_H = 8               # 구멍을 부러진 판자 줄로 그릴 때 한 줄 높이 (px)
CHEW_JOLT = 0.18          # 한 번 갉을 때마다 구멍·화면이 흔들리는 시간 (초)
CHEW_JOLT_AMP = 3         # 그때 구멍이 흔들리는 폭 (px)
CHEW_BURST = 6            # 한 번 갉을 때 확 튀어 나오는 0·1 개수
CHEW_HOLE_R = 26          # 다 갉았을 때 구멍 반지름 (px)
HOLE_TIME = 0.55          # 구멍이 화면 전체로 번지며 빨려 들어가는 시간 (초)
DROP_HEIGHT = 150         # 새 문서에 위에서 떨어져 들어오는 높이 (px)
DROP_GRAVITY = 1400       # 떨어지는 가속도 (px/s²)
ARRIVE_HOLE_TIME = 0.8    # 새 문서에 뚫린 도착 구멍이 메워지는 시간 (초)
BACK_SPOT = (24, 150, 190, 22)   # '← 뒤로' 껍데기 자리: 왼쪽 x, 페이지 맨 위에서 아래로, 폭, 높이
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
BOX_MAX_SEGS = 6          # 최대 마디 수 (다리 12) — 여기서 더 자라지 않음
PART_LOCKED_ALPHA = 0.3   # 최대일 때 다리 파츠 진하기 (주울 수 없다는 표시)
BOX_SEG_SIZE = 14         # 몸통 마디 한 변
BOX_HEAD_SIZE = 16        # 머리 한 변
BOX_EYE_SIZE = 4          # 머리 앞쪽 주황 점 한 변
EYE_CLOSED_THICK = 1.5    # 감은 눈(WAVE 착지 경직) 선 두께
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
# ── □ WAVE 점프 돌진 파동 (PRD 6.1.3) ──
WAVE_STEP = 0.05          # 다음 마디가 뛰기까지 간격 (초) — 마디 i는 i × 0.05초에 뜀
WAVE_HOLD = 0.55          # 마디 하나가 공중에 있는 시간 = 무적 시간 (초) — 지름 32px 위험 지점을 뛰어넘을 수 있게
WAVE_DASH = 160           # 머리가 점프로 날아가는 거리 (px) — 공중 시간(WAVE_HOLD) 동안
WAVE_JUMP_H = 18          # 점프 최고 높이 (px) — 공중 시간 동안 포물선(sin)으로 올라갔다 내려옴
WAVE_LEG_TUCK = 0.45      # 공중 다리: 어깨~발 거리를 이 비율로 접어 올림
WAVE_FOOT_LIFT = 0.6      # 공중 다리: 발 높이 = 마디가 뜬 높이 × 이 값 (발이 몸보다 조금 아래에 매달림)
WAVE_STRETCH = 1.6        # 파동 중 마디 간격이 늘어날 수 있는 최대 배율 (19 × 1.6 ≈ 30px)
WAVE_RESTORE = 600        # 늘어난 간격이 줄어드는 속도 (px/s) — 공중 마디가 따라붙을 때, 파동이 끝난 뒤
WAVE_LINK_ALPHA = 0.35    # 늘어난 마디 사이 연결선 진하기 (가늘고 흐리게)
WAVE_STUN_BASE = 0.1      # 머리 착지 뒤 경직 (초) — 바라보던 방향 그대로 뛰었을 때
WAVE_STUN_TURN = 0.7      # 꺾은 각도에 비례해 더하는 경직: 180°로 뒤돌아 뛰면 +0.7초 (방향 바꾸기용으로 쓰는 대가)
WAVE_STRETCH_AIR = 0.35   # 공중 마디가 나는 방향으로 길쭉해지는 정도: 길이 × (1 + 이 값), 폭은 그만큼 줄어 넓이 유지
WAVE_SQUASH = 0.2         # 착지 순간 납작해지는 정도: 길이 × (1 − 이 값), 폭 × 1/(1 − 이 값)
WAVE_SQUASH_TIME = 0.12   # 납작해졌다 정사각형으로 돌아오는 시간 (초)
WAVE_LAND_KICK = 40       # WAVE 착지 반동 (발 하나당, 걷기 착지 LAND_KICK보다 세게)
WAVE_GHOST = 0.3          # 공중(무적) 마디의 진하기 배율 — 반투명해져 아래가 비침
WAVE_COOLDOWN = 1.5       # 파동이 꼬리까지 끝난 뒤 다시 쓸 수 있을 때까지 (초)
GHOST_INTERVAL = 0.05     # 잔상 남기는 간격 (초)
GHOST_LIFE = 0.2          # 잔상이 사라지는 시간
GHOST_ALPHA = 0.3         # 잔상 진하기
GHOST_MIN_SPRINT = 0.5    # 질주 정도가 이 이상일 때만 잔상
PUFF_LIFE = 0.35          # 흙먼지가 사라지는 시간
PUFF_SPREAD = 9           # 흙먼지가 퍼지는 거리 (px)
PUFF_ALPHA = 0.6          # 흙먼지 진하기
CUT_LIFE = 1.3            # 잘린 다리가 날아가 바닥에서 꼼지락거리다 사라지는 시간 (초)
CUT_FLY_SPEED = 170       # 잘린 다리가 위험 지점 반대쪽으로 튕겨 나가는 속도 (px/s)
CUT_FLY_UP = 150          # 위로 튀어 오르는 속도 (px/s, 높이 방향)
CUT_GRAVITY = 900         # 잘린 다리를 끌어내리는 중력 (px/s²)
CUT_SPIN = 14             # 날아가는 동안 도는 빠르기 (rad/s, 방향은 무작위)
CUT_GROUND_FRICTION = 6   # 바닥에 떨어진 뒤 미끄러짐이 멈추는 빠르기
SPARK_COUNT = 7           # 잘린 자리에서 튀는 불꽃 수
SPARK_SPEED = 260         # 불꽃 속도 (px/s)
SPARK_LIFE = 0.22         # 불꽃 수명 (초)
SPARK_LEN = 0.035         # 불꽃 선 길이 = 속도 × 이 값 (빠를수록 긴 꼬리)
HIT_STOP = 0.07           # 잘리는 순간 게임이 멈칫하는 시간 (초) — 타격감
SHAKE_TIME = 0.25         # 화면 흔들림 시간 (초)
SHAKE_AMP = 6             # 화면 흔들림 폭 (px, 갈수록 잦아듦)
SHAKE_FREQ = 55           # 화면 흔들림 빠르기
HIT_FLASH = 0.15          # 맞은 마디가 빨갛게 번쩍이는 시간 (초)
# ── 다리 불균형 (한쪽 다리를 잃었을 때의 불편함) ──
LIMB_DRIFT = 0.4          # A 끌려감: 좌우 다리 수가 완전히 한쪽뿐이면 머리가 초당 이만큼(rad) 없는 쪽으로 돈다 (움직일 때)
LIMB_TURN_BIAS = 0.5      # A: 없는 쪽으로 도는 건 ×(1 + 이 값×불균형), 반대쪽은 ×(1 − 이 값×불균형)
STAGGER_KICK = 8          # 비틀거림: 짝 없는 다리가 디딜 때 머리가 없는 쪽으로 휘청 꺾이는 회전 속도 (rad/s × 불균형)
STAGGER_DECAY = 13        # 휘청 회전이 사라지는 빠르기 (클수록 짧게) → 꺾이는 각 ≈ KICK / DECAY ≈ 0.6rad(35°)
STAGGER_MIN = 0.4         # 비틀거림 세기 = STAGGER_MIN + (1 − STAGGER_MIN) × 불균형 (다리 하나만 잃어도 휘청)
STAGGER_GAP = 0.5         # 휘청임 사이 최소 간격 (초) — 너무 잦으면 떨림처럼 보임
STAGGER_SLOW = 0.4        # 휘청이는 동안 속도 ×(1 − 이 값 × 휘청 정도)
LEAN_PX = 3               # B 기울어짐: 한쪽 다리만 남은 마디가 없는 쪽으로 쏠리는 거리 (px)
LEAN_DROP = 3             # B: 그 마디가 낮게 처지는 높이 (px)
LIMP_STEP = 1.3           # C 절뚝임: 짝이 없는 다리의 걸음 시간 배율
LIMP_DIP = 4              # C: 짝 없는 다리를 뗄 때 마디가 푹 꺼지는 깊이 (px)
LIMP_SLOW = 0.25          # C: 그 동안 속도 ×(1 − 이 값)
DRAG_H = 1.5              # D 끌림: 다리가 하나도 없는 마디의 높이 (거의 바닥)
DRAG_SLOW = 0.15          # D: 끌리는 마디 하나당 속도 ×(1 − 이 값)
DROP_DELAY = 0.8          # 다리를 모두 잃은 마디가 끌리다 떨어져 나가기까지 (초) — 머리는 탈락 안 함 (PRD 5.4)
DROP_LIFE = 1.0           # 떨어진 마디가 바닥에서 흐려지며 사라지는 시간 (초)
DROP_SPIN = 2.5           # 떨어진 마디가 도는 빠르기 (rad/s, 점점 멈춤)
DRAG_DUST = 0.09          # D: 끌리는 마디가 움직일 때 먼지 간격 (초)
BODY_HIT_LEGS = 2         # 몸통(마디)에 맞으면 잃는 다리 수 — 꼬리 쪽 마디부터
LEG_SPEED_TABLE = ((2, 0.6), (5, 0.85), (8, 1.0), (12, 1.1))   # 다리 수 ≤ 앞 값이면 속도 × 뒤 값 (PRD 5.4)
HIT_IFRAME = 1.0          # 피격 후 무적 시간 (초) — 이 동안 다시 안 맞음 (PRD 5.4)
HIT_BLINK = 0.08          # 무적 중 깜빡임 간격 (초) — 흐려졌다 돌아옴 (사라지지는 않음)
HIT_BLINK_ALPHA = 0.3     # 깜빡일 때 진하기
HIT_POP = 90              # 맞으면 몸이 순간 들썩이는 세기 (몸 높이 속도에 더함)
CUT_FADE = 0.3            # 그중 마지막 이만큼 흐려짐
CUT_WIGGLE = 18           # 잘린 다리 꼼지락 빠르기
CUT_WIGGLE_AMP = 4        # 꼼지락 폭 (px) — 시간이 갈수록 잦아듦
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
