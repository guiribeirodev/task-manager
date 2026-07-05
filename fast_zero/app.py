from http import HTTPStatus

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from fast_zero.routers import auth, todos, users
from fast_zero.schemas import Message

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(todos.router)


class MessageIn(BaseModel):
    user_id: int
    text: str


@app.post('/messages')
async def receive_message(payload: MessageIn):
    return {'reply': f'Recebi: {payload.text}'}


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
async def read_root():
    return {'message': 'Olá Mundo!'}


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
