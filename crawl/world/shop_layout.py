# 쇼핑몰 레이아웃 — 아마존 화면 구성을 레퍼런스로, 어두운 테마로 배치한다 (PRD 10.1, S10-5).
# 이름·로고는 실제 회사가 아닌 가상의 'W·E·B 마켓'. 글 배치·링크·문단·출구는 PageLayout 공통.
# 문서는 두 종류 (data/pages/shop/*.json의 kind):
#
# 검색 결과 (kind: search)
#   title(문서 이름, 예: '검색: 텀블러'), query(검색어), count(결과 수 글)
#   filters: [[제목, [글, ...]], ...]        왼쪽 거르기 칸 (글에 [[링크]] 가능)
#   results: [{name, image, rating, reviews, price, list_price?, badge?, sponsored?, delivery?}, ...]
#            name은 표기 글 — 보통 [[상품 제목]] (그 상품 페이지로 가는 링크)
#
# 상품 상세 (kind: product)
#   title(상품 이름), brand(표기 글), path([분류, ...] — 맨 위 경로), image
#   rating, reviews, price, list_price?, options?([글, ...])
#   bullets: [표기 글, ...]                   '이 상품 정보' 점 목록
#   also_viewed: [{name, image, rating, price}, ...]   함께 본 상품 카드 (name은 [[상품]])
#   description: [표기 글, ...]               상품 설명 문단
#   review_list: [{user, stars, head, text, date}, ...]  고객 리뷰 (text는 표기 글)
import config
from ui.draw import text_width
from world.page_layout import PageLayout

NAVY = (19, 25, 33)          # 머리글 (아마존의 짙은 남색)
NAVY2 = (35, 47, 62)         # 메뉴 줄
BG2 = (24, 26, 30)           # 카드·상자 바탕
RULE = (58, 62, 70)          # 구분선
SUBTLE = (150, 154, 160)
WHITE = (238, 238, 238)
ORANGE = (255, 153, 0)       # 별·로고 웃음 선
YELLOW = (255, 216, 20)      # 장바구니 버튼
BUY = (255, 164, 28)         # 바로 구매 버튼
DEAL = (204, 12, 57)         # 할인율
GREEN = (0, 160, 90)         # 재고 있음
MENU = ['전체', '오늘의 딜', '베스트셀러', '신상품', '고객센터', '선물하기', '쿠폰']
SHOP_DEFAULTS = {
    'kind': 'product', 'brand': 'W·E·B 베이직', 'path': ['홈'], 'rating': 4.0, 'reviews': 0, 'price': 10000,
    'options': [], 'bullets': [], 'also_viewed': [], 'description': [], 'review_list': [],
    'query': '', 'count': '', 'filters': [], 'results': [],
}


def won(n):
    return '{:,}원'.format(n)


class ShopLayout(PageLayout):
    BODY_SIZE = 15
    LINE_H = 25
    TEXT = (220, 222, 226)
    LINK = (90, 200, 230)             # 아마존 링크색(청록)을 어두운 바탕에 맞게 밝게
    VISITED = (170, 150, 220)
    REDLINK = (235, 120, 105)
    ALPHA = 0.6
    CONTENT_X = 60                    # 아마존처럼 화면 폭을 거의 다 씀
    CONTENT_W = config.SCREEN_W - 120
    LINK_UNDERLINE = False
    HEADER_H = 60
    MENU_H = 38

    def build(self, doc):
        doc = dict(SHOP_DEFAULTS, **doc)
        top = self.height
        y = self.header(top, doc)
        if doc['kind'] == 'search':
            y = self.search_page(doc, y)
        else:
            y = self.product_page(doc, y)
        y = self.exit_box(y)
        return self.footer(y)

    # ── 공통: 머리글·바닥글·별점·값 ──
    def logo(self, x, mid):
        # 'W·E·B 마켓' + 아래 주황 웃음 선 (가상의 쇼핑몰)
        w = self.text_mid(x, mid + 3, 'W·E·B', 22, 'bold', WHITE)
        self.text_mid(x + w + 6, mid + 3, '마켓', 15, 'bold', WHITE)
        for i in range(6):                                   # 웃음 선: 짧은 선 여섯 개로 휜 모양
            x1, x2 = x + 4 + i * (w - 4) / 6, x + 4 + (i + 1) * (w - 4) / 6
            y1 = mid - 11 - 3 * (1 - ((i - 2.5) / 2.5) ** 2)
            y2 = mid - 11 - 3 * (1 - ((i - 1.5) / 2.5) ** 2)
            self.line(x1, y1, x2, y2, 2, ORANGE)
        return x + w + 50

    def header(self, top, doc):
        # 남색 머리글: 로고 · 배송지 · 검색창(주황 단추) · 계정·주문·장바구니 / 아래 메뉴 줄
        h = self.HEADER_H
        mid = top - h / 2
        self.fill(0, top - h, config.SCREEN_W, h, NAVY)
        cx = self.logo(24, mid)
        self.text_mid(cx, mid + 8, '배송지', 11, 'ui', SUBTLE)
        self.text_mid(cx, mid - 8, '서울 웹동', 13, 'bold', WHITE)
        sx = cx + 100
        sw = config.SCREEN_W - sx - 330
        self.fill(sx, mid - 18, sw, 36, BG2)
        self.rect(sx, mid - 18, sw, 36, RULE)
        self.fill(sx, mid - 18, 60, 36, NAVY2)
        self.text_mid(sx + 12, mid, '전체', 12, 'ui', SUBTLE)
        self.text_mid(sx + 72, mid, doc['query'] or '검색 W·E·B 마켓', 14, 'ui', WHITE if doc['query'] else SUBTLE)
        self.fill(sx + sw - 44, mid - 18, 44, 36, BUY)
        self.rect(sx + sw - 32, mid - 2, 12, 12, NAVY)        # 돋보기
        self.line(sx + sw - 20, mid - 2, sx + sw - 13, mid - 9, 2, NAVY)
        rx = config.SCREEN_W - 300
        for small, big in [('안녕하세요, 로그인', '계정 및 목록'), ('반품', '& 주문')]:
            self.text_mid(rx, mid + 8, small, 11, 'ui', WHITE)
            self.text_mid(rx, mid - 8, big, 13, 'bold', WHITE)
            rx += 120
        self.rect(rx, mid - 10, 26, 18, WHITE)                # 장바구니
        self.text_mid(rx + 9, mid - 1, '0', 12, 'bold', ORANGE)
        self.text_mid(rx + 30, mid - 4, '장바구니', 13, 'bold', WHITE)
        # 메뉴 줄
        y = top - h
        m = self.MENU_H
        self.fill(0, y - m, config.SCREEN_W, m, NAVY2)
        cx = 24
        for i, item in enumerate(MENU):
            if i == 0:
                for k in range(3):                            # ≡ 메뉴 표시 (글꼴에 없어 선으로)
                    self.line(cx, y - m / 2 - 5 + k * 5, cx + 14, y - m / 2 - 5 + k * 5, 2, WHITE)
                cx += 20
            cx += self.text_mid(cx, y - m / 2, item, 13, 'bold' if i == 0 else 'ui', WHITE) + 22
        return y - m

    def stars(self, x, mid, rating, size=15):
        # 별 다섯 개: 점수만큼(반올림) 주황 ★, 나머지는 ☆. 별 줄 폭을 돌려준다
        full = int(rating + 0.5)
        cx = x
        for i in range(5):
            cx += self.text_mid(cx, mid, '★' if i < full else '☆', size, 'ui', ORANGE if i < full else SUBTLE) + 1
        return cx - x

    def price_line(self, x, mid, price, list_price, big=26):
        # '-24%' + 큰 가격 (할인 없으면 가격만). 줄 폭을 돌려준다
        cx = x
        if list_price and list_price > price:
            off = round(100 * (1 - price / list_price))
            cx += self.text_mid(cx, mid, '-%d%%' % off, int(big * 0.85), 'ui', DEAL) + 10
        cx += self.text_mid(cx, mid, won(price), big, 'bold', WHITE)
        return cx - x

    def list_price(self, x, mid, list_price, size=12):
        # '정가: 25,000원' 취소선
        if not list_price:
            return
        w = self.text_mid(x, mid, '정가: ', size, 'ui', SUBTLE)
        pw = self.text_mid(x + w, mid, won(list_price), size, 'ui', SUBTLE)
        self.line(x + w, mid, x + w + pw, mid, 1, SUBTLE)

    def heading(self, x, y, text, size=20):
        self.text_mid(x, y - size * 0.7, text, size, 'bold', WHITE)
        return y - size * 1.4 - 10

    def rule(self, y):
        self.line(self.left, y, self.right, y, 1, RULE)
        return y - 24

    # ── 검색 결과 ──
    def search_page(self, doc, y):
        # 결과 줄 → 왼쪽 거르기 칸 + 오른쪽 결과 카드 격자 (4칸)
        y -= 8
        self.fill(0, y - 40, config.SCREEN_W, 40, BG2)
        cx = self.left + self.text_mid(self.left, y - 20, '%s 결과: ' % doc['count'], 14, 'ui', WHITE)
        self.text_mid(cx, y - 20, '"%s"' % doc['query'], 14, 'bold', ORANGE)
        self.rect(self.right - 170, y - 32, 170, 24, RULE)
        self.text_mid(self.right - 160, y - 20, '정렬 기준: 추천순', 12, 'ui', WHITE)
        y -= 64
        top = y
        # 왼쪽 거르기 칸
        fx, fw = self.left, 210
        fy = y
        for title, items in doc['filters']:
            fy = self.paragraph('**' + title + '**', fx, fy, fw, 15, WHITE, 24) - 4
            for item in items:
                fy = self.paragraph(item, fx + 4, fy, fw - 4, 14, self.TEXT, 24)
            fy -= 18
        # 결과 카드
        gx = self.left + fw + 40
        cols, gap = 4, 22
        cw = (self.right - gx - gap * (cols - 1)) / cols
        row_top = y
        for i, r in enumerate(doc['results']):
            col = i % cols
            if col == 0 and i > 0:
                row_top = row_bottom - 26
            if col == 0:
                row_bottom = row_top
            bottom = self.result_card(r, gx + col * (cw + gap), row_top, cw)
            row_bottom = min(row_bottom, bottom)
        y = min(fy, row_bottom if doc['results'] else y)
        return y - 30

    def result_card(self, r, x, y, w):
        # 결과 카드 하나: 정사각 사진(+딱지) → 스폰서 → 상품 이름 링크 → 별점·리뷰 수 → 가격 → 정가 → 배송
        self.fill(x, y - w, w, w, BG2)
        self.image(x + 10, y - w + 10, w - 20, w - 20, r['image'])
        if r.get('badge'):
            bw = text_width(r['badge'], 11, 'bold') + 12
            self.fill(x, y - 22, bw, 22, (196, 80, 0))
            self.text_mid(x + 6, y - 11, r['badge'], 11, 'bold', WHITE)
        y -= w + 10
        if r.get('sponsored'):
            self.text_mid(x, y - 7, '스폰서', 11, 'ui', SUBTLE)
            y -= 18
        y = self.paragraph(r['name'], x, y, w, 15, WHITE, 22) - 4
        sw = self.stars(x, y - 9, r['rating'], 13)
        self.text_mid(x + sw + 6, y - 9, '{:,}'.format(r['reviews']), 12, 'ui', self.LINK)
        y -= 26
        self.price_line(x, y - 12, r['price'], r.get('list_price'), 22)
        y -= 32
        if r.get('list_price'):
            self.list_price(x, y - 7, r['list_price'])
            y -= 20
        self.text_mid(x, y - 7, r.get('delivery', '무료 배송 내일 도착 보장'), 12, 'ui', SUBTLE)
        return y - 16

    # ── 상품 상세 ──
    def product_page(self, doc, y):
        # 경로 → [사진 | 이름·가격·상품 정보 | 구매 상자] → 함께 본 상품 → 상품 설명 → 고객 리뷰
        y -= 14
        path = ' › '.join(doc['path'])
        self.text_mid(self.left, y - 8, path, 12, 'ui', SUBTLE)
        y -= 34
        top = y
        # 왼쪽: 작은 사진 줄 + 큰 사진
        tx, ix, isz = self.left, self.left + 62, 420
        for k in range(4):
            self.rect(tx, y - 8 - k * 58 - 50, 50, 50, ORANGE if k == 0 else RULE)
            self.image(tx + 3, y - 8 - k * 58 - 47, 44, 44, doc['image'])
        self.image(ix, y - isz, isz, isz, doc['image'])
        left_bottom = y - isz - 10
        # 가운데: 이름 · 브랜드 · 별점 · 가격 · 옵션 · 이 상품 정보
        cx, cw = ix + isz + 40, 400
        cy = self.paragraph('**' + doc['title'] + '**', cx, y, cw, 22, WHITE, 32) - 2
        cy = self.paragraph(doc['brand'], cx, cy, cw, 14, self.TEXT, 22) - 4
        self.text_mid(cx, cy - 9, '%.1f' % doc['rating'], 14, 'ui', WHITE)
        sw = self.stars(cx + 30, cy - 9, doc['rating'])
        self.text_mid(cx + 36 + sw, cy - 9, '{:,}개 평가'.format(doc['reviews']), 13, 'ui', self.LINK)
        cy -= 28
        self.line(cx, cy, cx + cw, cy, 1, RULE)
        cy -= 30
        self.price_line(cx, cy, doc['price'], doc.get('list_price'), 28)
        cy -= 30
        self.list_price(cx, cy, doc.get('list_price'))
        cy -= 30
        if doc['options']:
            self.text_mid(cx, cy, '옵션:', 13, 'bold', WHITE)
            ox = cx + 44
            for k, opt in enumerate(doc['options']):
                ow = text_width(opt, 13) + 20
                self.rect(ox, cy - 14, ow, 28, ORANGE if k == 0 else RULE)
                self.text_mid(ox + 10, cy, opt, 13, 'ui', WHITE)
                ox += ow + 8
            cy -= 40
        self.line(cx, cy, cx + cw, cy, 1, RULE)
        cy = self.heading(cx, cy - 14, '이 상품 정보', 16)
        for b in doc['bullets']:
            self.text_mid(cx, cy - 12, '•', 15, 'bold', WHITE)
            cy = self.body_paragraph(b, cx + 16, cy, cw - 16) - 6
        # 오른쪽: 구매 상자
        bx, bw = cx + cw + 30, self.right - (cx + cw + 30)
        by = y
        bh = 300
        self.rect(bx, by - bh, bw, bh, RULE)
        px = bx + 16
        self.price_line(px, by - 30, doc['price'], None, 24)
        self.text_mid(px, by - 64, '무료 배송', 13, 'ui', self.LINK)
        self.text_mid(px, by - 84, '내일(화) 도착 보장', 13, 'bold', WHITE)
        self.text_mid(px, by - 116, '재고 있음', 17, 'ui', GREEN)
        self.rect(px, by - 152, 90, 26, RULE)
        self.text_mid(px + 10, by - 139, '수량: 1', 12, 'ui', WHITE)
        for k, (label, color) in enumerate([('장바구니에 담기', YELLOW), ('바로 구매', BUY)]):
            ty = by - 196 - k * 44
            self.fill(px, ty - 16, bw - 32, 32, color)
            self.text_mid(px + (bw - 32 - text_width(label, 13)) / 2, ty, label, 13, 'ui', NAVY)
        self.text_mid(px, by - 284, '판매: W·E·B 마켓', 12, 'ui', SUBTLE)
        y = min(left_bottom, cy, by - bh) - 30
        y = self.rule(y)
        y = self.also_viewed(doc, y)
        y = self.description(doc, y)
        return self.reviews(doc, y)

    def also_viewed(self, doc, y):
        # 이 상품을 본 고객이 함께 본 상품: 카드 5장 한 줄
        if not doc['also_viewed']:
            return y
        y = self.heading(self.left, y, '이 상품을 본 고객이 함께 본 상품')
        cols, gap = 5, 26
        cw = (self.right - self.left - gap * (cols - 1)) / cols
        lowest = y
        for i, card in enumerate(doc['also_viewed'][:cols]):
            x = self.left + i * (cw + gap)
            size = cw * 0.8
            self.image(x + (cw - size) / 2, y - size, size, size, card['image'])
            cy = self.paragraph(card['name'], x, y - size - 10, cw, 14, WHITE, 21) - 2
            self.stars(x, cy - 8, card.get('rating', 4), 12)
            self.price_line(x, cy - 32, card['price'], None, 17)
            lowest = min(lowest, cy - 50)
        return self.rule(lowest - 10)

    def description(self, doc, y):
        if not doc['description']:
            return y
        y = self.heading(self.left, y, '상품 설명')
        for p in doc['description']:
            y = self.body_paragraph(p, self.left, y, 820) - 14
        return self.rule(y - 6)

    def reviews(self, doc, y):
        # 고객 리뷰: 왼쪽 별점 요약(막대 그래프) + 오른쪽 리뷰 목록
        y = self.heading(self.left, y, '고객 리뷰')
        top = y
        x = self.left
        sw = self.stars(x, y - 10, doc['rating'], 18)
        self.text_mid(x + sw + 10, y - 10, '5점 만점에 %.1f점' % doc['rating'], 15, 'bold', WHITE)
        self.text_mid(x, y - 38, '전체 평가 {:,}개'.format(doc['reviews']), 13, 'ui', SUBTLE)
        shares = review_shares(doc['rating'])
        for k, share in enumerate(shares):                   # 5점 ~ 1점 막대
            my = y - 72 - k * 30
            self.text_mid(x, my, '%d점' % (5 - k), 13, 'ui', self.LINK)
            self.rect(x + 40, my - 10, 200, 20, RULE)
            self.fill(x + 41, my - 9, 198 * share, 18, ORANGE)
            self.text_mid(x + 250, my, '%d%%' % round(share * 100), 13, 'ui', self.LINK)
        left_bottom = y - 72 - 5 * 30
        rx, rw = self.left + 340, 760
        for r in doc['review_list']:
            self.fill(rx, y - 26, 26, 26, RULE)               # 프로필 동그라미 자리
            self.text_mid(rx + 36, y - 13, r['user'], 13, 'ui', WHITE)
            y -= 38
            sw = self.stars(rx, y - 9, r['stars'], 14)
            self.text_mid(rx + sw + 8, y - 9, r['head'], 14, 'bold', WHITE)
            y -= 24
            self.text_mid(rx, y - 8, '%s 대한민국에서 작성' % r.get('date', '2026년 11월 3일'), 12, 'ui', SUBTLE)
            self.text_mid(rx, y - 28, '구매 확인', 12, 'bold', BUY)
            y -= 44
            y = self.body_paragraph(r['text'], rx, y, rw) - 8
            self.rect(rx, y - 26, 90, 26, RULE)
            self.text_mid(rx + 18, y - 13, '도움이 됨', 12, 'ui', WHITE)
            y -= 54
        return min(y, left_bottom) - 10

    def footer(self, y):
        # '맨 위로' 띠 + 남색 바닥글 (가상 쇼핑몰 안내)
        top = y - 10
        self.fill(0, top - 44, config.SCREEN_W, 44, NAVY2)
        self.text_mid((config.SCREEN_W - text_width('맨 위로', 13)) / 2, top - 22, '맨 위로', 13, 'ui', WHITE)
        top -= 44
        h = 130
        self.fill(0, top - h, config.SCREEN_W, h, NAVY)
        cx = 120
        for s in ['회사 소개', '판매자 되기', '고객센터', '배송 안내', '반품 및 교환', '이용 약관']:
            cx += self.text_mid(cx, top - 40, s, 13, 'ui', WHITE) + 34
        self.text_mid(120, top - 90, '© 2026 W·E·B 마켓. 이 사이트는 CRAWL.EXE 속 가상의 쇼핑몰이며 실제 회사가 아닙니다.', 12, 'ui', SUBTLE)
        return top - h


def review_shares(rating):
    # 평균 점수로 5점~1점 비율을 그럴듯하게 (높을수록 5점이 많음). 합이 1
    raw = [max(0.02, 1 - abs(star - rating) / 2.2) ** 2 for star in (5, 4, 3, 2, 1)]
    total = sum(raw)
    return [v / total for v in raw]
