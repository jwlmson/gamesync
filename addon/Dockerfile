# ── Stage 1: Build React frontend ──
FROM node:20-alpine AS frontend-build

WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python runtime ──
ARG BUILD_FROM
FROM ${BUILD_FROM}

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Backend code
COPY gamesync/ ./gamesync/

# Frontend dist from build stage
COPY --from=frontend-build /build/dist ./frontend/dist

# Entrypoint
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
