FROM python:3.9-alpine

WORKDIR /app

COPY requirements.txt .

RUN apk update && \
    apk add --no-cache gcc musl-dev linux-headers

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

CMD ["python3", "-m", "Adarsh"]
