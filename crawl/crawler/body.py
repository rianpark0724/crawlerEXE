# □ 사각형 크롤러의 몸 — 머리(segs[0])만 입력으로 움직이고 나머지 마디는 끌려온다 (PRD 5.1, 6.1)
# 좌표는 전부 월드 좌표. 그릴 때만 camera.to_screen으로 바꾼다.
import math
import random

import config
from crawler.leg import Leg
from crawler.effects import Effects
from ui.draw import fill_rect_rotated, draw_line


class Segment:
    # 마디 하나: 중심 위치와 바라보는 방향
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.angle = angle      # 라디안. 앞(머리 쪽)을 향함
        self.vx = self.vy = 0.0  # 이번 프레임 이동 속도 (px/s) — 다리가 앞으로 미리 딛는 데 사용
        self.ox = self.oy = 0.0  # 좌우 쏠림 (디딘 다리 쪽으로). 그리기와 어깨 위치에 더한다
        self.squash = 0.0        # WAVE 착지 후 납작함이 남은 시간
        self.flash = 0.0         # 피격 후 빨갛게 번쩍임이 남은 시간
        self.legs = [Leg(+1), Leg(-1)]   # 다리 한 쌍 (왼쪽, 오른쪽)
        self.legs[0].partner, self.legs[1].partner = self.legs[1], self.legs[0]   # 서로 반대쪽 다리


class Body:
    def __init__(self, x, y, seg_count=config.BOX_START_SEGS):
        # 머리는 아래(-π/2)를 보고, 나머지 마디는 그 위쪽에 SEG_SPACING 간격으로 줄지어 시작
        # seg_count: 마디 수 (문서를 옮겨도 자란 몸을 유지하려고 play_mode가 넘김)
        self.segs = [Segment(x, y + i * config.SEG_SPACING, -math.pi / 2) for i in range(seg_count)]
        self.speed = 0.0                             # 이번 프레임 머리 속도 (디버그 표시용)
        self.sprint = False                          # 좌클릭 질주 중인지 (누르고 있는지)
        self.sprint_k = 1.0                          # 실제 질주 배율 1 → SPRINT_SPEED. 바로 바뀌지 않고 따라감 (관성)
        self.height = config.BODY_HEIGHT             # 몸 높이 — 착지할 때마다 눌렸다 튀어 오름 (용수철)
        self.height_v = 0.0                          # 몸 높이 변화 속도
        self.effects = Effects()                     # 질주 잔상·흙먼지
        self.on_land = None                          # 발이 착지할 때 부를 함수 on_land(leg) — 수집 판정 (play_mode가 연결)
        self.wave_t = None                           # □ WAVE: 파동이 시작된 뒤 지난 시간 (None = 파동 중 아님)
        self.wave_cool = 0.0                         # WAVE 재사용까지 남은 시간
        self.wave_dir = 0.0                          # 점프 돌진 방향 (출발할 때 커서 쪽으로 고정)
        self.wave_stun = 0.0                         # 이번 점프의 착지 경직 시간 (꺾은 각도로 정함)
        self.stun = 0.0                              # 남은 경직 시간 — 머리가 움직이지도 돌지도 않음
        self.dust_timer = 0.0                        # 다리 없이 끌리는 마디의 다음 먼지까지 남은 시간
        self.stagger_v = 0.0                         # 비틀거림: 지금 머리를 꺾고 있는 회전 속도 (rad/s, 점점 사라짐)
        self.stagger_gap = 0.0                       # 다음 휘청임까지 남은 최소 시간
        self.gaps = [config.SEG_SPACING] * len(self.segs)   # 마디 i와 앞 마디 사이 간격 (평소 19, WAVE 중 늘어남). gaps[0]은 안 씀
        self.update_legs(0.0)                        # 발을 처음 위치에 놓는다

    def all_legs(self):
        return [leg for seg in self.segs for leg in seg.legs]

    def seg_size(self, i):
        return config.BOX_HEAD_SIZE if i == 0 else config.BOX_SEG_SIZE

    def place(self, x, y):
        # 문서를 옮길 때: 몸을 (x, y)에 다시 세운다 — 마디 수·남은 다리는 그대로 (잃은 다리를 문서 간에 유지)
        for i, seg in enumerate(self.segs):
            seg.x, seg.y, seg.angle = x, y + i * config.SEG_SPACING, -math.pi / 2
            seg.vx = seg.vy = 0.0
            seg.squash = 0.0
            for leg in seg.legs:
                leg.placed = False                      # 다음 자세 계산 때 발을 이상적 위치에 바로 놓음
                leg.stepping = leg.in_air = leg.landed = leg.from_air = False
                leg.lift = 0.0
        self.gaps = [config.SEG_SPACING] * len(self.segs)
        self.speed, self.height, self.height_v = 0.0, config.BODY_HEIGHT, 0.0
        self.wave_t, self.stun = None, 0.0
        self.effects = Effects()
        self.update_legs(0.0)

    def cut_leg(self, leg, from_x, from_y):
        # 다리 하나 잘림 (PRD 5.4): 몸에서 떼고, (from_x, from_y)(위험 지점) 반대쪽으로 튕겨 날아가게.
        # 맞은 마디는 빨갛게 번쩍이고 몸이 순간 들썩인다
        for seg in self.segs:
            if leg in seg.legs:
                seg.legs.remove(leg)
                seg.flash = config.HIT_FLASH
                for other in seg.legs:
                    other.partner = None                # 짝이 없어졌으니 혼자 걷는다
        self.height_v += config.HIT_POP
        self.effects.add_cut(leg, leg.knee_x - from_x, leg.knee_y - from_y)

    def imbalance(self):
        # 좌우 다리 수 차이 −1 ~ +1: +면 왼쪽(+side) 다리가 더 많음 → 오른쪽(없는 쪽)으로 끌려감
        left = sum(1 for leg in self.all_legs() if leg.side > 0)
        right = sum(1 for leg in self.all_legs() if leg.side < 0)
        return (left - right) / max(1, left + right)

    def sag(self, i):
        # 마디 i가 처지는 높이 (B 기울어짐 + C 절뚝임 + D 끌림)
        legs = self.segs[i].legs
        if not legs:
            return self.height - config.DRAG_H                    # D: 다리가 없으면 바닥에 끌림
        if len(legs) == 1:
            leg = legs[0]
            dip = config.LIMP_DIP * math.sin(math.pi * leg.t) if leg.stepping else 0.0   # C: 혼자 버티는 다리를 떼면 푹
            return config.LEAN_DROP + dip                             # B: 한쪽만 남으면 처짐
        return 0.0

    def seg_h(self, i):
        # 마디 i의 지금 높이 = 몸 높이(반동) + 점프 − 처짐
        return self.height + self.air(i) - self.sag(i)

    def can_grow(self):
        # 마디가 최대(6)보다 적어야 다리 파츠를 주울 수 있다
        return len(self.segs) < config.BOX_MAX_SEGS

    def grow(self):
        # 다리 파츠: 꼬리 뒤에 마디 1 + 다리 2를 붙인다 (PRD 6.1.2)
        tail = self.segs[-1]
        back = tail.angle + math.pi                      # 꼬리가 바라보는 반대쪽 = 몸 뒤쪽
        seg = Segment(tail.x + math.cos(back) * config.SEG_SPACING, tail.y + math.sin(back) * config.SEG_SPACING, tail.angle)
        seg.squash = config.GROW_POP                     # 붙는 순간 납작했다 펴짐 (WAVE 착지와 같은 모양 변형)
        self.segs.append(seg)
        self.gaps.append(config.SEG_SPACING)
        self.update_legs(0.0)                            # 새 다리 두 개를 바로 바닥에 놓는다

    def wave_length(self):
        # 파동 전체 시간: 마지막 마디가 굳기 시작하는 시각 + 무적 시간
        return (len(self.segs) - 1) * config.WAVE_STEP + config.WAVE_HOLD

    def invincible(self, i):
        # 마디 i가 지금 공중(=무적)인지: 파동 시작 후 [i × STEP, i × STEP + HOLD] 초 사이 (머리 i = 0부터 차례로)
        if self.wave_t is None:
            return False
        start = i * config.WAVE_STEP
        return start <= self.wave_t < start + config.WAVE_HOLD

    def air(self, i):
        # 마디 i가 공중에 뜬 높이: 공중 시간 동안 포물선 sin(π × 진행)으로 0 → WAVE_JUMP_H → 0
        if not self.invincible(i):
            return 0.0
        u = (self.wave_t - i * config.WAVE_STEP) / config.WAVE_HOLD
        return config.WAVE_JUMP_H * math.sin(math.pi * u)

    def shape(self, i):
        # 마디 i의 (길이 배율, 폭 배율) — 길이는 바라보는 방향. 넓이(길이×폭)는 1로 유지해 쫀득하게
        if self.invincible(i):
            u = (self.wave_t - i * config.WAVE_STEP) / config.WAVE_HOLD
            along = 1 + config.WAVE_STRETCH_AIR * math.sin(math.pi * u)        # 공중: 나는 방향으로 길쭉
        elif self.segs[i].squash > 0:
            along = 1 - config.WAVE_SQUASH * min(1.0, self.segs[i].squash / config.WAVE_SQUASH_TIME)   # 착지·새 마디: 납작했다 돌아옴
        else:
            return 1.0, 1.0
        return along, 1 / along

    def start_wave(self, target_x, target_y):
        # 우클릭: 파동 중이 아니고 재사용 대기가 끝났으면 커서 쪽으로 점프 돌진 시작. 시작했으면 True
        if self.wave_t is not None or self.wave_cool > 0:
            return False
        head = self.segs[0]
        self.wave_t = 0.0
        self.wave_dir = math.atan2(target_y - head.y, target_x - head.x)   # 방향은 여기서 고정 (공중에서 못 바꿈)
        # 바라보던 방향에서 꺾은 각도(0 ~ π)가 클수록 착지 경직이 길다 → 뒤돌기용으로 쓰면 손해
        turn = abs((self.wave_dir - head.angle + math.pi) % (2 * math.pi) - math.pi)
        self.wave_stun = config.WAVE_STUN_BASE + config.WAVE_STUN_TURN * turn / math.pi
        return True

    def dash_head(self, dt):
        # 머리 점프: 공중 시간 동안 WAVE_DASH만큼, 처음이 가장 빠르고 끝으로 갈수록 느려짐
        # 속도 = 2 × 거리 / 시간 × (1 − 진행)  → 0~1 구간을 적분하면 정확히 거리만큼 이동
        u = self.wave_t / config.WAVE_HOLD
        speed = 2 * config.WAVE_DASH / config.WAVE_HOLD * (1 - u)
        head = self.segs[0]
        head.angle = self.wave_dir
        head.x += math.cos(self.wave_dir) * speed * dt
        head.y += math.sin(self.wave_dir) * speed * dt
        self.speed = speed

    def update_wave(self, dt):
        # 파동 시간 진행, 끝나면 재사용 대기 시작. 머리가 착지하는 순간 경직 시작
        self.stun = max(0.0, self.stun - dt)
        for seg in self.segs:
            seg.squash = max(0.0, seg.squash - dt)
            seg.flash = max(0.0, seg.flash - dt)
        if self.wave_t is not None:
            before = self.wave_t
            self.wave_t += dt
            if before < config.WAVE_HOLD <= self.wave_t:
                self.stun = self.wave_stun                                     # 머리 착지 → 경직
            for i, seg in enumerate(self.segs):
                land = i * config.WAVE_STEP + config.WAVE_HOLD                 # 마디 i가 내려앉는 시각
                if before < land <= self.wave_t:
                    seg.squash = config.WAVE_SQUASH_TIME                       # 착지 → 납작
            if self.wave_t >= self.wave_length():
                self.wave_t = None
                self.wave_cool = config.WAVE_COOLDOWN
        else:
            self.wave_cool = max(0.0, self.wave_cool - dt)

    def sprint_frac(self):
        # 질주 정도 0(걷기) ~ 1(최고 속도 질주)
        return (self.sprint_k - 1) / (config.SPRINT_SPEED - 1)

    def update(self, target_x, target_y, dt, sprint=False):
        self.sprint = sprint
        # 관성: 질주 배율이 목표로 따라간다. 누를 땐 빠르게(ACCEL), 뗄 땐 천천히(DECEL) → 떼도 한동안 밀려감
        goal = config.SPRINT_SPEED if sprint else 1.0
        rate = config.SPRINT_ACCEL if goal > self.sprint_k else config.SPRINT_DECEL
        self.sprint_k += (goal - self.sprint_k) * min(1, rate * dt)
        self.update_wave(dt)
        before = [(seg.x, seg.y) for seg in self.segs]
        if self.invincible(0):
            self.dash_head(dt)                   # 1~2. WAVE: 머리가 공중에 있는 동안은 점프 돌진 (조종 불가)
        elif self.stun > 0:
            self.speed = 0.0                     # 1~2. WAVE 착지 경직: 움직이지도 돌지도 않음
        else:
            self.move_head(target_x, target_y, dt)   # 1~2. 머리 회전·전진
        self.follow(dt)                          # 3. 나머지 마디는 앞 마디에 끌려온다 (거리 제약)
        for seg, (px, py) in zip(self.segs, before):
            if dt > 0:
                seg.vx, seg.vy = (seg.x - px) / dt, (seg.y - py) / dt   # 마디 속도 = 이번 프레임 이동량 / 시간
        self.update_legs(dt)                     # 4. 다리
        self.drag_dust(dt)                       # D: 다리 없이 끌리는 마디의 먼지
        self.update_height(dt)                   # 5. 착지 반동 (+ 질주 중 착지 흙먼지)
        self.effects.update(dt, self)            # 6. 효과

    def drag_dust(self, dt):
        # D: 다리가 하나도 없는 마디가 움직이면 바닥을 긁으며 먼지가 난다
        self.dust_timer -= dt
        if self.dust_timer > 0:
            return
        self.dust_timer = config.DRAG_DUST
        for seg in self.segs:
            if not seg.legs and math.hypot(seg.vx, seg.vy) > 20:
                self.effects.add_puff(seg.x, seg.y)

    def update_height(self, dt):
        self.stagger_gap -= dt
        # 이번 프레임에 착지한 발: 착지 이벤트를 알리고, 그 수만큼 몸을 아래로 툭 친다 (질주 중엔 더 세게)
        landed = 0
        for leg in self.all_legs():
            if leg.landed:
                landed += 1
                leg.landed = False
                if self.on_land is not None:
                    self.on_land(leg)                                     # 착지 이벤트 (PRD 5.3: 착지하는 순간 한 번)
                if leg.partner is None and self.stagger_gap <= 0 and self.wave_t is None:
                    # 비틀거림: 혼자 버티던 다리가 디디는 순간 몸이 다리 없는 쪽으로 휘청 (왼쪽 다리면 오른쪽으로 = 각도 −)
                    # 세기 = 0.4 + 0.6 × 불균형: 다리 하나만 잃어도 휘청이고, 한쪽을 다 잃으면 가장 크게
                    strength = config.STAGGER_MIN + (1 - config.STAGGER_MIN) * abs(self.imbalance())
                    self.stagger_v = -leg.side * config.STAGGER_KICK * strength * random.uniform(0.7, 1.2)
                    self.stagger_gap = config.STAGGER_GAP * random.uniform(1.0, 1.6)
                if leg.from_air:
                    leg.from_air = False
                    self.effects.add_puff(leg.foot_x, leg.foot_y)        # WAVE 점프 착지 → 흙먼지
                    self.height_v -= config.WAVE_LAND_KICK - config.LAND_KICK   # 더 세게 툭 (아래에서 LAND_KICK을 더함)
                elif self.sprint_frac() > config.PUFF_MIN_SPRINT:
                    self.effects.add_puff(leg.foot_x, leg.foot_y)        # 질주 중 착지 → 흙먼지
        kick = config.LAND_KICK * (1 + (config.SPRINT_LAND_KICK - 1) * self.sprint_frac())
        self.height_v -= kick * landed
        # 용수철: 원래 높이로 당기는 힘 − 흔들림을 줄이는 힘 → 눌렸다가 살짝 튀어 오른 뒤 가라앉음
        rest = config.BODY_HEIGHT - config.SPRINT_CROUCH * self.sprint_frac()   # 질주 중엔 몸을 낮춤 (웅크린 자세)
        acc = -config.BODY_SPRING * (self.height - rest) - config.BODY_DAMP * self.height_v
        self.height_v += acc * dt
        self.height += self.height_v * dt
        lo, hi = config.BODY_HEIGHT - config.BODY_BOUNCE_MAX, config.BODY_HEIGHT + config.BODY_BOUNCE_MAX
        self.height = max(lo, min(hi, self.height))

    def move_head(self, target_x, target_y, dt):
        head = self.segs[0]
        dist = math.hypot(target_x - head.x, target_y - head.y)    # 커서까지 거리
        want_speed = 0.0                                            # 이번 프레임에 내고 싶은 속도
        if dist >= config.BOX_STOP_DIST:                            # 커서 위에 도착하면 회전하지 않음 (가까우면 방향이 흔들려 떨기 때문)
            # 1. 커서 쪽으로 회전 — 초당 BOX_TURN_SPEED rad 까지만, 질주 중엔 둔해짐 (대가)
            want = math.atan2(target_y - head.y, target_x - head.x)     # 커서 방향
            diff = (want - head.angle + math.pi) % (2 * math.pi) - math.pi   # 돌아야 할 양 (-π ~ π)
            max_turn = config.BOX_TURN_SPEED * (1 - config.SPRINT_TURN_LOSS * self.sprint_frac()) * dt
            # A: 다리 불균형 — 없는 쪽(오른쪽이면 각도 −)으로 도는 건 쉽고, 반대쪽은 어렵다
            imb = self.imbalance()
            toward_missing = (diff < 0) == (imb > 0)
            max_turn *= 1 + config.LIMB_TURN_BIAS * abs(imb) * (1 if toward_missing else -1)
            head.angle += max(-max_turn, min(max_turn, diff))
            head.angle = (head.angle + math.pi) % (2 * math.pi) - math.pi     # 각도를 -π ~ π 로 유지

            # 2. 내고 싶은 속도
            want_speed = config.BOX_BASE_SPEED + config.BOX_SPEED_PER_PAIR * (len(self.all_legs()) / 2)   # 120 + 8 × 다리 쌍
            want_speed = min(want_speed, dist * config.BOX_SLOW_FACTOR)        # 커서 가까이 가면 감속
            want_speed *= max(config.BOX_MIN_FACING, math.cos(diff))           # 커서와 다른 방향을 볼수록 느리게 (뒤돌 때 거의 제자리 회전)
            # 밀려가기: 들린 발이 적을수록(디딘 발이 많을수록) 빠르게. lifted 0 = 전부 디딤, 1 = 걸을 수 있는 다리가 모두 가장 높이
            legs = self.all_legs()
            lifted = sum(leg.lift for leg in legs) / (config.LEG_LIFT * max(1, len(legs) // 2))
            want_speed *= 1 + config.BODY_SURGE * (0.5 - lifted)               # 평균 속도는 그대로, ×(1 ± SURGE/2) 사이에서 출렁
            want_speed *= self.sprint_k                                        # 좌클릭 질주 (관성 있는 배율)
            # C: 짝 없는 다리가 걸음 중이면 절뚝이며 느려짐 / D: 다리 없이 끌리는 마디마다 느려짐
            if any(leg.partner is None and leg.stepping for leg in legs):
                want_speed *= 1 - config.LIMP_SLOW
            want_speed *= (1 - config.DRAG_SLOW) ** sum(1 for seg in self.segs if not seg.legs)

        # 3. 제동: 속도는 바로 올릴 수 있지만 줄일 때는 brake(px/s²)보다 빨리 못 줄인다.
        #    걸을 땐 브레이크가 세서 거의 바로 서고, 질주 중엔 약해서 커서를 지나쳐 미끄러진다 (대가)
        if want_speed >= self.speed:
            self.speed = want_speed
        else:
            brake = config.BRAKE_WALK + (config.BRAKE_SPRINT - config.BRAKE_WALK) * self.sprint_frac()
            self.speed = max(want_speed, self.speed - brake * dt)
        # A: 움직이는 동안 다리가 없는 쪽으로 계속 끌려 돈다 (커서로 계속 보정해야 똑바로 감)
        moving = min(1.0, self.speed / config.BOX_BASE_SPEED)
        head.angle -= config.LIMB_DRIFT * self.imbalance() * moving * dt
        # 비틀거림: 휘청 회전이 남아 있으면 그만큼 꺾이고 느려진다. 회전은 지수적으로 사라져 다시 커서 쪽으로
        head.angle += self.stagger_v * dt
        self.speed *= 1 - config.STAGGER_SLOW * min(1.0, abs(self.stagger_v) / config.STAGGER_KICK) * dt * 10
        self.stagger_v *= math.exp(-config.STAGGER_DECAY * dt)
        head.x += math.cos(head.angle) * self.speed * dt
        head.y += math.sin(head.angle) * self.speed * dt

    def update_legs(self, dt):
        # (1) 어깨·이상적 위치: 다리 기울기는 머리 마디 +LEG_TILT(앞) → 꼬리 마디 -LEG_TILT(뒤)로 고르게
        n = len(self.segs)
        for i, seg in enumerate(self.segs):
            # 좌우 쏠림: 한쪽 다리가 들리면 몸이 반대쪽(디딘 쪽)으로. 왼쪽(+) 다리가 들리면 오른쪽으로
            left = sum(leg.lift for leg in seg.legs if leg.side > 0)            # 다리를 잃었으면 그쪽은 0
            right = sum(leg.lift for leg in seg.legs if leg.side < 0)
            sway = config.BODY_SWAY * (right - left) / config.LEG_LIFT
            # B: 한쪽 다리만 남은 마디는 없는 쪽으로 쏠린다 (왼쪽만 남으면 오른쪽으로)
            if len(seg.legs) == 1:
                sway -= config.LEAN_PX * seg.legs[0].side
            seg.ox = math.cos(seg.angle + math.pi / 2) * sway
            seg.oy = math.sin(seg.angle + math.pi / 2) * sway
            tilt = config.LEG_TILT * (1 - 2 * i / (n - 1)) if n > 1 else 0.0
            sweep = config.SPRINT_SWEEP * self.sprint_frac()                      # 질주 중엔 다리를 뒤로 젖힘
            air = self.air(i)
            for leg in seg.legs:
                leg.stride = 1 + (config.SPRINT_STRIDE - 1) * self.sprint_frac()   # 질주: 보폭 커짐
                leg.air = air                                                     # WAVE 공중 높이 (뜬 마디의 다리는 접힘)
                leg.body_h = self.seg_h(i)                                        # 지금 마디 높이 (반동 + 점프 − 처짐)
                leg.lift_scale = 1 + config.SPRINT_LIFT * self.sprint_frac()      # 질주 중엔 발을 더 높이 차올림
                leg.update_pose(seg, self.seg_size(i), tilt - sweep, tilt)
        legs = self.all_legs()
        # (2) 걷는 중인 다리 진행 (착지·순간이동 처리)
        for leg in legs:
            leg.update_step(dt)
        # (3) 새 걸음 시작: 이상적 위치에서 가장 멀리 벗어난 다리부터.
        #     동시에 걷는 다리는 전체의 절반까지, 같은 마디 반대쪽 다리가 걷는 중이면 기다린다 (번갈아 걷기)
        stepping = sum(1 for leg in legs if leg.stepping)
        limit = max(1, len(legs) // 2)
        waiting = [leg for leg in legs if leg.air == 0 and leg.wants_step()]   # 공중 다리는 걷지 않음
        waiting.sort(key=lambda leg: (leg.overstretched(), leg.distance()), reverse=True)   # 다 펴진 다리가 가장 먼저
        for leg in waiting:
            if stepping >= limit:
                break
            if leg.partner is not None and leg.partner.stepping:
                continue
            leg.start_step()
            stepping += 1
        # (4) 무릎
        for leg in legs:
            leg.solve_knee()

    def follow(self, dt):
        # 머리에서 꼬리 순서로: 마디 i를 마디 i-1에서 정확히 gaps[i] 떨어진 곳으로 당긴다
        # gaps[i]는 평소 19px. WAVE 중에는:
        #   아직 뛰기 전인 마디 → 제자리에 버팀: 간격이 지금 거리만큼 늘어남 (최대 19 × 1.6)
        #   뛰어오른 마디 / 착지한 마디 / 파동이 끝난 뒤 → 앞 마디로 따라붙음: 간격이 초당 WAVE_RESTORE px씩 19까지 줄어듦
        base = config.SEG_SPACING
        while len(self.gaps) < len(self.segs):       # 마디가 늘어나면 (S07) 간격도 추가
            self.gaps.append(base)
        for i in range(1, len(self.segs)):
            front, seg = self.segs[i - 1], self.segs[i]
            dx, dy = front.x - seg.x, front.y - seg.y
            d = math.hypot(dx, dy)
            if d == 0:
                continue
            if self.wave_t is not None and self.wave_t < i * config.WAVE_STEP:   # 파도가 아직 안 닿은 마디
                self.gaps[i] = min(base * config.WAVE_STRETCH, max(self.gaps[i], d))   # 버팀: 늘어나기만
            else:
                self.gaps[i] = max(base, self.gaps[i] - config.WAVE_RESTORE * dt)      # 따라붙음: 줄어들기만
            seg.x = front.x - dx / d * self.gaps[i]          # 앞 마디 → 이 마디 방향으로 gaps[i]만큼
            seg.y = front.y - dy / d * self.gaps[i]
            seg.angle = math.atan2(dy, dx)                   # 앞 마디를 바라봄

    def draw(self, camera):
        # 1. 그림자를 먼저 전부 깐다 (몸·다리 위에 그림자가 겹치지 않게)
        for leg in self.all_legs():
            leg.draw_shadow(camera)
        for i, seg in enumerate(self.segs):
            size = self.seg_size(i)
            along, across = self.shape(i)
            sx, sy = camera.to_screen(seg.x + seg.ox, seg.y + seg.oy)
            k = self.seg_h(i) / config.BODY_HEIGHT                                 # 높이에 비례해 그림자가 멀어짐 (점프하면 멀리, 처지면 가까이)
            fill_rect_rotated(sx + config.SHADOW_DX * k, sy + config.SHADOW_DY * k, size * along + 2, size * across + 2, seg.angle,
                              (0, 0, 0), config.SHADOW_ALPHA)
        self.effects.draw_ground(camera)       # 흙먼지 (바닥)
        self.effects.draw_cuts(camera)         # 잘린 다리 (바닥)
        self.effects.draw_ghosts(camera)       # 질주 잔상
        # 2. 다리 (마디 아래에)
        for leg in self.all_legs():
            leg.draw(camera)
        # 늘어난 마디 사이 연결선: 가늘고 흐리게 (WAVE로 몸이 늘어났을 때만)
        for i in range(1, len(self.segs)):
            if self.gaps[i] > config.SEG_SPACING + 1:
                a, b = self.segs[i - 1], self.segs[i]
                ax, ay = camera.to_screen(a.x + a.ox, a.y + a.oy)
                bx, by = camera.to_screen(b.x + b.ox, b.y + b.oy)
                draw_line(ax, ay + self.seg_h(i - 1) * config.VIEW_TILT,
                          bx, by + self.seg_h(i) * config.VIEW_TILT, 1, config.COLOR_WHITE, config.WAVE_LINK_ALPHA)
        # 3. 마디: 꼬리부터 그려서 머리가 맨 위에 오게 한다. 몸은 height(+점프 높이)만큼 떠 있으니 그만큼 화면 위로
        for i in range(len(self.segs) - 1, -1, -1):
            seg = self.segs[i]
            size = self.seg_size(i)
            sx, sy = camera.to_screen(seg.x + seg.ox, seg.y + seg.oy)
            draw_segment(sx, sy + self.seg_h(i) * config.VIEW_TILT, size, seg.angle, self.invincible(i), *self.shape(i),
                         flash=seg.flash / config.HIT_FLASH)
        # 머리 앞쪽 가장자리 근처에 주황 점 — 어느 쪽이 앞인지 표시
        head = self.segs[0]
        lift = self.seg_h(0) * config.VIEW_TILT
        hx, hy = camera.to_screen(head.x + head.ox, head.y + head.oy)
        r = config.BOX_HEAD_SIZE * self.shape(0)[0] / 2 - config.BOX_EYE_SIZE / 2 - 1     # 중심에서 점까지 거리 (늘어나면 앞 가장자리도)
        ex, ey = hx + math.cos(head.angle) * r, hy + lift + math.sin(head.angle) * r
        if self.stun > 0:
            # 착지 경직 중: 눈을 감음 — 앞뒤로 얇고 옆으로 긴 가는 선
            fill_rect_rotated(ex, ey, config.EYE_CLOSED_THICK, config.BOX_EYE_SIZE + 2, head.angle, config.COLOR_ORANGE)
        else:
            fill_rect_rotated(ex, ey, config.BOX_EYE_SIZE, config.BOX_EYE_SIZE, head.angle, config.COLOR_ORANGE)


def draw_segment(x, y, size, angle, ghost=False, along=1.0, across=1.0, flash=0.0):
    # 크롤러 마디 그리기 — Body와 다리 파츠(world/objects.py)가 같이 쓴다 (파츠가 크롤러 조각처럼 보이게)
    # 입체감 있는 사각 마디 하나 (화면 좌표). 빛은 LIGHT_DIR(왼쪽 위)에서 온다고 본다
    # ghost = WAVE로 공중에 뜬(무적) 마디: 전체를 WAVE_GHOST배로 흐리게 → 유령처럼 비침
    # along, across = 바라보는 방향 길이·폭 배율 (WAVE 공중엔 길쭉, 착지 땐 납작 — 평소 1, 1 = 정사각형)
    # flash = 피격 번쩍임 0~1 (빨간 덧칠 진하기)
    lx, ly = config.LIGHT_DIR
    a = config.WAVE_GHOST if ghost else 1.0
    w, hgt = size * along, size * across
    # 반투명 몸 채움
    fill_rect_rotated(x, y, w, hgt, angle, config.COLOR_BODY, config.BOX_BODY_ALPHA * a)
    # 윗면 하이라이트: 작은 밝은 사각형을 빛 쪽으로 살짝 옮겨 겹침 → 볼록해 보임
    hs = config.BOX_HIGHLIGHT_SIZE
    shift = size * config.BOX_HIGHLIGHT_SHIFT
    fill_rect_rotated(x + lx * shift, y + ly * shift, w * hs, hgt * hs, angle, config.COLOR_BODY_LIGHT, config.BOX_HIGHLIGHT_ALPHA * a)
    # 테두리: 네 변을 각각 빛을 받는 정도에 따라 밝게/어둡게
    c, s = math.cos(angle), math.sin(angle)
    hw, hh = w / 2, hgt / 2
    corners = []
    for px, py in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
        corners.append((x + px * c - py * s, y + px * s + py * c))    # 회전 변환
    for k in range(4):
        x1, y1 = corners[k]
        x2, y2 = corners[(k + 1) % 4]
        edge = math.hypot(x2 - x1, y2 - y1) or 1
        nx, ny = (y2 - y1) / edge, -(x2 - x1) / edge          # 변의 바깥쪽 방향 (단위 벡터)
        lit = (nx * lx + ny * ly + 1) / 2                     # 빛을 받는 정도 0(등진 쪽) ~ 1(정면)
        f = config.EDGE_DARK + (1 - config.EDGE_DARK) * lit   # 밝기 배율
        color = (int(config.COLOR_WHITE[0] * f), int(config.COLOR_WHITE[1] * f), int(config.COLOR_WHITE[2] * f))
        draw_line(x1, y1, x2, y2, 1, color, a)
    if flash > 0:
        fill_rect_rotated(x, y, w, hgt, angle, config.COLOR_RED, 0.8 * flash)   # 피격: 빨갛게 번쩍
