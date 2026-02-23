# Pin to specific version for stability
FROM grafana/pyroscope:1.7.1

# Run as root for Railway volume permissions
USER root

COPY pyroscope.yml /etc/pyroscope/pyroscope.yml

# Inline the startup script so there is no COPY entrypoint.sh step.
# Railway's BuildKit sometimes fails to resolve files in monorepo subdirectory
# build contexts; inlining avoids that entirely.
#
# What this does at runtime:
#   1. Creates /data/pyroscope (VOLUME in base image — can't be done at build time)
#   2. Starts Pyroscope, using $PORT if Railway injects one, otherwise 4040
RUN printf '#!/bin/sh\nset -e\nmkdir -p /data/pyroscope\nchmod -R 777 /data/pyroscope || true\nexec /usr/bin/pyroscope -config.file=/etc/pyroscope/pyroscope.yml "$@"\n' \
    > /entrypoint.sh && chmod +x /entrypoint.sh

# PORT CONFIGURATION FOR RAILWAY:
# Railway injects $PORT automatically when you generate a public domain.
# The entrypoint passes it through to pyroscope.yml via the ${PORT:-4040} substitution.
#
# gatewayz-backend (separate Railway project) pushes profiles via PUBLIC domain:
#   Railway dashboard → Pyroscope service → Settings → Generate Domain
#   Set PYROSCOPE_SERVER_ADDRESS=https://pyroscope-xxx.up.railway.app on the backend
#
# Grafana (same Railway project) reads via internal DNS — free, zero-latency:
#   Set PYROSCOPE_INTERNAL_URL=http://pyroscope.railway.internal:4040 on Grafana service
EXPOSE 4040

ENTRYPOINT ["/entrypoint.sh"]
