# Etapa base para la construcción y configuración
FROM python:3.9 AS builder

WORKDIR /app

COPY . .

ENV PORT=5454
ENV ROCKSDB_VERSION=7.8.3

# Instalar dependencias del sistema
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

# Establecer la ruta de la librería
ENV LD_LIBRARY_PATH="/usr/local/lib:/usr/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
# Verificar la instalación de las librerías
RUN ldconfig && ldconfig -p | grep rocksdb
RUN ldconfig -p | grep bz2

# Crear un script para verificar la disponibilidad de GPU
# RUN echo "import torch\nDEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')\nprint(DEVICE)" > device  && chmod +x device.py 

# Ejecutar el script de verificación de GPU
# RUN device.py > /device.txt

# Etapa final para la configuración
FROM python:3.9 AS chef

WORKDIR /app

COPY --from=builder /app /app

ENV PORT=5454
ENV ROCKSDB_VERSION=7.8.3

# Instalar dependencias del sistema
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

# Establecer la ruta de la librería
ENV LD_LIBRARY_PATH="/usr/local/lib:/usr/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
# Verificar la instalación de las librerías
RUN ldconfig && ldconfig -p | grep rocksdb
RUN ldconfig -p | grep bz2

# Actualizar pip
RUN pip install --upgrade pip

# Instalar dependencias de Python sin PyTorch
RUN pip install -r requirements.txt


# Construir e instalar quipubase
RUN cd /app/quipubase && python setup.py build_ext --inplace

EXPOSE 5454

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5454", "--reload"]