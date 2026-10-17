from openpyxl import Workbook, load_workbook

from app.schemas.application import ApplicationData, Person
from app.services.excel_writer import inspect_workbook, write_application


def test_writer_preserves_template_and_writes_adjacent_label(tmp_path):
    template = tmp_path / "template.xlsx"
    workbook = Workbook()
    workbook.active["A1"] = "UNIT"
    workbook.active["B1"] = "existing"
    workbook.active["A2"] = "FIRST NAME"
    workbook.save(template)
    output = write_application(template, tmp_path / "generated", ApplicationData(unit="Model X", applicant=Person(first_name="Jane")))
    assert inspect_workbook(template)["sheets"] == ["Sheet"]
    assert load_workbook(output).active["B1"].value == "existing"


def test_writer_writes_to_top_left_cell_of_merged_destination(tmp_path):
    template = tmp_path / "template.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "UNIT"
    sheet.merge_cells("B1:C1")
    workbook.save(template)

    output = write_application(template, tmp_path / "generated", ApplicationData(unit="Model X"))

    assert load_workbook(output).active["B1"].value == "Model X"


def test_writer_skips_occupied_adjacent_label(tmp_path):
    template = tmp_path / "template.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "UNIT"
    sheet["B1"] = "MAKE/MODEL"
    sheet.merge_cells("B2:C2")
    workbook.save(template)

    output = write_application(template, tmp_path / "generated", ApplicationData(unit="Model X"))

    assert load_workbook(output).active["B2"].value == "Model X"


def test_writer_filters_words_and_separates_borrower_sections(tmp_path):
    template = tmp_path / "template.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "PRINCIPAL BORROWER"
    sheet["B1"] = "NAME OF EMPLOYER/BUSINESS"
    sheet["A5"] = "CO-MAKER"
    sheet["B5"] = "EMPLOYER/BUSINESS NAME"
    workbook.save(template)

    output = write_application(
        template,
        tmp_path / "generated",
        ApplicationData(
            applicant=Person(employment_name="Primary Employer"),
            spouse=Person(employment_name="Co-maker Employer"),
        ),
    )

    sheet = load_workbook(output).active
    assert sheet["C1"].value == "Primary Employer"
    assert sheet["C5"].value == "Co-maker Employer"
