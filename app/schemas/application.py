from pydantic import BaseModel, ConfigDict, Field


class Person(BaseModel):
    model_config = ConfigDict(extra="allow")

    last_name: str = ""
    first_name: str = ""
    middle_name: str = ""
    birthday: str = ""
    citizenship: str = ""
    birth_place: str = ""
    age: str = ""
    address: str = ""
    length_of_stay: str = ""
    housing_status: str = ""
    civil_status: str = ""
    email: str = ""
    contact_no: str = ""
    home_tel: str = ""
    relationship: str = ""
    main_bank: str = ""
    bank_branch: str = ""
    employment_name: str = ""
    position: str = ""
    employment_address: str = ""
    employment_contact_no: str = ""
    years_of_service: str = ""
    monthly_income: str = ""
    employment_email: str = ""
    bank_depositor: str = ""
    tin_number: str = ""


class ApplicationData(BaseModel):
    model_config = ConfigDict(extra="allow")

    unit: str = ""
    color_first: str = ""
    color_second: str = ""
    applicant: Person = Field(default_factory=Person)
    spouse: Person = Field(default_factory=Person)


class ParseRequest(BaseModel):
    raw_text: str = Field(min_length=1)


class ParseResponse(BaseModel):
    data: ApplicationData
    warnings: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    source_values: dict[str, str] = Field(default_factory=dict)


class GenerateRequest(BaseModel):
    data: ApplicationData
