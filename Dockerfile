FROM python:3.9-alpine

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD flask run -h 0.0.0.0 -p 10000
