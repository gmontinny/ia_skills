#!/bin/sh

PAT_FILE="/shared-config/admin-pat"
mkdir -p /shared-config

echo "[gitlab-setup] Aguardando gitlab-rails ficar pronto..."

for i in $(seq 1 30); do
  TOKEN=$(docker exec gitlab gitlab-rails runner \
    "u = User.find_by(username: 'root'); \
     u.personal_access_tokens.where(name: 'init-token').destroy_all; \
     t = u.personal_access_tokens.create!(name: 'init-token', scopes: ['api', 'sudo'], expires_at: 1.year.from_now); \
     puts t.token" 2>&1 | grep '^glpat-' || true)

  if [ -n "$TOKEN" ]; then
    echo "$TOKEN" > "$PAT_FILE"
    echo "[gitlab-setup] PAT salvo com sucesso."
    exit 0
  fi

  echo "[gitlab-setup] Tentativa $i/30 — gitlab-rails ainda não pronto. Aguardando 20s..."
  sleep 20
done

echo "[gitlab-setup] ERRO: Não foi possível criar PAT após 30 tentativas."
exit 1
