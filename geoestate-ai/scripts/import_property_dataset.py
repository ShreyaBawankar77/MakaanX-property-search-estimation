from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "backend" / "data" / "properties.csv"
REQUIRED_COLUMNS = {"Price", "Area", "Location", "City", "No. of Bedrooms", "Resale"}
AMENITY_COLUMNS = [
    "Gymnasium",
    "SwimmingPool",
    "LandscapedGardens",
    "JoggingTrack",
    "RainWaterHarvesting",
    "IndoorGames",
    "ShoppingMall",
    "Intercom",
    "SportsFacility",
    "ClubHouse",
    "School",
    "24X7Security",
    "PowerBackup",
    "CarParking",
    "Hospital",
    "Children'splayarea",
    "LiftAvailable",
]


def import_dataset(archive_path: Path) -> pd.DataFrame:
    with ZipFile(archive_path) as archive:
        csv_members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(csv_members) != 1:
            raise ValueError(f"Expected one CSV in the archive; found {len(csv_members)}.")
        with archive.open(csv_members[0]) as source:
            source_df = pd.read_csv(source)

    missing_columns = REQUIRED_COLUMNS.difference(source_df.columns)
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing_columns))}")

    price = pd.to_numeric(source_df["Price"], errors="coerce")
    area = pd.to_numeric(source_df["Area"], errors="coerce")
    bedrooms = pd.to_numeric(source_df["No. of Bedrooms"], errors="coerce")
    valid = (
        price.gt(0)
        & area.gt(0)
        & bedrooms.gt(0)
        & source_df["Location"].notna()
        & source_df["City"].notna()
    )
    source_df = source_df.loc[valid].copy()

    city = source_df["City"].astype(str).str.strip().replace({"Bangalore": "Bengaluru"})
    amenities = source_df.reindex(columns=AMENITY_COLUMNS, fill_value=0).apply(
        lambda row: ", ".join(column for column, value in row.items() if pd.to_numeric(value, errors="coerce") == 1),
        axis=1,
    )
    imported = pd.DataFrame(
        {
            "property_id": [f"source-{index:05d}" for index in source_df.index],
            "city": city,
            "locality": source_df["Location"].astype(str).str.strip(),
            "bhk": bedrooms.loc[source_df.index].astype(int),
            "area_sqft": area.loc[source_df.index].astype(float),
            "listing_price": price.loc[source_df.index].astype(float),
            "actual_price": price.loc[source_df.index].astype(float),
            "resale": pd.to_numeric(source_df["Resale"], errors="coerce").fillna(0).astype(int),
            "amenities": amenities,
            "image_url": "",
        }
    ).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    imported.to_csv(OUTPUT_PATH, index=False)
    return imported


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize the supplied property dataset for MakaanX.")
    parser.add_argument("archive", type=Path, help="ZIP containing the source properties CSV")
    args = parser.parse_args()
    frame = import_dataset(args.archive)
    print(f"Imported {len(frame)} rows into {OUTPUT_PATH}")
    print(frame["city"].value_counts().to_string())