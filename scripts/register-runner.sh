#!/bin/bash

GITLAB_URL="${GITLAB_INTERNAL_URL:-http://gitlab}"
TOKEN_FILE="/shared-config/runner-token"
CONFIG_DIR="/etc/gitlab-runner"
CONFIG="$CONFIG_DIR/config.toml"
NETWORK="${DOCKER_NETWORK:-ia_skills_gitlab_net}"

log() { echo "[runner-register] $1"; }

# Garante que o diretório existe com permissões corretas
mkdir -p "$CONFIG_DIR"

wait_token() {
  log "Aguardando token do runner..."
  for i in $(seq 1 60); do
    [ -f "$TOKEN_FILE" ] && [ -s "$TOKEN_FILE" ] && log "Token encontrado!" && return 0
    log "Tentativa $i/60. Aguardando 10s..."
    sleep 10
  done
  log "ERRO: Token não encontrado."
  exit 1
}

wait_gitlab_api() {
  log "Aguardando API do GitLab..."
  for i in $(seq 1 60); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$GITLAB_URL/users/sign_in" 2>/dev/null || echo "000")
    [ "$STATUS" = "200" ] && log "API disponível!" && return 0
    log "Tentativa $i/60 — HTTP $STATUS. Aguardando 10s..."
    sleep 10
  done
  log "ERRO: API não ficou disponível."
  exit 1
}

register_runner() {
  if [ -f "$CONFIG" ]; then
    log "Runner já registrado, pulando registro."
    return 0
  fi

  TOKEN=$(cat "$TOKEN_FILE")
  log "Registrando runner (network: $NETWORK)..."

  gitlab-runner register \
    --non-interactive \
    --url "$GITLAB_URL" \
    --registration-token "$TOKEN" \
    --name "${RUNNER_NAME:-docker-dind-runner}" \
    --executor "docker" \
    --docker-image "docker:24-dind" \
    --docker-privileged \
    --docker-volumes "/cache" \
    --tag-list "${RUNNER_TAGS:-docker,java,python,nodejs,vuejs,react,dind}" \
    --run-untagged \
    --locked=false \
    --access-level "not_protected"

  log "Runner registrado com sucesso!"
}

patch_config() {
  log "Aplicando configurações no config.toml..."
  sed -i "s/^concurrent = .*/concurrent = ${RUNNER_CONCURRENT:-4}/" "$CONFIG"
  log "config.toml atualizado."
}

wait_token
wait_gitlab_api
register_runner
patch_config

log "Iniciando gitlab-runner..."
exec gitlab-runner run --user=gitlab-runner --working-directory=/home/gitlab-runner
