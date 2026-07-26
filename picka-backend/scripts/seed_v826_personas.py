from pathlib import Path

from scripts import persona_seed_importer as importer


importer.CSV_PATH = (
    Path(__file__).resolve().parents[1]
    / "PICKA_persona_all_in_one_v8_26_jeongeunju_budget450_pick45.csv"
)
importer.SOURCE_VERSION = "v8_26_jeongeunju_budget450_pick45"
importer.CONSUMPTION_TENDENCY_SOURCE = "PICKA_페르소나_소비성향_정리.xlsx"
importer.BENEFIT_ID_REFERENCE_CSV = None


if __name__ == "__main__":
    importer.main()
