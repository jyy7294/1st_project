"""Synchronize ``cards.is_active`` with Card Gorilla's discontinuation flag.

``only_online`` and acquisition-event status describe how a card is promoted;
they do not prove whether ordinary issuance is available.  The source exposes
an explicit ``is_discon`` flag, so cards are disabled only when that flag is
true.  Missing/invalid flags and failed lookups are left unchanged.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from urllib.request import Request, urlopen

from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models import Card, CardRecommendationSnapshot


API_URL = "https://api.card-gorilla.com:8080/v1/cards/{source_card_id}"
USER_AGENT = "Mozilla/5.0 (compatible; PICKA issuance status sync)"


def resolve_is_issuable(payload: dict) -> bool | None:
    """Return issuance status only when the source gives an explicit signal."""
    is_discontinued = payload.get("is_discon")
    if is_discontinued is True:
        return False
    if is_discontinued is False:
        return True
    return None


def fetch_is_issuable(source_card_id: int) -> tuple[int, bool | None]:
    request = Request(
        API_URL.format(source_card_id=source_card_id),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
    return source_card_id, resolve_is_issuable(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()

    with SessionLocal() as db:
        cards = db.scalars(
            select(Card).where(Card.source_card_id.is_not(None)).order_by(Card.id)
        ).all()
        by_source_id = {card.source_card_id: card for card in cards}
        results: dict[int, bool] = {}
        unknown: list[int] = []
        failures: list[tuple[int, str]] = []

        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            futures = {
                executor.submit(fetch_is_issuable, source_id): source_id
                for source_id in by_source_id
            }
            for future in as_completed(futures):
                source_id = futures[future]
                try:
                    resolved_id, is_issuable = future.result()
                    if is_issuable is None:
                        unknown.append(resolved_id)
                    else:
                        results[resolved_id] = is_issuable
                except Exception as error:
                    failures.append((source_id, str(error)))

        changes = [
            (card, results[card.source_card_id])
            for card in cards
            if card.source_card_id in results
            and card.is_active != results[card.source_card_id]
        ]
        active_count = sum(results.values())
        print(
            f"checked={len(results)} issuable={active_count} "
            f"not_issuable={len(results) - active_count} "
            f"changes={len(changes)} unknown={len(unknown)} "
            f"failures={len(failures)}"
        )
        for card, is_issuable in changes[:30]:
            print(f"{card.id}\t{card.source_card_id}\t{is_issuable}\t{card.card_name}")
        if failures:
            print("failed source ids:", ", ".join(str(item[0]) for item in failures[:30]))

        if args.apply:
            for card, is_issuable in changes:
                card.is_active = is_issuable
            # Snapshots may contain cards that have just been deactivated.
            db.execute(delete(CardRecommendationSnapshot))
            db.commit()
            print("applied changes and cleared recommendation snapshots")
        else:
            print("dry run only; pass --apply to persist")


if __name__ == "__main__":
    main()
