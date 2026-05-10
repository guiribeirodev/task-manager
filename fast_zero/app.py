from http import HTTPStatus
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from fast_zero.routers import auth, todos, users
from fast_zero.schemas import Message

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / 'frontend'

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(todos.router)
app.mount('/static', StaticFiles(directory=FRONTEND_DIR), name='static')


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
async def read_root():
    return {'message': 'Olá Mundo!'}


@app.get('/app', response_class=HTMLResponse)
async def read_frontend():
    return (FRONTEND_DIR / 'index.html').read_text(encoding='utf-8')


@app.get('/exercicio-html', response_class=HTMLResponse)
async def hello_world():
    return """
    <html>
      <head>
        <title>Nosso olá mundo!</title>
      </head>
      <body>
        <h1> Olá Mundo </h1>
      </body>
    </html>"""
