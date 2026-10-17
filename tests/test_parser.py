from app.services.parser import parse_text
from app.services.validators import validate_application


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


def test_parser_accepts_application_title_labels():
    result = parse_text("APPLICATION FORM: online application")
    assert not any("Unrecognized field label" in warning for warning in result.warnings)


def test_parser_handles_hash_labels_and_raw_client_field_variants():
    result = parse_text("""BORROWER/PRIMARY
CITIZENSHIP: Filipino
Cell # 09690100549
Tin # 242 905 879
Year of stay: 8yrs
Employer/Business name: BIPO Service Philippines Inc.
Employer/Business address: 10F Rockwell
COBORROWER/COMAKER
Employer/Business name: Great Vission Academy""")

    assert result.data.applicant.citizenship == "FILIPINO"
    assert result.data.applicant.contact_no == "0969 010 0549"
    assert result.data.applicant.tin_number == "242-905-879"
    assert result.data.applicant.length_of_stay == "8YRS"
    assert result.data.applicant.employment_name == "BIPO SERVICE PHILIPPINES INC."
    assert result.data.spouse.employment_name == "GREAT VISSION ACADEMY"


def test_parser_accepts_mixed_case_and_common_human_label_variants():
    result = parse_text("""APPLICATION DETAILS
FIRST NAME: Eddie
Middle name: Boy
Last Name: Padilla
Home Add.: 30 Alley B, Manila
Cellphone number: 09653766533
Date of Birth: Dec. 30 1990
type of ownership: owned
EMPLOYERS NAME: Urduja
Employers Add: Marikina
Year in Stay: 5 years
TIN no.: 266-052-445-000
CO-MAKER DETAILS
first Name: Edlyn Joy
CP Number: 09663191076
""")

    assert result.data.applicant.first_name == "EDDIE"
    assert result.data.applicant.middle_name == "BOY"
    assert result.data.applicant.last_name == "PADILLA"
    assert result.data.applicant.address == "30 ALLEY B, MANILA"
    assert result.data.applicant.contact_no == "0965 376 6533"
    assert result.data.applicant.birthday == "12/30/1990"
    assert result.data.applicant.housing_status == "OWNED"
    assert result.data.applicant.employment_name == "URDUJA"
    assert result.data.applicant.employment_address == "MARIKINA"
    assert result.data.applicant.years_of_service == "5YRS"
    assert result.data.applicant.tin_number == "266-052-445-000"
    assert result.data.spouse.first_name == "EDLYN JOY"
    assert result.data.spouse.contact_no == "0966 319 1076"
    assert validate_application(result.data) == []


def test_parser_accepts_business_and_unit_application_variants():
    result = parse_text("""Borrower Details
First: Lucio
Middle: Lampayan
Surname: Pacate jr
Inplace of birth: Sogod Southern Leyte
Type of Ownership: Rent
Mobile #: 0916 399 6759
Bank/Branch: BDO
TIN#: 
Email Add: pacatelucio@gmail.com
Unit Model: Kia Sonet LX MT
Co-Maker
First name: Jonalyn
Middle name: Ursulun
Surname: Pacate
Employers Name: Hypermove Transport Inc
Employers Add.: 1832 Oroquieta St, Sta Cruz, Manila
Position: Driver/Operator
Year in Stay: 2 yrs
Monthly Income: 32k
""")

    assert result.data.applicant.first_name == "LUCIO"
    assert result.data.applicant.birth_place == "SOGOD SOUTHERN LEYTE"
    assert result.data.applicant.housing_status == "RENT"
    assert result.data.applicant.contact_no == "0916 399 6759"
    assert result.data.unit == "KIA SONET LX MT"
    assert result.data.spouse.first_name == "JONALYN"
    assert result.data.spouse.employment_name == "HYPERMOVE TRANSPORT INC"
    assert result.data.spouse.years_of_service == "2YRS"
