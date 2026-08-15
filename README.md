# Courses service

A small FastAPI service with a browser-based panel for managing courses, lesson
JSON data, course assignment, lesson order, and automatic next-lesson links.

## Database

The service uses the shared PostgreSQL database managed by
`../bricks/docker-compose.yml`. Start it first:

```bash
cd ../bricks
docker compose up -d db seeder
cd ../courses_service
```

The service automatically loads `courses_service/.env`, even when it is
started from another working directory. It reads `DATABASE_URL` when provided;
otherwise it builds the connection from `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB`, `POSTGRES_HOST`, and `POSTGRES_PORT`. Variables supplied by the
process or container take precedence over values in `.env`.

## Run

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

Open <http://127.0.0.1:8000>. API documentation is available at
<http://127.0.0.1:8000/docs>.

## Run with Docker

Start the Bricks database first, then build and run this service:

```bash
cd ../bricks
docker compose up -d db seeder

cd ../courses_service
docker compose up --build
```

The container joins the external `junkie_net` network and connects to the
PostgreSQL service at `db:5432`. Open the panel at
<http://127.0.0.1:8002> and its API documentation at
<http://127.0.0.1:8002/docs>.
