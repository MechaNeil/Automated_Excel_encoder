from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = Path(os.getenv("TEMPLATE_PATH", BASE_DIR / "excel_templates" / "CREDIT APPLICATION -  Sample.xlsx"))
GENERATED_DIR = Path(os.getenv("GENERATED_DIR", BASE_DIR / "generated"))
