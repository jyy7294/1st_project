"""card_database.json 의 연회비 정보를 cards.annual_fee 컬럼으로 채웁니다.

시드 과정에서 연회비(연회비_최소)가 DB로 적재되지 않아 대부분 NULL 로 남아,
신규 카드 추천 화면에서 연회비가 전부 '없음' 으로 표시되던 문제를 바로잡습니다.

매칭: cards.source_card_id  ↔  card_database.json 의 '카드번호'
값:   연회비_무료 == True → 0,  아니면 연회비_최소(정수).
"""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Card


CDB_PATH = Path(__file__).resolve().parents[1] / "card_database.json"


def _load_cards(data) -> list[dict]:
    if isinstance(data, list):
        return [c for c in data if isinstance(c, dict)]
    if isinstance(data, dict):
        for key in ("cards", "data", "items"):
            if isinstance(data.get(key), list):
                return [c for c in data[key] if isinstance(c, dict)]
        # 카드번호를 가진 dict 들의 모음인 경우
        values = [v for v in data.values() if isinstance(v, dict)]
        if values and all("카드번호" in v for v in values):
            return values
    return []


def _fee_for(card: dict) -> int | None:
    if card.get("연회비_무료") is True:
        return 0
    minimum = card.get("연회비_최소")
    if minimum is None:
        return None
    try:
        return int(float(minimum))
    except (TypeError, ValueError):
        return None


def main() -> None:
    with CDB_PATH.open(encoding="utf-8") as file:
        data = json.load(file)

    fee_by_source = {}
    for card in _load_cards(data):
        num = card.get("카드번호")
        fee = _fee_for(card)
        if num is not None and fee is not None:
            fee_by_source[str(num)] = fee

    updated = 0
    skipped_no_match = 0
    with SessionLocal() as db:
        cards = db.scalars(select(Card).where(Card.source_card_id.isnot(None))).all()
        for card in cards:
            fee = fee_by_source.get(str(card.source_card_id))
            if fee is None:
                skipped_no_match += 1
                continue
            if card.annual_fee != fee:
                card.annual_fee = fee
                updated += 1
        db.commit()

    print(f"card_database 연회비 로드: {len(fee_by_source)}개")
    print(f"annual_fee 갱신: {updated}개")
    print(f"매칭 실패(원본에 없음): {skipped_no_match}개")


if __name__ == "__main__":
    main()
