FROM python:3.11-slim

# Install system dependencies & wireguard tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    wireguard-tools \
    iptables \
    iproute2 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ .

ENV WG_CONFIG_DIR=/etc/wireguard
ENV WG_DATA_FILE=/app/data/vpn_data.json
ENV PORT=8080
ENV HOST=0.0.0.0

EXPOSE 8080 51820/udp

# Entrypoint script
RUN echo '#!/bin/sh\n\
mkdir -p /etc/wireguard /app/data\n\
# Enable IP Forwarding in container network namespace\n\
sysctl -w net.ipv4.ip_forward=1 2>/dev/null || true\n\
python app.py\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
