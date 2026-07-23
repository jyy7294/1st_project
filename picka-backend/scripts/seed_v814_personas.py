from pathlib import Path

from scripts import seed_v811_personas as importer


importer.CSV_PATH = (
    Path(__file__).resolve().parents[1]
    / "PICKA_persona_all_in_one_v8_14_smoothed_monthly_spend.csv"
)
importer.SOURCE_VERSION = "v8_14_smoothed_monthly_spend"


if __name__ == "__main__":
    importer.main()
