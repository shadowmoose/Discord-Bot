FROM python:3

ADD shadowbot ./shadowbot/
ADD requirements.txt ./

RUN pip install -r ./requirements.txt

RUN ls

ENTRYPOINT [ "python", "-u", "./shadowbot/"]
