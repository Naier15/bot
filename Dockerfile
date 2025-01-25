FROM python:3.11
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN pip install -U pip
RUN pip install pipenv

COPY Pipfile* .
RUN pipenv sync

CMD pipenv run python main.py