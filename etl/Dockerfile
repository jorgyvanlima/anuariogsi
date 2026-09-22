FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY etl/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY etl/ /app/
COPY data/geo/pa_municipios_ibge.json /data_static/pa_municipios_ibge.json
COPY data/geo/pa_municipios.geojson /data_static/pa_municipios.geojson

CMD ["python", "run_all.py"]
