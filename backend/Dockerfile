FROM ghcr.io/astral-sh/uv:0.11.28@sha256:0f36cb9361a3346885ca3677e3767016687b5a170c1a6b88465ec14aefec90aa AS uv
FROM python:3.11.15-slim-bookworm@sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3 AS dependencies
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./
COPY backend/vendor/referencing-0.37.0+cg.1-py3-none-any.whl /app/vendor/referencing-0.37.0+cg.1-py3-none-any.whl
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy
RUN uv sync --locked --no-dev --python /usr/local/bin/python \
    && .venv/bin/python -c "import fastapi,httpx,jsonschema,pydantic,uvicorn,sqlite3; from importlib.metadata import version; from referencing import Resource; from referencing.jsonschema import DRAFT3,DRAFT4; assert version('jsonschema') == '4.26.0'; assert version('referencing') == '0.37.0+cg.1'; child={'type':'string'}; assert [r.contents for r in Resource.from_contents({'extends':child}, default_specification=DRAFT3).subresources()] == [child]; assert [r.contents for r in Resource.from_contents({'extends':[child]}, default_specification=DRAFT3).subresources()] == [child]; assert [r.contents for r in Resource.from_contents({'allOf':[child]}, default_specification=DRAFT4).subresources()] == [child]; print('SQLite',sqlite3.sqlite_version,'jsonschema',version('jsonschema'),'referencing',version('referencing'))"

FROM python:3.11.15-slim-bookworm@sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3
RUN groupadd --gid 10001 cognitive \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin cognitive \
    && mkdir /data && chown 10001:10001 /data && chmod 700 /data
WORKDIR /app
COPY --from=dependencies /app/.venv /app/.venv
COPY backend/app /app/app
ENV PATH=/app/.venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CG_DATA_DIR=/data WEB_CONCURRENCY=1
USER 10001:10001
EXPOSE 8000
STOPSIGNAL SIGTERM
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--timeout-graceful-shutdown", "30", "--no-access-log"]
