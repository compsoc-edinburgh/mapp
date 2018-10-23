FROM python:2.7

RUN apt-get update -y && \
    apt-get install -y libldap2-dev libsasl2-dev

ADD ./requirements.txt /code/requirements.txt
WORKDIR /code

RUN pip install -r requirements.txt

ADD . /code

EXPOSE 9000

CMD ["python", "run.py"]
