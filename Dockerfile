FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN printf "torch==2.6.0+cpu\n" > /tmp/constraints.txt \
    && pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -c /tmp/constraints.txt torch \
    && pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -c /tmp/constraints.txt -r requirements.txt \
    && rm -f /tmp/constraints.txt

COPY Backend ./Backend

EXPOSE 8000

CMD ["uvicorn", "Backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
