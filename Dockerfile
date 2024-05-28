FROM python:3.9

WORKDIR /app

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5454
ENV ROCKSDB_VERSION=7.8.3

# Install dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    build-essential \
    libsnappy-dev \
    zlib1g-dev \
    libbz2-dev \
    libgflags-dev \
    liblz4-dev \
    libzstd-dev \
    wget \
    git \
    librocksdb-dev \
    && rm -rf /var/lib/apt/lists/*

# Set library path
ENV LD_LIBRARY_PATH="/usr/local/lib:/usr/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
# Verify installation of libraries
RUN ldconfig && ldconfig -p | grep rocksdb
RUN ldconfig -p | grep bz2

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Build and install quipubase
RUN cd /app/quipubase && python setup.py build_ext --inplace

EXPOSE 5454

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5454", "--reload"]
