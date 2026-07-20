"""
카드 추천 스코어링 프로토타입 v0.5 (가맹점 커버리지 계수 반영)
입력: 카테고리별 월 소비액(dict), 카드 구분 선호(신용/체크/None)
출력: 순기대혜택액(월 기대혜택 - 연회비/12) 기준 카드 랭킹

필요 파일: cardlist_step5_master.csv, card_benefits_long.csv

v0.4 변경점:
  - 옵션형(택1) 혜택: 옵션그룹 내 최대 기대혜택 1개만 반영 (사용자가 최적 옵션을
    선택한다고 가정), 그룹 헤더 블록과 연1회 기프트성 혜택은 스코어링 제외
  - 다중 카테고리 혜택(카테고리목록): 해당 카테고리들의 소비액 합산에 적용
  - '모든가맹점' 혜택: 총 소비액 전체에 적용

핵심 가정(파라미터로 조정 가능):
  - FUEL_PRICE: 주유 원/L 혜택 환산용 유가 (기본 1,700원/L)
  - MILE_AS_WON: 1마일 가치 (기본 15원), 포인트는 1P=1원
  - DEFAULT_CAP_HIGHRATE: 한도 미상 & 할인율 20% 이상 혜택의 보수적 월 한도 (기본 1만원)
  - 사용자 전월실적 = 입력 소비액 합계로 가정 (마이데이터 연동 시 대체)
  - MERCHANT_COVERAGE: 혜택의 가맹점 범위에 따른 카테고리 소비 커버리지 계수
    (단일가맹점 혜택은 해당 카테고리 소비 중 일부에만 적용된다는 가정;
     결제 시점 추천에서는 가맹점목록 직접 매칭으로 대체)
"""
import pandas as pd
import numpy as np

FUEL_PRICE = 1700.0
MILE_AS_WON = 15.0
DEFAULT_CAP_HIGHRATE = 10000.0
MERCHANT_COVERAGE = {'업종전체': 1.0, '복수가맹점': 0.8, '단일가맹점': 0.4, '불명': 0.5}


def load(master_path='cardlist_step5_master.csv',
         bene_path='card_benefits_long.csv'):
    master = pd.read_csv(master_path, encoding='utf-8-sig')
    bene = pd.read_csv(bene_path, encoding='utf-8-sig')
    bene = bene.merge(master[['카드번호', '통합한도_월']], on='카드번호', how='left',
                      suffixes=('', '_m'))
    if '통합한도_월_m' not in bene.columns:
        bene['통합한도_월_m'] = bene['통합한도_월']
    return master, bene


def _expected(row, cat_spend, user_perf):
    if row.get('옵션헤더', False) or row.get('적용범위') == '연1회기프트':
        return 0.0
    if pd.notnull(row.get('카테고리목록')):
        cats = str(row['카테고리목록']).split('|')
    else:
        cats = [row['카테고리']]
    if '모든가맹점' in cats:
        spend = sum(cat_spend.values())
    else:
        spend = sum(cat_spend.get(c, 0) for c in cats)
    spend *= MERCHANT_COVERAGE.get(row.get('가맹점수준', '업종전체'), 1.0)
    if spend <= 0:
        return 0.0
    if not np.isnan(row['실적조건']) and user_perf < row['실적조건']:
        return 0.0
    unit, val = row['혜택단위'], row['혜택값']
    if pd.isnull(unit) or np.isnan(val):
        return 0.0
    if unit == '%':
        raw = spend * val / 100 * (1.5 if row['혜택유형'] == '마일리지 적립' else 1.0)
    elif unit == '원/L':
        raw = spend / FUEL_PRICE * val
    elif unit == '마일/천원':
        raw = spend / 1000 * val * MILE_AS_WON
    elif unit == '원':
        raw = val * (row['횟수_월'] if not np.isnan(row['횟수_월']) else 1)
    else:
        return 0.0
    cap = row['월최대혜택액']
    if np.isnan(cap) and not row.get('한도없음', False):
        if not np.isnan(row.get('통합한도_월_m', np.nan)):
            cap = row['통합한도_월_m']
        elif unit == '%' and val >= 20:
            cap = DEFAULT_CAP_HIGHRATE
    return min(raw, cap) if not np.isnan(cap) else raw


def recommend(master, bene, cat_spend, card_type=None, top_n=10):
    user_perf = sum(cat_spend.values())
    pool = master if card_type is None else master[master['구분'] == card_type]
    pool = pool[pool['전월실적'] <= user_perf]
    sub = bene[bene['카드번호'].isin(pool['카드번호'])].copy()
    sub['기대'] = sub.apply(_expected, axis=1, args=(cat_spend, user_perf))
    # 옵션그룹은 그룹 내 최대 1개(택1), 일반 혜택은 합산
    normal = sub[sub['옵션그룹'].isnull()].groupby('카드번호')['기대'].sum()
    opt = (sub[sub['옵션그룹'].notnull()]
           .groupby(['카드번호', '옵션그룹'])['기대'].max()
           .groupby('카드번호').sum())
    cb = normal.add(opt, fill_value=0).rename('월기대혜택액')
    out = pool.merge(cb, on='카드번호', how='left').fillna({'월기대혜택액': 0})
    out['월기대혜택액'] = np.where(out['통합한도_월'].notnull(),
                              np.minimum(out['월기대혜택액'], out['통합한도_월']),
                              out['월기대혜택액'])
    out['순기대혜택액'] = out['월기대혜택액'] - out['연회비_최소'].fillna(0) / 12
    cols = ['카드번호', '카드명', '카드사', '구분', '전월실적', '연회비_최소',
            '월기대혜택액', '순기대혜택액', '한도파악률']
    return out.sort_values('순기대혜택액', ascending=False)[cols].head(top_n)


if __name__ == '__main__':
    master, bene = load()
    spend = {'공과금/생활요금': 200000, '통신': 100000, '온라인쇼핑': 300000,
             '편의점': 100000, '푸드/외식': 200000}
    print(recommend(master, bene, spend, top_n=5).to_string(index=False))
