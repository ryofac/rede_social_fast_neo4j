FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache bash gcc musl-dev libffi-dev postgresql-dev

COPY ./requirements /app/requirements

RUN pip install --no-cache-dir --upgrade -r /app/requirements/base.txt

COPY . /app


CMD ["fastapi", "run", "finn/main.py", "--port", "8000", "--host", "0.0.0.0"]
