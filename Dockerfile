FROM python:3.9

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY . /qm

COPY ./requirements.txt /
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /opt/qm_tokens

WORKDIR /qm/qm

CMD ["python", "main.py"]
