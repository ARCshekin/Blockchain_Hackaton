from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

ORGANIZATIONS = [
    {"id": "redcross", "name": "Красный Крест"},
    {"id": "wwf", "name": "Всемирный фонд дикой природы"},
    {"id": "unicef", "name": "Детский фонд ООН"},
    {"id": "doctors", "name": "Врачи без границ"},
]

@app.get("/donate", response_class=HTMLResponse)
async def donation_interface(request: Request, user_id: int):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_id": user_id,
        "organizations": ORGANIZATIONS,
    })
