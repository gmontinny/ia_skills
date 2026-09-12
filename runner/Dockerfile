FROM gitlab/gitlab-runner:latest

USER root

# Dependências base + Docker CLI (repositório Ubuntu) + Java 21 + Python 3 — tudo em um RUN
RUN apt-get update && apt-get install -y \
    curl wget git unzip ca-certificates gnupg lsb-release \
    openjdk-21-jdk maven \
    python3 python3-pip python3-venv \
    && \
    # Docker CLI via repositório Ubuntu (não Debian)
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list && \
    apt-get update && apt-get install -y docker-ce-cli docker-compose-plugin && \
    # Node.js 20 LTS
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    # Ferramentas globais
    pip3 install --no-cache-dir pytest coverage tox --break-system-packages && \
    npm install -g yarn pnpm @vue/cli && \
    rm -rf /var/lib/apt/lists/*

# Variáveis de ambiente Java
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

COPY scripts/register-runner.sh /register-runner.sh
RUN chmod +x /register-runner.sh

ENTRYPOINT ["/bin/bash", "/register-runner.sh"]
