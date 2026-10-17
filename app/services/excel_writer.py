from datetime import datetime
from pathlib import Path
import re

from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell

from app.schemas.application import ApplicationData
from app.services.field_map import FIELD_ALIASES


EXPLICIT_DESTINATIONS = {
    "applicant": {"age": "K8"},
    "spouse": {"age": "K22"},
}


def inspect_workbook(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    workbook = load_workbook(path, data_only=False)
    return {
        "exists": True,
        "sheets": workbook.sheetnames,
        "merged_ranges": {sheet.title: [str(item) for item in sheet.merged_cells.ranges] for sheet in workbook.worksheets},
        "hidden_sheets": [sheet.title for sheet in workbook.worksheets if sheet.sheet_state != "visible"],
        "defined_names": list(workbook.defined_names),
    }


def _label_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _label_tokens(value: object) -> set[str]:
    tokens = set(_label_key(value).split())
    tokens.discard("of")
    if "employment" in tokens:
        tokens.remove("employment")
        tokens.add("employer")
    return tokens


def _section_rows(sheet, section: str) -> tuple[int, int] | None:
    markers = {"applicant": "principal borrower", "spouse": "co maker"}
    marker_rows = {
        marker: cell.row
        for row in sheet.iter_rows()
        for cell in row
        if (marker := _label_key(cell.value)) in markers.values()
    }
    if len(marker_rows) < 2:
        return None
    principal_row = marker_rows["principal borrower"]
    comaker_row = marker_rows["co maker"]
    return (principal_row, comaker_row - 1) if section == "applicant" else (comaker_row, sheet.max_row)


def _label_matches(value: object, field: str) -> bool:
    label_tokens = _label_tokens(value)
    return any(
        _label_key(alias) == _label_key(value)
        or _label_tokens(alias).issubset(label_tokens)
        for alias in FIELD_ALIASES[field]
    )


def _explicit_destination(sheet, field: str, section: str | None = None):
    coordinate = EXPLICIT_DESTINATIONS.get(section or "", {}).get(field)
    if not coordinate:
        return None
    for merged_range in sheet.merged_cells.ranges:
        if coordinate == merged_range.start_cell.coordinate:
            return sheet[coordinate]
    return None


def _find_destination(sheet, field: str, section: str | None = None):
    row_bounds = _section_rows(sheet, section) if section else None
    if field == "monthly_income" and section:
        income_row = {"applicant": 35, "spouse": 36}[section]
        for cell in sheet[income_row]:
            if _label_matches(cell.value, field):
                for merged_range in sheet.merged_cells.ranges:
                    if cell.coordinate in merged_range:
                        destination = sheet.cell(merged_range.min_row, merged_range.max_col + 1)
                        if not isinstance(destination, MergedCell):
                            return destination
                return sheet.cell(cell.row, cell.column + 1)
    for row in sheet.iter_rows():
        for cell in row:
            if row_bounds and not row_bounds[0] <= cell.row <= row_bounds[1]:
                continue
            if _label_matches(cell.value, field):
                destination = sheet.cell(cell.row, cell.column + 1)
                if isinstance(destination, MergedCell):
                    for merged_range in sheet.merged_cells.ranges:
                        if destination.coordinate in merged_range:
                            if merged_range.min_col == cell.column:
                                destination = sheet.cell(merged_range.max_row + 1, merged_range.min_col)
                            else:
                                destination = sheet.cell(merged_range.min_row, merged_range.min_col)
                            break
                if not destination.value and not isinstance(destination, MergedCell):
                    return destination
                if destination.value and _label_matches(destination.value, field):
                    for row_number in range(destination.row + 1, sheet.max_row + 1):
                        candidate = sheet.cell(row_number, destination.column)
                        if not isinstance(candidate, MergedCell) and not candidate.value:
                            return candidate
    return None


def write_application(template_path: Path, output_dir: Path, data: ApplicationData) -> Path:
    if not template_path.exists():
        raise FileNotFoundError(f"Excel template not found: {template_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    workbook = load_workbook(template_path)
    values = {"unit": data.unit, "color_first": data.color_first, "color_second": data.color_second}
    for prefix, person in (("applicant", data.applicant), ("spouse", data.spouse)):
        values.update({f"{prefix}.{name}": value for name, value in person.model_dump().items() if name in FIELD_ALIASES})
    written = 0
    for key, value in values.items():
        field = key.split(".")[-1]
        if not value or field not in FIELD_ALIASES:
            continue
        for sheet in workbook.worksheets:
            section = key.split(".")[0] if "." in key else None
            destination = _explicit_destination(sheet, field, section)
            if destination is None:
                destination = _find_destination(sheet, field, section)
            if destination:
                destination.value = value
                written += 1
                break
    if not written:
        raise ValueError("No recognized template labels were found; refusing to generate an unmapped workbook.")
    output = output_dir / f"credit_application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    workbook.save(output)
    return output
