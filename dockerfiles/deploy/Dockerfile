FROM python:3.12-alpine

WORKDIR /app

COPY ./requirements /app/requirements

RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev

RUN pip install --no-cache-dir --upgrade -r /app/requirements/base.txt && \
  pip install --no-cache-dir -r /app/requirements/local.txt

COPY . /app

RUN chmod +x /app/run.sh

EXPOSE 8000

CMD ["./run.sh"]
