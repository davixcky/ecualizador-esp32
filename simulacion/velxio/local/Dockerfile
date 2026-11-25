# Rebuild only the frontend; reuse the upstream toolchains and emulators.
FROM node:22-bookworm-slim AS frontend
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
ARG VELXIO_COMMIT=b9fd8eb837ebec22e817dfd8ebd01c9f51aa16b6
RUN git clone --filter=blob:none --no-checkout https://github.com/davidmonterocrespo24/velxio.git /src && cd /src && git sparse-checkout set frontend && git checkout ${VELXIO_COMMIT}
COPY limites-operacional.patch /tmp/limites-operacional.patch
RUN cd /src && git apply /tmp/limites-operacional.patch
COPY rotulos-presentacion.patch /tmp/rotulos-presentacion.patch
RUN cd /src && git apply /tmp/rotulos-presentacion.patch
COPY potenciometros-flotantes.patch /tmp/potenciometros-flotantes.patch
RUN cd /src && git apply /tmp/potenciometros-flotantes.patch
WORKDIR /src/frontend
RUN npm install --ignore-scripts --no-audit --no-fund --workspaces=false --legacy-peer-deps
RUN node scripts/copy-monaco.mjs && npx vite build

FROM ghcr.io/davidmonterocrespo24/velxio@sha256:397f476752a750692861ea4229e420c7981c142807864a3c33cfeb207fc05a68
RUN rm -rf /usr/share/nginx/html
COPY --from=frontend /src/frontend/dist/ /usr/share/nginx/html/
