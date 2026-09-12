#!/bin/bash
set -e

GITLAB_URL="${GITLAB_INTERNAL_URL:-http://gitlab}"
TOKEN_FILE="/shared-config/runner-token"
PAT_FILE="/shared-config/admin-pat"

log() { echo "[gitlab-init] $1"; }

wait_gitlab() {
  log "Aguardando GitLab ficar pronto..."
  for i in $(seq 1 60); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$GITLAB_URL/users/sign_in" 2>/dev/null || echo "000")
    if [ "$STATUS" = "200" ]; then
      log "GitLab está pronto!"
      return 0
    fi
    log "Tentativa $i/60 — HTTP $STATUS. Aguardando 10s..."
    sleep 10
  done
  log "ERRO: GitLab não ficou pronto a tempo."
  exit 1
}

wait_pat() {
  log "Aguardando PAT do admin..."
  for i in $(seq 1 30); do
    if [ -f "$PAT_FILE" ] && [ -s "$PAT_FILE" ]; then
      PAT=$(cat "$PAT_FILE")
      STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "PRIVATE-TOKEN: $PAT" "$GITLAB_URL/api/v4/version" 2>/dev/null || echo "000")
      if [ "$STATUS" = "200" ]; then
        log "PAT válido!"
        return 0
      fi
    fi
    log "Tentativa $i/30. Aguardando 10s..."
    sleep 10
  done
  log "ERRO: PAT não ficou disponível."
  exit 1
}

get_runner_token() {
  log "Obtendo token de registro do runner..."
  PAT=$(cat "$PAT_FILE")

  TOKEN=$(curl -s -H "PRIVATE-TOKEN: $PAT" \
    "$GITLAB_URL/api/v4/application/settings" | \
    grep -o '"runners_registration_token":"[^"]*"' | cut -d'"' -f4)

  if [ -z "$TOKEN" ]; then
    TOKEN="initial-runner-token"
    log "Usando token inicial fixo."
  fi

  mkdir -p /shared-config
  echo "$TOKEN" > "$TOKEN_FILE"
  log "Token do runner salvo: $TOKEN"
}

disable_signup() {
  log "Desabilitando registro público..."
  PAT=$(cat "$PAT_FILE")
  curl -s -X PUT "$GITLAB_URL/api/v4/application/settings" \
    -H "PRIVATE-TOKEN: $PAT" \
    -H "Content-Type: application/json" \
    -d '{"signup_enabled":false}' > /dev/null
  log "Signup desabilitado."
}

wait_gitlab
wait_pat
get_runner_token
disable_signup
log "Inicialização concluída!"
