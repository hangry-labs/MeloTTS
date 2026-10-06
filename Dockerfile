# ============================================================
# Stage 1: Build environment with dependencies and models
# ============================================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system-level dependencies once
RUN apt-get update && apt-get install -y \
    build-essential libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the deployment lock first so dependency installation remains cacheable.
COPY requirements.txt .

# Install Python dependencies (PostInstall will auto-download unidic!)
RUN pip install --upgrade pip setuptools wheel
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu130
ARG TORCH_PACKAGES="torch==2.11.0+cu130 torchaudio==2.11.0+cu130"
RUN pip install --extra-index-url ${TORCH_INDEX_URL} -r requirements.txt
RUN pip install --index-url ${TORCH_INDEX_URL} ${TORCH_PACKAGES}
RUN python -m unidic download

# Copy only inference sources before model preload. UI and API-only edits can then
# reuse the expensive model-download layer.
RUN mkdir -p /app/melo
COPY melo/__init__.py melo/api.py melo/attentions.py melo/commons.py \
    melo/download_utils.py melo/init_downloads.py melo/models.py melo/modules.py \
    melo/split_utils.py melo/transforms.py melo/utils.py /app/melo/
COPY melo/monotonic_align /app/melo/monotonic_align
COPY melo/text /app/melo/text

# Download and remove unneeded model formats from Hugging Face cache.
ARG INIT_DOWNLOADS_STRICT=1
ARG INIT_DOWNLOADS_MAX_RETRIES=5
ARG INIT_DOWNLOADS_RETRY_SLEEP=5
ARG INIT_DOWNLOADS_PROFILE=FULL
RUN INIT_DOWNLOADS_STRICT=${INIT_DOWNLOADS_STRICT} \
    INIT_DOWNLOADS_MAX_RETRIES=${INIT_DOWNLOADS_MAX_RETRIES} \
    INIT_DOWNLOADS_RETRY_SLEEP=${INIT_DOWNLOADS_RETRY_SLEEP} \
    INIT_DOWNLOADS_PROFILE=${INIT_DOWNLOADS_PROFILE} \
    PYTHONPATH=/app \
    python melo/init_downloads.py || \
    if [ "${INIT_DOWNLOADS_STRICT}" = "1" ]; then exit 1; else echo "[WARN] init_downloads failed in non-strict mode; continuing build"; fi && \
    find /root/.cache/huggingface/hub \
        -type f \
        \( -name "*.h5" -o -name "*.tflite" -o -name "tf_model*" -o -name "*.onnx" -o -name "rust_model*" -o -name "*.msgpack" \) \
        -exec rm -f {} + 2>/dev/null || true

# Bring in packaging, API, and browser files only after the model cache is ready.
COPY . .

RUN pip install -e .

# Persist the same immutable identity exposed through the OCI image labels.
ARG APP_VERSION=unknown
ARG BUILD_DATE=unknown
ARG BUILD_ID=""
ARG VCS_REF=unknown
RUN APP_VERSION=${APP_VERSION} BUILD_DATE=${BUILD_DATE} BUILD_ID=${BUILD_ID} VCS_REF=${VCS_REF} python -c "import datetime, json, os, pathlib; now=datetime.datetime.now(datetime.UTC).replace(microsecond=0); version_path=pathlib.Path('/app/VERSION'); app_version=(version_path.read_text(encoding='utf-8').strip() if version_path.exists() else '') or os.getenv('APP_VERSION', 'unknown'); build_date=os.getenv('BUILD_DATE', 'unknown'); built_at=build_date if build_date != 'unknown' else now.isoformat().replace('+00:00', 'Z'); build_id=(os.getenv('BUILD_ID') or '').strip() or f'{built_at}@{os.getenv(\"VCS_REF\", \"unknown\")}'; json.dump({'app_version': app_version, 'build_id': build_id, 'built_at_utc': built_at, 'vcs_ref': os.getenv('VCS_REF', 'unknown')}, open('/app/.build_meta.json', 'w', encoding='utf-8'))"

# ============================================================
# Stage 2: Final runtime image
# ============================================================
FROM python:3.13-slim AS runtime

LABEL org.opencontainers.image.source="https://github.com/hangry-labs/MeloTTS"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HOST=0.0.0.0 \
    PORT=8888

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/*

ARG APP_VERSION=unknown
ARG BUILD_DATE=unknown
ARG BUILD_ID=""
ARG DEFAULT_TTS_LANGUAGES="EN,EN_V2,EN_NEWEST,ES,FR,ZH,JP,KR"
ARG VCS_REF=unknown

LABEL org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.revision="${VCS_REF}" \
    org.opencontainers.image.version="${APP_VERSION}"

ENV BUILD_ID=${BUILD_ID} \
    MELOTTS_BUILD_DATE=${BUILD_DATE} \
    MELOTTS_VCS_REF=${VCS_REF} \
    TTS_LANGUAGES=${DEFAULT_TTS_LANGUAGES}

COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface
COPY --from=builder /root/nltk_data /root/nltk_data

# Expose port and run the app
EXPOSE 8888
CMD ["python", "./melo/app.py"]
