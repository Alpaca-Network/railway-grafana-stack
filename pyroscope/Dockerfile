# Pyroscope base image is distroless — no shell available.
# We do not need one: the base ENTRYPOINT is /usr/bin/pyroscope (a static Go binary).
# Just copy the config and pass it as CMD arguments.
#
# PORT CONFIGURATION FOR RAILWAY:
# Railway injects $PORT when you generate a public domain for this service.
# pyroscope.yml uses ${PORT:-4040} so Pyroscope binds on Railway's assigned port.
#
# gatewayz-backend (separate Railway project) pushes profiles via PUBLIC domain:
#   Railway dashboard → Pyroscope service → Settings → Generate Domain
#   Set PYROSCOPE_SERVER_ADDRESS=https://pyroscope-xxx.up.railway.app on the backend
#
# Grafana (same Railway project) reads via internal DNS:
#   Set PYROSCOPE_INTERNAL_URL=http://pyroscope.railway.internal:4040 on Grafana service

FROM grafana/pyroscope:1.7.1

USER root

COPY pyroscope.yml /etc/pyroscope/pyroscope.yml

EXPOSE 4040

# Base image ENTRYPOINT = /usr/bin/pyroscope
# CMD supplies the arguments: -config.file + any extra args passed at runtime
CMD ["-config.file=/etc/pyroscope/pyroscope.yml"]
