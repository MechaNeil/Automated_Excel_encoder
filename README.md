# Credit Application Encoder

Dockerized FastAPI application for extracting client application text, reviewing normalized fields, and writing a completed copy of a supplied Excel template.

## Run locally

Place the original workbook at `excel_templates/CREDIT APPLICATION - Sample.xlsx`, then run `docker compose up --build`.

Open http://localhost:8000. Generated files are written to `generated/`.

## Test

Install dependencies with `python -m pip install -r requirements.txt`, then run `pytest -q`.

## Template inspection and limitations

The current workspace did not contain the supplied workbook, so no claim is made about its worksheets, merged cells, formulas, validations, drawings, print settings, or field destinations. The `/health` endpoint reports the discovered workbook structure when the real file is mounted. The writer scans each worksheet for verified label text and writes to the adjacent cell; it refuses to produce output when no recognized labels are found. Before production use, add the original workbook and inspect `/health`, then visually review a generated copy. `openpyxl` preserves ordinary workbook structures but may not preserve every Excel drawing or advanced feature; LibreOffice/Excel round-trip validation should be performed if those features are present.
