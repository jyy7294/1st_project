import pandas as pd
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.merchant_alias import MerchantAlias


CSV_PATH = "merchant_alias_dictionary.csv"


def main():

    df = pd.read_csv(CSV_PATH)

    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        # SessionLocal은 autoflush=False이므로 루프 중 select만으로는
        # 이번 실행에서 db.add()한 alias 중복을 발견할 수 없다.
        seen_aliases = set(
            db.scalars(
                select(MerchantAlias.alias)
            ).all()
        )

        for _, row in df.iterrows():
            alias = row["alias"]

            if pd.isna(alias) or alias in seen_aliases:
                skipped += 1
                continue

            db.add(
                MerchantAlias(
                    alias=alias,
                    canonical_merchant=row["canonical_merchant"],
                    category=row["category"],
                    match_type=row["match_type"]
                    if pd.notna(row["match_type"])
                    else None,
                    priority=int(row["priority"])
                    if pd.notna(row["priority"])
                    else None,
                    source=row["source"]
                    if pd.notna(row["source"])
                    else None,
                )
            )

            seen_aliases.add(alias)
            inserted += 1

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    print(f"저장 완료 : {inserted}개")
    print(f"건너뜀 : {skipped}개")


if __name__ == "__main__":
    main()
