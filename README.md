# Credit Application Encoder

Dockerized FastAPI application for extracting client application text, reviewing normalized fields, and writing a completed copy of a supplied Excel template.

## Run locally

Place the original workbook at `excel_templates/CREDIT APPLICATION - Sample.xlsx`, then run `docker compose up --build`.

Open http://localhost:8000. Generated files are written to `generated/`.

## Excel encoding architecture

The API depends on the `ExcelEncoder` port in `app/services/excel_encoder.py`. The default adapter, `OpenPyXLTemplateEncoder`, loads the supplied workbook template, resolves labels through `TemplateFieldLocator`, and saves a generated copy. `openpyxl` is intentional here because the application edits an existing `.xlsx` template and must retain merged-cell destinations. A future encoder can implement the same port without changing the API layer.

## Test

Install dependencies with `python -m pip install -r requirements.txt`, then run `pytest -q`.

## Template inspection and limitations

The current workspace did not contain the supplied workbook, so no claim is made about its worksheets, merged cells, formulas, validations, drawings, print settings, or field destinations. The `/health` endpoint reports the discovered workbook structure when the real file is mounted. The writer scans each worksheet for verified label text and writes to the adjacent cell; it refuses to produce output when no recognized labels are found. Before production use, add the original workbook and inspect `/health`, then visually review a generated copy. `openpyxl` preserves ordinary workbook structures but may not preserve every Excel drawing or advanced feature; LibreOffice/Excel round-trip validation should be performed if those features are present.
