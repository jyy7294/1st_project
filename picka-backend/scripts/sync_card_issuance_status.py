"""Synchronize cards.is_active with current Card Gorilla issuance signals.

The source keeps archived card detail pages visible, so ``is_visible`` does not
mean a card can still be issued. We use only explicit application signals:
online application support or a currently active acquisition event. Unknown or
failed lookups are left unchanged; use ``--apply`` to persist confirmed results.
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


def fetch_is_issuable(source_card_id: int) -> tuple[int, bool]:
    request = Request(
        API_URL.format(source_card_id=source_card_id),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
    event = payload.get("event") or {}
    is_issuable = bool(
        payload.get("only_online") is True
        or event.get("evt_status") == "T"
    )
    return source_card_id, is_issuable


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
            f"changes={len(changes)} failures={len(failures)}"
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
