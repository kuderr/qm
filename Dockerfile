FROM python:3.8

COPY ./qm /queue_manager
COPY ./requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

CMD ["python", "/queue_manager/main.py"]
