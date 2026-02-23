# ── Stage 1: script builder ──────────────────────────────────────────────────
# Pyroscope's base image is distroless (no /bin/sh).
# Use busybox to write the entrypoint script — no COPY from build context needed.
FROM busybox:1.36 AS setup

RUN printf '#!/bin/sh\nset -e\nmkdir -p /data/pyroscope\nchmod -R 777 /data/pyroscope || true\nexec /usr/bin/pyroscope -config.file=/etc/pyroscope/pyroscope.yml "$@"\n' \
    > /entrypoint.sh && chmod +x /entrypoint.sh

# ── Stage 2: final image ──────────────────────────────────────────────────────
FROM grafana/pyroscope:1.7.1

USER root

# Copy config
COPY pyroscope.yml /etc/pyroscope/pyroscope.yml

# Bring in /bin/sh from busybox so the shell script can run at container startup
COPY --from=setup /bin/sh /bin/sh

# Bring in the entrypoint (written in stage 1 — no build-context COPY)
COPY --from=setup /entrypoint.sh /entrypoint.sh

# PORT CONFIGURATION FOR RAILWAY:
# Railway injects $PORT when you generate a public domain for this service.
# pyroscope.yml uses ${PORT:-4040} so the server binds on Railway's assigned port.
#
# gatewayz-backend (separate Railway project) pushes profiles via PUBLIC domain:
#   Railway dashboard → Pyroscope service → Settings → Generate Domain
#   Set PYROSCOPE_SERVER_ADDRESS=https://pyroscope-xxx.up.railway.app on the backend
#
# Grafana (same Railway project) reads via internal DNS:
#   Set PYROSCOPE_INTERNAL_URL=http://pyroscope.railway.internal:4040 on Grafana service
EXPOSE 4040

ENTRYPOINT ["/entrypoint.sh"]
