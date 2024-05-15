FROM python:3.10

WORKDIR /app

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


RUN apt-get update && apt-get install -y \
	chromium \
	chromium-driver \
	&& rm -rf /var/lib/apt/lists/*


RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn","main:app","--port 5454","--host","0.0.0.0"]