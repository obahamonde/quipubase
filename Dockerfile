FROM python:3.10

WORKDIR /app

COPY . .

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

ENV PORT=5454


RUN apt-get update && apt-get install -y \
	librocksdb-dev \
	&& rm -rf /var/lib/apt/lists/*

RUN cd quipubase && pip install cython && python setup.py  build_ext --inplace

EXPOSE 5454

RUN pip install -r requirements.txt

CMD ["uvicorn","main:app","--host","0.0.0.0","--port","5454"]