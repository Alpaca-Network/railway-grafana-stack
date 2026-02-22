# Pin to specific version for stability
FROM grafana/pyroscope:1.7.1

# Run as root for Railway volume permissions
USER root

# NOTE: /data is declared as a VOLUME in the base Pyroscope image, so
# directory creation must happen at runtime, not build time.  The
# entrypoint.sh already runs: mkdir -p /data/pyroscope && chmod 777 ...
COPY pyroscope.yml /etc/pyroscope/pyroscope.yml
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# PORT CONFIGURATION FOR RAILWAY:
# Pyroscope listens on a single port:
#   - 4040: HTTP API (profile ingest + Grafana queries) - INTERNAL only
#
# The backend pushes profiles to http://pyroscope.railway.internal:4040
# Grafana reads profiles from http://pyroscope.railway.internal:4040
# No public exposure needed — all traffic is internal to the Railway project.
EXPOSE 4040

ENTRYPOINT ["/entrypoint.sh"]
