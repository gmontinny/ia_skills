# GitLab CE — Stack com Docker Compose

Stack completa com GitLab CE, runner Docker-in-Docker e auto-configuração via API.

📖 **Documentação completa**: [docs/stack-reference.md](docs/stack-reference.md)

🔌 **Configurar IDEs (VS Code, JetBrains, Cursor, Antigravity)**: [docs/ide-mcp-setup.md](docs/ide-mcp-setup.md)

🚀 **Enviar projetos e skills ao GitLab**: [docs/gitlab-push-guide.md](docs/gitlab-push-guide.md)

---

## Início rápido

### 1. Configure IP e senha

Edite `gitlab-config/gitlab.rb`:

```ruby
external_url 'http://SEU_IP'
gitlab_rails['initial_root_password'] = 'SuaSenha'
```

> Senha não pode conter palavras comuns nem `$`. Ex: `Xk9mP2vL7nQ4wRst`

### 2. Suba a stack

```bash
bash start.sh
```

O script faz tudo automaticamente:
- Derruba e limpa volumes anteriores (`down -v`)
- Sobe a stack completa
- Aguarda a inicialização terminar
- Atualiza `mcp-server/.env` com o novo PAT gerado

### 3. Acesse

- URL: `http://SEU_IP`
- Usuário: `root`
- Senha: valor de `initial_root_password` no `gitlab.rb`

### 4. Verifique o runner

`Admin Area > CI/CD > Runners` → runner `docker-dind-runner` deve estar **online**.

---

## Reiniciar / religar

```bash
bash start.sh           # religar sem perder dados
bash start.sh --reset   # apagar tudo e subir do zero
```

> Use `--reset` apenas quando mudar senha, mudar IP, ou após inicialização parcial.
> No uso normal, `bash start.sh` preserva o banco e os repositórios do GitLab.

---

## Estrutura

```
.
├── start.sh                      # Sobe tudo e atualiza o PAT automaticamente
├── docker-compose.yml
├── .env
├── gitlab-config/gitlab.rb       # Configuração estática do GitLab
├── gitlab-init/Dockerfile        # Init container (Alpine + curl)
├── runner/Dockerfile             # Runner com Java 21, Python 3, Node 20
├── scripts/
│   ├── setup-gitlab.sh           # Cria PAT via docker exec
│   ├── init-gitlab.sh            # Configura settings via API REST
│   └── register-runner.sh        # Registra runner e inicia processo
├── ia-skill/                     # Repositório de skills OKF (versionado no GitLab)
│   ├── knowledge.yaml            # Descritor do bundle
│   ├── .gitlab-ci.yml            # Pipeline de validação OKF
│   ├── scripts/validate_okf.py   # Validador local
│   └── skills/                   # Uma pasta por skill
│       ├── lgpd-brasil/SKILL.md
│       └── mantine-ui/SKILL.md
├── mcp-server/                   # Servidor MCP (FastAPI + Python)
│   ├── src/                      # Código fonte
│   ├── .env                      # Configuração (PAT, URL GitLab)
│   ├── main.py                   # Entrypoint FastAPI
│   └── requirements.txt
└── docs/
    ├── stack-reference.md        # Referência técnica da infra
    ├── ide-mcp-setup.md          # Configuração das IDEs
    └── gitlab-push-guide.md      # Como enviar projetos e skills
```

## Serviços

| Serviço         | Imagem                    | Descrição                                        |
|-----------------|---------------------------|--------------------------------------------------|
| `gitlab`        | `gitlab/gitlab-ce:latest` | GitLab CE                                        |
| `gitlab-setup`  | `docker:24-cli`           | Cria PAT via `docker exec` no container gitlab   |
| `gitlab-init`   | custom (alpine)           | Obtém runner token e desabilita signup via API   |
| `dind`          | `docker:24-dind`          | Docker daemon sem TLS em `tcp://dind:2375`       |
| `gitlab-runner` | custom                    | Runner auto-registrado, multi-stack              |

## Stacks suportadas no runner

| Stack    | Imagem usada no pipeline        |
|----------|---------------------------------|
| Java     | `maven:3.9-eclipse-temurin-21`  |
| Python   | `python:3.12-slim`              |
| Node.js  | `node:20-alpine`                |
| Vue.js   | `node:20-alpine`                |
| React    | `node:20-alpine`                |
| Docker   | `docker:24-cli` + serviço dind  |
