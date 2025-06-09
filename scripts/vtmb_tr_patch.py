import csv
from pathlib import Path
import argparse


def load_translations(csv_path):
    translations = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 2:
                english, turkish = row[0].strip(), row[1].strip()
                translations[english] = turkish
    return translations


def patch_file(original_path, translations, output_path):
    output_lines = []
    with open(original_path, encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            # Replace line if translation exists
            translated = translations.get(stripped)
            output_lines.append((translated + '\n') if translated else line)

    with open(output_path, 'w', encoding='utf-8') as f:
        for line in output_lines:
            f.write(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply Turkish translations to VTMB patch file")
    parser.add_argument("original", help="Path to the original text file from the patch")
    parser.add_argument("translations", help="CSV file containing English and Turkish text pairs")
    parser.add_argument("output", help="Path for the patched text file")
    args = parser.parse_args()

    translations = load_translations(args.translations)
    patch_file(args.original, translations, args.output)
