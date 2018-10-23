FROM python:2.7

RUN apt-get update -y && \
    apt-get install -y libldap2-dev libsasl2-dev
RUN pip install pipenv

WORKDIR /code
ADD ./Pipfile.lock /code/Pipfile.lock
ADD ./Pipfile /code/Pipfile

RUN pipenv install --system --deploy

ADD . /code

EXPOSE 9000

CMD ["python", "run.py"]
