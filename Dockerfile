FROM python:2.7

RUN apt-get update -y && \
    apt-get install -y libldap2-dev libsasl2-dev

ADD ./requirements.txt /code/requirements.txt
WORKDIR /code

RUN pip install -r requirements.txt

ADD . /code

CMD ["python", "run_debug.py"]
