FROM python:3
WORKDIR /tg_bot
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "python", "main.py", "--host=0.0.0.0"]
