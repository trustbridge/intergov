FROM python:3.6

# don't create __pycache__ files
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /src

# copy all source code in (cwd must be the root of the repo)
COPY ./ .
RUN pip install -r requirements/test.txt
