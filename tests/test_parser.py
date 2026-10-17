from app.services.parser import parse_text


def test_parser_handles_aliases_and_multiline_values():
    result = parse_text("""UNIT: Model X
APPLICANT DETAILS
LAST NAME: Doe
FIRST NAME: Jane
COMPLETE ADDRESS: 1 Main Street
Second floor
EMAIL ADDRESS: jane@example.com""")
    assert result.data.unit == "MODEL X"
    assert result.data.applicant.address == "1 MAIN STREET SECOND FLOOR"
    assert result.data.applicant.email == "jane@example.com"


def test_parser_reports_missing_identity():
    result = parse_text("UNIT: Model X")
    assert any("Applicant identity" in warning for warning in result.warnings)


def test_parser_corrects_application_format_and_maps_comaker_fields():
    result = parse_text("""BORROWER/PRIMARY
LAST NAME: Feliciano jr
BIRTHDATE: 2/26/1986
CELL #: 09690100549
TIN #: 242905879
EMAIL: ReyFeliciano1986@Gmail.com
HOME ADDRESS: Dalimag St, Purok 3
COBORROWER/COMAKER
RELATIONSHIP TO BORROWER: wife
CITIZENSHIP: filipino
OFC TEL: 09662587381""")

    assert result.data.applicant.last_name == "FELICIANO JR"
    assert result.data.applicant.birthday == "02/26/1986"
    assert result.data.applicant.contact_no == "0969 010 0549"
    assert result.data.applicant.tin_number == "242-905-879"
    assert result.data.applicant.email == "reyfeliciano1986@gmail.com"
    assert result.data.applicant.address == "DALIMAG ST, PUROK 3"
    assert result.data.spouse.relationship == "WIFE"
    assert result.data.spouse.citizenship == "FILIPINO"
    assert result.data.spouse.employment_contact_no == "0966 258 7381"


def test_parser_reports_unknown_field_labels():
    result = parse_text("NOT A REAL FIELD: value")
    assert any("Unrecognized field label" in warning for warning in result.warnings)
