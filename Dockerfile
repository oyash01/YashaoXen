FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    EARNAPP_TERM=yes \
    TZ=UTC

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create EarnApp directory
RUN mkdir -p /etc/earnapp \
    && chmod a+wr /etc/earnapp/

# Download and install EarnApp
RUN arch=$(uname -m) && \
    if [ "$arch" = "x86_64" ] || [ "$arch" = "amd64" ]; then \
        file="earnapp-x64-1.0.0"; \
    elif [ "$arch" = "armv7l" ] || [ "$arch" = "armv6l" ]; then \
        file="earnapp-arm7l-1.0.0"; \
    elif [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then \
        file="earnapp-aarch64-1.0.0"; \
    else \
        file="earnapp-arm7l-1.0.0"; \
    fi && \
    wget -c "https://cdn-earnapp.b-cdn.net/static/$file" -O /usr/local/bin/earnapp \
    && chmod +x /usr/local/bin/earnapp

# Create status file
RUN touch /etc/earnapp/status \
    && chmod a+wr /etc/earnapp/status

# Set working directory
WORKDIR /etc/earnapp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD earnapp status | grep enabled || exit 1

# Start EarnApp
CMD ["earnapp", "start"] 