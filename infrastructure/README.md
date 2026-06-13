# infrastructure/ — Infrastructure as Code (IaC)

Deployment configurations, container definitions, and environment setup for Frappe Bench.

## What Belongs Here

| Folder / File                | Purpose                                        |
|------------------------------|------------------------------------------------|
| `docker/`                    | Docker and docker-compose configurations       |
| `docker/Dockerfile`          | Frappe app container definition                |
| `docker/docker-compose.yml`  | Local development environment (bench + DB)     |
| `nginx/`                     | Nginx reverse proxy configuration              |
| `nginx/nginx.conf`           | Production Nginx config for Frappe             |
| `sql/`                       | Database seed scripts (if needed)              |
| `bench/`                     | Bench configuration templates                  |

## Docker Example (frappe_docker)

### docker-compose.yml (Development)

```yaml
services:
  mariadb:
    image: mariadb:10.6
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --skip-character-set-client-handshake
      - --skip-innodb-read-only-compressed
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD:-frappe}
    volumes:
      - mariadb-data:/var/lib/mysql
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis-cache:
    image: redis:7-alpine
    ports:
      - "13000:6379"

  redis-queue:
    image: redis:7-alpine
    ports:
      - "11000:6379"

  redis-socketio:
    image: redis:7-alpine
    ports:
      - "12000:6379"

volumes:
  mariadb-data:
```

### Dockerfile (Production — Multi-Stage)

```dockerfile
# Based on official frappe_docker
FROM frappe/bench:latest AS builder

ARG APP_REPO
ARG APP_BRANCH=main

WORKDIR /home/frappe/frappe-bench

# Install app
RUN bench get-app --branch ${APP_BRANCH} ${APP_REPO}

# Production image
FROM frappe/frappe-worker:v16

COPY --from=builder /home/frappe/frappe-bench/apps/my_app /home/frappe/frappe-bench/apps/my_app

RUN bench --site all install-app my_app
```

## Nginx Configuration

### nginx.conf (Production)

```nginx
upstream frappe-bench {
    server 127.0.0.1:8000 fail_timeout=0;
}

upstream socketio-server {
    server 127.0.0.1:9000 fail_timeout=0;
}

server {
    listen 80;
    server_name my-site.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name my-site.example.com;

    # SSL (managed by certbot or similar)
    ssl_certificate /etc/letsencrypt/live/my-site.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/my-site.example.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=63072000" always;

    location / {
        proxy_pass http://frappe-bench;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://socketio-server;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Bench Configuration Template

### common_site_config.json

```json
{
  "db_host": "mariadb",
  "db_port": 3306,
  "redis_cache": "redis://redis-cache:6379",
  "redis_queue": "redis://redis-queue:6379",
  "redis_socketio": "redis://redis-socketio:6379",
  "socketio_port": 9000
}
```

## Rules

- Use `frappe_docker` patterns for production containers
- Non-root user in Docker containers
- Pin base image versions
- Health checks on all services
- Never store secrets in Docker images — use environment variables
- Use Docker volumes for persistent data (MariaDB, Redis)
      - db

  db:
    image: mcr.microsoft.com/mssql/server:2022-latest
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=YourStrong!Password
    ports:
      - "1433:1433"
    volumes:
      - sqldata:/var/opt/mssql

volumes:
  sqldata:
```

## SQL Scripts

Place database initialization scripts in `sql/`:

| File                    | Purpose                              |
|-------------------------|--------------------------------------|
| `init.sql`              | Initial schema (if not using EF)     |
| `seed-data.sql`         | Test/development seed data           |
| `stored-procedures/`    | Stored procedures (if used)          |

## Rules

- Use multi-stage Docker builds for small images
- Never hardcode secrets in infrastructure files
- Use environment variables or secret managers
- Tag Docker images with git commit SHA + semver
- Infrastructure changes go through PR review like code

> Delete folders you don't use. Most projects start with just `docker/`.
