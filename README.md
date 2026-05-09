# Fast Zero

## Sobre o Projeto
O Fast Zero é uma aplicação web desenvolvida com FastAPI. O projeto utiliza PostgreSQL como banco de dados relacional, SQLAlchemy como ORM, gerenciamento de migrações com Alembic e controle de dependências através do uv.

O projeto foi desenvolvido durante o[curso de Python do Dunossauro](https://fastapidozero.dunossauro.com). 

## Tecnologias Utilizadas
- Python 3.14
- FastAPI
- PostgreSQL
- SQLAlchemy & Alembic
- uv (Gerenciamento de dependências)
- Docker & Docker Compose
- pytest (Testes automatizados)
- ruff (Linting e formatação)
- taskipy (Automação de tarefas)

## Pré-requisitos
Para executar o projeto, certifique-se de ter instalado:
- Python 3.14
- uv
- Docker e Docker Compose (para instanciar o banco de dados e/ou executar a aplicação conteinerizada)

## Como Executar Localmente

1. Acesse o diretório raiz do projeto.

2. Instale as dependências com o uv:
```bash
uv sync
```

3. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis de ambiente:
```env
DATABASE_URL="postgresql+psycopg://app_user:app_password@localhost:5432/app_db"
SECRET_KEY="sua-chave-secreta"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES="30"
```
*(Nota: Para desenvolvimento local sem o Docker, você pode alterar o `DATABASE_URL` para `sqlite+aiosqlite:///database.db` e ignorar a próxima etapa).*

4. Inicie o banco de dados PostgreSQL usando o Docker Compose:
```bash
docker compose up fastzero_database -d
```

5. Execute as migrações do banco de dados para criar as tabelas necessárias:
```bash
uv run alembic upgrade head
```

6. Inicie o servidor de desenvolvimento:
```bash
uv run task run
```
A API estará acessível em: `http://localhost:8000`

## Como Executar via Docker

Para rodar o ambiente completo (API + Banco de Dados) apenas com Docker:

1. Na raiz do projeto, execute o seguinte comando:
```bash
docker compose up --build
```

O contêiner da aplicação automaticamente executará as migrações necessárias e iniciará o servidor. O serviço também estará disponível na porta 8000.

## Como Executar os Testes e Tarefas

O projeto utiliza o `taskipy` para facilitar a execução de comandos frequentes. 

Para rodar os testes (com cobertura de código):
```bash
uv run task test
```

Para checar erros de tipografia (typos) e executar o linter (ruff):
```bash
uv run task lint
```

Para formatar o código de acordo com o padrão do projeto:
```bash
uv run task format
```
