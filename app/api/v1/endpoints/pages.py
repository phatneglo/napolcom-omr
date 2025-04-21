"""
Page routing for the web interface
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter()

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Home page / dashboard
    """
    return templates.TemplateResponse("dashboard/index.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """
    Login page
    """
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Registration page
    """
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.get("/templates", response_class=HTMLResponse)
async def templates_page(request: Request):
    """
    Templates management page
    """
    return templates.TemplateResponse("templates/index.html", {"request": request})


@router.get("/templates/{template_id}", response_class=HTMLResponse)
async def template_detail(request: Request, template_id: int):
    """
    Template detail page
    """
    return templates.TemplateResponse(
        "templates/detail.html", 
        {"request": request, "template_id": template_id}
    )


@router.get("/templates/{template_id}/edit", response_class=HTMLResponse)
async def template_edit(request: Request, template_id: int):
    """
    Template editor page
    """
    return templates.TemplateResponse(
        "templates/edit.html", 
        {"request": request, "template_id": template_id}
    )


@router.get("/templates/new", response_class=HTMLResponse)
async def template_new(request: Request):
    """
    New template page
    """
    return templates.TemplateResponse("templates/new.html", {"request": request})


@router.get("/training/datasets", response_class=HTMLResponse)
async def datasets_page(request: Request):
    """
    Datasets management page
    """
    return templates.TemplateResponse("training/datasets.html", {"request": request})


@router.get("/training/datasets/{dataset_id}", response_class=HTMLResponse)
async def dataset_detail(request: Request, dataset_id: int):
    """
    Dataset detail page
    """
    return templates.TemplateResponse(
        "training/dataset_detail.html", 
        {"request": request, "dataset_id": dataset_id}
    )


@router.get("/training/generate", response_class=HTMLResponse)
async def dataset_generate(request: Request):
    """
    Dataset generation page
    """
    return templates.TemplateResponse("training/generate.html", {"request": request})


@router.get("/training/models", response_class=HTMLResponse)
async def models_page(request: Request):
    """
    Models management page
    """
    return templates.TemplateResponse("training/models.html", {"request": request})


@router.get("/training/models/{model_id}", response_class=HTMLResponse)
async def model_detail(request: Request, model_id: int):
    """
    Model detail page
    """
    return templates.TemplateResponse(
        "training/model_detail.html", 
        {"request": request, "model_id": model_id}
    )


@router.get("/training/new", response_class=HTMLResponse)
async def model_new(request: Request):
    """
    New model training page
    """
    return templates.TemplateResponse("training/new.html", {"request": request})


@router.get("/processing/forms", response_class=HTMLResponse)
async def forms_page(request: Request):
    """
    Processed forms management page
    """
    return templates.TemplateResponse("processing/forms.html", {"request": request})


@router.get("/processing/forms/{form_id}", response_class=HTMLResponse)
async def form_detail(request: Request, form_id: int):
    """
    Form detail page
    """
    return templates.TemplateResponse(
        "processing/form_detail.html", 
        {"request": request, "form_id": form_id}
    )


@router.get("/processing/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    """
    Form upload page
    """
    return templates.TemplateResponse("processing/upload.html", {"request": request})


@router.get("/processing/queue", response_class=HTMLResponse)
async def processing_queue(request: Request):
    """
    Processing queue page
    """
    return templates.TemplateResponse("processing/queue.html", {"request": request})


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """
    Analytics page
    """
    return templates.TemplateResponse("analytics/index.html", {"request": request})


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """
    User profile page
    """
    return templates.TemplateResponse("user/profile.html", {"request": request})


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """
    Settings page
    """
    return templates.TemplateResponse("user/settings.html", {"request": request})
