FROM python:3.11

WORKDIR /app

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


RUN apt-get update && apt-get install -y \
	librocksdb-dev \
	&& rm -rf /var/lib/apt/lists/*

EXPOSE 5454

RUN pip install --no-cache-dir -r requirements.txt

CMD ["make"]