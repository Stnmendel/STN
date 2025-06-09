# AetherAI Demo

This repository contains a simple Flask web application demonstrating an AI assistant called **AetherAI**. The application includes a basic chat interface and a placeholder subscription check.

## Running the app

1. Install dependencies:
   ```bash
   pip install flask
   ```
2. Start the server:
   ```bash
   python app.py
   ```
3. Open `http://localhost:5000` in your browser.

A single demo user `demo@example.com` is subscribed by default. Integrate your own subscription and AI logic as needed.

## Creating a VTMB Turkish Patch

The `scripts/vtmb_tr_patch.py` script applies Turkish translations to a text
file from the VTMB Unofficial Patch. Provide a CSV file with English and Turkish
phrases and run:

```bash
python scripts/vtmb_tr_patch.py path/to/original.txt scripts/sample_translations.csv patched.txt
```

The example `scripts/sample_translations.csv` demonstrates the CSV format. The
script replaces any matching English lines in the original file with their
Turkish equivalents and writes the result to `patched.txt`.
