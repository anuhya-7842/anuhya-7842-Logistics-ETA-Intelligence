
import hashlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def calculate_checksums():
    checksums = {}

    for file_path in sorted(DATA_DIR.glob("*.csv")):
        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        checksums[file_path.name] = file_hash

    return checksums


def main():
    print("\n========== REPRODUCIBILITY VERIFICATION ==========\n")

    print("Generating datasets for the first run...")
    subprocess.run(
        [sys.executable, "-m", "src.generator"],
        cwd=PROJECT_ROOT,
        check=True
    )
    first_run = calculate_checksums()

    print("\nGenerating datasets for the second run...")
    subprocess.run(
        [sys.executable, "-m", "src.generator"],
        cwd=PROJECT_ROOT,
        check=True
    )
    second_run = calculate_checksums()

    if first_run == second_run:
        print("\nPASS: All generated CSV files are reproducible.")
        print(f"Verified files: {len(first_run)}")
    else:
        print("\nFAIL: Dataset checksums do not match.")

        for filename in sorted(set(first_run) | set(second_run)):
            if first_run.get(filename) != second_run.get(filename):
                print(f"MISMATCH: {filename}")

        sys.exit(1)

    print("\n========== VERIFICATION COMPLETED ==========\n")


if __name__ == "__main__":
    main()
