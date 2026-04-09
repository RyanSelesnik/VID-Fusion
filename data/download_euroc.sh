#!/bin/bash
# Download EuRoC MAV dataset sequences.
#
# Usage:
#   bash data/download_euroc.sh           # download and extract all Machine Hall sequences
#   bash data/download_euroc.sh MH_01     # download a specific sequence only
#
# Source: https://www.research-collection.ethz.ch/entities/researchdata/bcaf173e-5dac-484b-bc37-faf97a594f1f

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ZIP="$SCRIPT_DIR/euroc_mh.zip"

MACHINE_HALL_URL="https://www.research-collection.ethz.ch/bitstreams/7b2419c1-62b5-4714-b7f8-485e5fe3e5fe/download"

SEQUENCES=(
  machine_hall/MH_01_easy/MH_01_easy.bag
  machine_hall/MH_02_easy/MH_02_easy.bag
  machine_hall/MH_03_medium/MH_03_medium.bag
  machine_hall/MH_04_difficult/MH_04_difficult.bag
  machine_hall/MH_05_difficult/MH_05_difficult.bag
)

# Filter by argument if provided
if [ -n "$1" ]; then
  SEQUENCES=($(printf '%s\n' "${SEQUENCES[@]}" | grep "$1"))
  if [ ${#SEQUENCES[@]} -eq 0 ]; then
    echo "ERROR: no sequence matching '$1'. Available: MH_01 MH_02 MH_03 MH_04 MH_05"
    exit 1
  fi
fi

# Download ZIP if not already present
if [ ! -f "$ZIP" ]; then
  echo "Downloading Machine Hall ZIP (~12 GB)..."
  curl -L --progress-bar -o "$ZIP" "$MACHINE_HALL_URL"
else
  echo "Found existing $ZIP, skipping download."
fi

# Extract requested sequences
for SEQ in "${SEQUENCES[@]}"; do
  BAG="$SCRIPT_DIR/$SEQ"
  if [ -f "$BAG" ]; then
    echo "Already exists: $BAG"
    continue
  fi
  echo "Extracting $SEQ..."
  python3 -c "
import zipfile, os
z = zipfile.ZipFile('$ZIP')
z.extract('$SEQ', '$SCRIPT_DIR')
print('Extracted: $BAG')
"
done

echo "Done. Bags available in $SCRIPT_DIR/machine_hall/"
