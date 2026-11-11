# CRAWL.EXE — Claude 작업 지침

웹페이지 속 크롤러가 되어 **발로 밟아** 데이터를 모으는 2D 탑다운 액션 게임.
Python 3 + pico2d, 1인 개발, 4주. 상세 명세는 `docs/PRD.md`, 커밋 단위 계획은 `docs/COMMITS.md` — 작업 전에 해당 절을 읽을 것.

## 실행
```
pip install pico2d
python main.py
```
- `F1` 디버그 뷰(발 목표 원, 판정 범위, 무적 표시) 토글
- `F12` (타이틀 화면) 모든 크롤러·스테이지 임시 해금, 저장 안 함

## 폴더
```
main.py              창 1280×720 열고 game_framework 실행
game_framework.py    씬 전환 (수업 프레임워크)
config.py            모든 수치 상수 (PRD의 '초기값'은 전부 여기)
modes/               title · select · play · result 씬
crawler/             leg.py · body.py · crawler.py · box.py · tri.py · orb.py
world/               camera.py · stage.py · objects.py · enemies.py · collision.py
ui/                  hud.py · debug_view.py · draw.py(선·원 그리기)
data/stages/*.json   스테이지 배치 (스키마: PRD 11장)
assets/              이미지 · 사운드
```

## 좌표와 단위 — 반드시 지킬 것
- pico2d 좌표계: 원점 왼쪽 아래, **y는 위로 증가**.
- **월드 좌표**(페이지 위 위치)와 **화면 좌표**를 구분한다. 화면 y = 월드 y − `camera.y`. 게임 로직은 전부 월드 좌표, 그리기 직전에만 변환.
- 마우스 이벤트 y는 위가 0이다 → `screen_y = 720 - 1 - event.y`, 그다음 `world_y = screen_y + camera.y`.
- 길이 px, 시간 초, 각도 라디안. 이동은 항상 `game_framework.frame_time`을 곱한다.
- 수치를 코드에 직접 쓰지 말고 `config.py` 상수로 둔다.

## pico2d에서 주의할 점
- 선 그리기 함수가 없다. `ui/draw.py`의 `draw_line(x1, y1, x2, y2, width, color)`을 쓴다(1×1 흰 픽셀 이미지를 늘리고 회전해 `composite_draw`로 그림). 흰 픽셀 하나에 그릴 때 색을 입힌다(`SDL_SetTextureColorMod`), 투명도는 `opacify`.
- 이미지는 `load_image`를 `open_canvas()` 뒤에 한 번만(모듈마다 `load()` 함수를 두고 main에서 호출). 매 프레임 로드 금지.

## 협업 규칙 (AI 협업이 과제의 핵심)
1. **요청 하나 = 커밋 하나.** `docs/COMMITS.md`의 번호(예: S04-2) 단위로 일한다. 그 커밋 범위 밖 파일은 건드리지 않는다. 커밋마다 게임이 실행되는 상태를 유지하고, 끝나면 그 행의 메시지 형식으로 커밋 메시지를 제안한다.
2. 새 시스템(IK, WAVE, 판정 등)은 코드 작성 전에 **계획을 먼저 짧게 제시**하고 확인받는다.
3. 학생이 읽고 설명할 수 있는 코드로: 과한 추상화·메타프로그래밍·불필요한 클래스 계층 금지. 핵심 수식 옆에는 한 줄 주석.
4. 새 라이브러리 추가 전에 묻는다. 기본은 pico2d + 표준 라이브러리만.
5. 작업이 끝나면 (a) 직접 실행해서 확인할 방법(무엇을 보면 되는지), (b) `AI_LOG.md`에 붙일 항목 초안을 함께 준다.
6. PRD와 다르게 구현해야 할 이유가 생기면 구현 전에 말한다. 결정이 바뀌면 PRD 20장(결정 기록)에 한 줄 추가.

## 완료 판단
테스트 코드보다 **플레이로 확인**한다. 각 슬라이스의 완료 기준(PRD 17장)을 디버그 뷰를 켜고 직접 확인할 수 있어야 한다.
