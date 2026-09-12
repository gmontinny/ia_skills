# Servidor MCP — Como Rodar

O servidor MCP é uma aplicação **FastAPI + Python** que lê as skills do GitLab e as expõe como ferramentas para IDEs via protocolo MCP.

---

## Sumário

- [Pré-requisitos](#pré-requisitos)
- [Configuração](#configuração)
- [Instalando dependências](#instalando-dependências)
- [Rodando o servidor](#rodando-o-servidor)
- [Verificando se está funcionando](#verificando-se-está-funcionando)
- [Endpoints disponíveis](#endpoints-disponíveis)
- [Parando o servidor](#parando-o-servidor)
- [Problemas comuns](#problemas-comuns)

---

## Pré-requisitos

- Python 3.12+
- GitLab rodando (`bash start.sh` na raiz do projeto)
- Stack Docker levantada e PAT gerado

---

## Configuração

O arquivo `.env` já é criado e atualizado automaticamente pelo `start.sh`.
Verifique se está correto:

```bash
# mcp-server/.env
GITLAB_URL=http://192.168.15.4
GITLAB_TOKEN=glpat-...          # atualizado automaticamente pelo start.sh
GITLAB_PROJECT_ID=gmontinny/ia-skill
GITLAB_BRANCH=main
MCP_HOST=0.0.0.0
MCP_PORT=8000
SKILL_CACHE_TTL=300
LOG_LEVEL=INFO
```

> Se precisar atualizar o PAT manualmente, copie o valor de `GITLAB_TOKEN`
> rodando na raiz do projeto:
> ```bash
> bash start.sh
> ```

---

## Instalando dependências

Na primeira vez, crie o ambiente virtual e instale as dependências:

```bash
cd mcp-server

# Criar ambiente virtual
python -m venv .venv

# Ativar — Windows
.venv\Scripts\activate

# Ativar — Linux/macOS
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

---

## Rodando o servidor

Com o ambiente virtual ativado:

```bash
cd mcp-server
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS

python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Saída esperada:
```
INFO  Servidor iniciando — MCP em http://0.0.0.0:8000/mcp | Health em http://0.0.0.0:8000/health
INFO  Application startup complete.
```

### Modo desenvolvimento (reload automático)

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Verificando se está funcionando

```bash
# Health check
curl http://192.168.15.4:8000/health

# Resposta esperada:
# {"status":"ok","server":"ia-skills-mcp","version":"1.0.0"}
```

```bash
# Listar skills carregadas
curl http://192.168.15.4:8000/skills

# Resposta esperada:
# {"skills":[{"id":"lgpd-brasil",...},{"id":"mantine-ui",...}],"total":2}
```

---

## Endpoints disponíveis

| Método | Endpoint         | Descrição                              |
|--------|------------------|----------------------------------------|
| GET    | `/health`        | Status do servidor                     |
| GET    | `/skills`        | Lista todas as skills com metadados    |
| GET    | `/skills/{id}`   | Retorna conteúdo completo de uma skill |
| POST   | `/skills/reload` | Força recarregamento do cache          |
| POST   | `/mcp`           | Endpoint MCP (usado pelas IDEs)        |

---

## Parando o servidor

`Ctrl+C` no terminal onde o servidor está rodando.

---

## Problemas comuns

### `ModuleNotFoundError: No module named 'mcp'`

O ambiente virtual não está ativado ou as dependências não foram instaladas:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

### `No module named 'mcp.server.fastmcp'`

A versão do `mcp` instalada é a 2.x. O projeto requer `mcp<2`:

```bash
pip install "mcp[cli]>=1.9.0,<2.0.0"
```

### Skills não carregam — erro de autenticação

O PAT no `.env` está expirado. Rode na raiz do projeto:

```bash
bash start.sh
```

O script atualiza o `mcp-server/.env` automaticamente.

### Servidor sobe mas retorna 0 skills

Verifique se o GitLab está rodando e o projeto `ia-skill` existe:

```bash
# Verificar containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Testar acesso ao GitLab
curl -H "PRIVATE-TOKEN: <SEU_PAT>" http://192.168.15.4/api/v4/projects/gmontinny%2Fia-skill
```
