FROM python:3.10.8

ENV BOT_TOKEN=""
ENV SERVER_GUID=""
ENV GAME=""

RUN groupadd -r discordbot && useradd --no-log-init -r -g discordbot discordbot

WORKDIR /home/discordbot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

USER discordbot:discordbot

COPY main.py ./

CMD [ "python", "./main.py" ]