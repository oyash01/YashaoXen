FROM ubuntu:20.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    supervisor \
    ca-certificates \
    iptables \
    net-tools \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Create directory for EarnApp
RUN mkdir -p /opt/earnapp

# Download and install EarnApp
RUN curl -L https://brightdata.com/static/earnapp/EarnApp-linux.zip -o /tmp/earnapp.zip \
    && unzip /tmp/earnapp.zip -d /opt/earnapp \
    && rm /tmp/earnapp.zip \
    && chmod +x /opt/earnapp/earnapp

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create directory for logs
RUN mkdir -p /var/log/earnapp

# Set working directory
WORKDIR /opt/earnapp

# Environment variables
ENV NODE_ID=""
ENV PROXY_URL=""
ENV MEMORY_LIMIT="2G"

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose required ports
EXPOSE 49152

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"] 