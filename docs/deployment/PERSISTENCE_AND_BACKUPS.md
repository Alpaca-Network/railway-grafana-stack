# Persistence & Backups (Railway-focused)

This repo runs a production observability stack (Grafana/Prometheus/Loki/Tempo).

## Goals

- Keep **Prometheus/Loki/Tempo private-only** (not publicly exposed)
- Persist state so restarts/redeploys don’t wipe dashboards, alert rules, or metrics/logs/traces history
- Provide a clear path to **durable storage** (Railway volumes for small/medium; object storage for long-term)

## Local development

`docker-compose.yml` uses named volumes:

- `grafana_data` → `/var/lib/grafana`
- `prometheus_data` → `/prometheus`
- `loki_data` → `/loki`
- `tempo_data` → `/var/tempo`

These volumes persist on your machine. To reset locally:

```bash
docker compose down -v
```

## Railway production

### Recommended baseline (Railway volumes)

For each stateful service, attach a Railway Volume and mount it to the same path used in compose:

- Grafana: `/var/lib/grafana`
- Prometheus: `/prometheus`
- Loki: `/loki`
- Tempo: `/var/tempo`

This gets you persistence across deploys.

### Backups

#### Grafana

Grafana state consists of:

- SQLite DB inside `/var/lib/grafana` (users, dashboards, alert history, etc.)
- Provisioned dashboards/datasources (stored in git under `grafana/`)

**Best practice:** Treat provisioning in git as source-of-truth and keep volume primarily for runtime state.

#### Prometheus

Prometheus uses local TSDB in `/prometheus`.

Options:

1) **Volume snapshots** (simple)
2) Remote-write to a long-term system (advanced)

#### Loki

Loki can run with filesystem storage, but object storage is strongly recommended for production durability.

Options:

1) **Filesystem + Volume** (simpler; adequate for smaller retention windows)
2) **Object storage (S3-compatible)** (recommended for longer retention)

> Note: Loki 3.4 retention/compactor config has breaking changes. We are addressing this in a dedicated branch `fix/fix/loki-3.4-fail`.

#### Tempo

Tempo trace blocks are best stored in object storage for durability.

Options:

1) **Volume** for small setups
2) **S3-compatible object storage** for production durability

## Operational notes

- `docker-compose.yml` includes healthchecks and basic container hardening settings.
- Prometheus/Loki/Tempo ports are intentionally **not published**; Grafana is the only public entrypoint.

