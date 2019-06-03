FROM python:3-alpine

LABEL maintainer "Micael Carlstedt"

ENV DOMAIN_NAME=''
ENV RECORD_NAMES=''
ENV API_KEY=''
ENV API_SECRET=''

COPY requirements.txt /
COPY app.py /

WORKDIR /
RUN pip install -r requirements.txt

CMD python -u /app.py --domainname ${DOMAIN_NAME} --record_names ${RECORD_NAMES} --key ${API_KEY} --secret ${API_SECRET}
