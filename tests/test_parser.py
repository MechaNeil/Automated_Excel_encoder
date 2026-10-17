from app.services.parser import parse_text


def test_parser_handles_aliases_and_multiline_values():
    result = parse_text("""UNIT: Model X
APPLICANT DETAILS
LAST NAME: Doe
FIRST NAME: Jane
COMPLETE ADDRESS: 1 Main Street
Second floor
EMAIL ADDRESS: jane@example.com""")
    assert result.data.unit == "Model X"
    assert result.data.applicant.address == "1 Main Street Second floor"
    assert result.data.applicant.email == "jane@example.com"


def test_parser_reports_missing_identity():
    result = parse_text("UNIT: Model X")
    assert any("Applicant identity" in warning for warning in result.warnings)
