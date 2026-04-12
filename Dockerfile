# ---------------------------
# Stage 1: Build & Install
# ---------------------------
FROM python:3.10-slim AS builder

WORKDIR /app

# Create a virtual environment so we only copy the final installed packages
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/requirements.txt .

RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir -r requirements.txt

# ---------------------------
# Stage 2: Final Small Image
# ---------------------------
FROM python:3.10-slim

WORKDIR /app

# Copy the pre-installed Python packages from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only the backend code
COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
