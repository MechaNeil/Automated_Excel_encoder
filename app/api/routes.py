from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import GENERATED_DIR, TEMPLATE_PATH
from app.schemas.application import GenerateRequest, ParseRequest
from app.services.excel_writer import inspect_workbook, write_application
from app.services.parser import parse_text
from app.services.validators import normalize_application, validate_application

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "template_available": TEMPLATE_PATH.exists()})


@router.post("/api/parse")
async def parse(request: ParseRequest):
    response = parse_text(request.raw_text)
    response.warnings.extend(validate_application(response.data))
    return response


@router.get("/review", response_class=HTMLResponse)
async def review(request: Request):
    return templates.TemplateResponse("review.html", {"request": request})


@router.post("/api/generate")
async def generate(request: GenerateRequest):
    try:
        data = normalize_application(request.data)
        issues = validate_application(data)
        if issues:
            raise HTTPException(status_code=422, detail=issues)
        output = write_application(TEMPLATE_PATH, GENERATED_DIR, data)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"filename": output.name, "download_url": f"/api/download/{output.name}"}


@router.get("/api/download/{filename}")
async def download(filename: str):
    candidate = (GENERATED_DIR / filename).resolve()
    if candidate.parent != GENERATED_DIR.resolve() or not candidate.exists():
        raise HTTPException(status_code=404, detail="Generated workbook not found.")
    return FileResponse(candidate, filename=candidate.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/health")
async def health():
    return {"status": "ok", "template": inspect_workbook(TEMPLATE_PATH)}
