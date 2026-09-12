#!/bin/bash
set -e

log()     { echo ""; echo ">>> $1"; echo ""; }
success() { echo "  ✔ $1"; }
waiting() { echo "  ⏳ $1"; }
error()   { echo ""; echo "  ✘ ERRO: $1"; echo ""; exit 1; }

RESET=false
[ "$1" = "--reset" ] && RESET=true

PROJECT=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
SHARED_VOL="${PROJECT}_shared_config"

# ── 1. Reset opcional ─────────────────────────────────────────────────────────
if [ "$RESET" = true ]; then
  log "Limpando stack anterior..."
  docker compose down -v --remove-orphans 2>/dev/null || true
  success "Volumes removidos."
fi

# ── 2. Sobe infraestrutura base (gitlab + dind) ───────────────────────────────
log "Iniciando serviços base..."
docker compose up -d gitlab dind
success "GitLab e Docker daemon iniciados."

# ── 3. Aguarda GitLab ficar healthy ──────────────────────────────────────────
log "Aguardando GitLab inicializar (pode levar 5-15 min no primeiro boot)..."
DOTS=0
while true; do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' gitlab 2>/dev/null || echo "waiting")
  case "$STATUS" in
    healthy)
      success "GitLab está pronto!"
      break
      ;;
    unhealthy)
      error "GitLab falhou ao inicializar. Veja: docker logs gitlab"
      ;;
    *)
      printf "."
      DOTS=$((DOTS + 1))
      [ $((DOTS % 60)) -eq 0 ] && echo " (ainda aguardando...)"
      sleep 10
      ;;
  esac
done

# ── 4. Sobe gitlab-setup e gitlab-init ───────────────────────────────────────
log "Iniciando configuração automática..."
docker compose up -d gitlab-setup gitlab-init
success "Serviços de configuração iniciados."

# ── 5. Aguarda PAT ficar disponível ──────────────────────────────────────────
log "Aguardando geração do PAT de acesso..."
for i in $(seq 1 60); do
  PAT=$(docker run --rm -v "${SHARED_VOL}:/shared-config" alpine \
    cat /shared-config/admin-pat 2>/dev/null || true)
  if [ -n "$PAT" ]; then
    success "PAT gerado com sucesso."
    break
  fi

  STATUS=$(docker inspect --format='{{.State.Status}}' gitlab-setup 2>/dev/null || echo "waiting")
  if [ "$STATUS" = "exited" ]; then
    EXIT_CODE=$(docker inspect --format='{{.State.ExitCode}}' gitlab-setup 2>/dev/null || echo "1")
    [ "$EXIT_CODE" != "0" ] && error "Falha na configuração. Veja: docker logs gitlab-setup"
  fi

  waiting "Tentativa $i/60..."
  sleep 10
done

[ -z "$PAT" ] && error "PAT não encontrado. Veja: docker logs gitlab-setup"

# ── 6. Sobe o runner (após init completar) ────────────────────────────────────
log "Iniciando runner..."
docker compose up -d gitlab-runner
success "Runner iniciado."

# ── 7. Atualiza mcp-server/.env ─────────────────────────────────────────────
sed -i "s|^GITLAB_TOKEN=.*|GITLAB_TOKEN=$PAT|" "mcp-server/.env"
success "mcp-server/.env atualizado."

# ── 8. Resumo ─────────────────────────────────────────────────────────────────
log "Stack pronta!"
echo "  GitLab:  http://192.168.15.4"
echo "  Usuário: root"
echo "  Senha:   (definida em gitlab-config/gitlab.rb)"
echo "  PAT:     $PAT"
echo ""
echo "  Verificar runner: Admin Area > CI/CD > Runners"
