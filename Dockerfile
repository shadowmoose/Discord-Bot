FROM python:3

ADD shadowbot ./shadowbot/
ADD requirements.txt ./

RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "-u", "./shadowbot/"]
