# Distribuição de Conhecimento Especializado para Agentes de IA via Model Context Protocol: Uma Arquitetura Baseada em GitLab CE, FastAPI e Versionamento OKF

**Autor:** Guilherme Montinny  
**Categoria:** Engenharia de Software · Inteligência Artificial · DevOps  
**Data:** Setembro de 2026

---

## Resumo

Este artigo descreve a concepção, implementação e validação de uma plataforma para distribuição de conhecimento especializado a agentes de Inteligência Artificial por meio do protocolo Model Context Protocol (MCP). A solução integra um servidor GitLab CE auto-hospedado para versionamento de *skills* no formato Open Knowledge Format (OKF), um servidor MCP construído com FastAPI e Python, e um mecanismo de transporte dual (SSE e HTTP Streamable) que garante compatibilidade com múltiplas IDEs — JetBrains, VS Code, Cursor e Antigravity Desktop. O objetivo central é permitir que profissionais de diferentes perfis (programadores, analistas, DBAs, auditores) consumam conhecimento curado e versionado diretamente em seus ambientes de desenvolvimento, sem necessidade de configuração técnica avançada.

---

## 1. Introdução

O avanço dos modelos de linguagem de grande escala (LLMs) e sua integração em IDEs modernas criou uma nova demanda: como fornecer a esses agentes conhecimento especializado, atualizado e confiável, de forma controlada e auditável?

Soluções baseadas em *prompts* estáticos embutidos no código ou em documentos avulsos apresentam limitações críticas: ausência de versionamento, dificuldade de atualização, falta de rastreabilidade e impossibilidade de reutilização entre equipes e ferramentas.

Este trabalho propõe uma arquitetura que trata o conhecimento como um artefato de software de primeira classe — versionado em repositório Git, validado por pipeline de CI/CD, e distribuído via protocolo padronizado (MCP) para qualquer IDE compatível.

---

## 2. Problema e Motivação

### 2.1 O Problema do Conhecimento Efêmero

Agentes de IA em IDEs operam com contexto limitado e genérico. Um analista de conformidade que usa um assistente de IA para revisar contratos sob a LGPD, por exemplo, precisa que o agente conheça as especificidades da lei brasileira — não apenas o conhecimento genérico do modelo base.

Hoje, a solução comum é copiar e colar *prompts* em cada conversa. Isso é:

- **Não escalável** — cada usuário mantém sua própria cópia
- **Não auditável** — não há histórico de quem alterou o quê
- **Não versionado** — não há como saber qual versão do conhecimento foi usada
- **Não distribuível** — não há mecanismo para publicar atualizações para a equipe

### 2.2 A Oportunidade do MCP

O Model Context Protocol, especificado pela Anthropic em 2024 e adotado por múltiplos fornecedores de IDEs, define um protocolo padronizado para que agentes de IA descubram e invoquem *ferramentas* (tools) expostas por servidores externos. Isso cria uma camada de extensibilidade que permite injetar conhecimento especializado de forma programática, sem modificar o modelo base.

---

## 3. Arquitetura da Solução

A plataforma é composta por três camadas principais:

```
┌─────────────────────────────────────────────────────────────┐
│                        IDEs / Clientes                       │
│   JetBrains (SSE)   VS Code (HTTP)   Antigravity (HTTP)     │
└──────────────────────────┬──────────────────────────────────┘
                           │ MCP Protocol
┌──────────────────────────▼──────────────────────────────────┐
│                    Servidor MCP (FastAPI)                     │
│                                                              │
│  GET /sse  ──► SSE Transport (JetBrains)                    │
│  POST /sse ──► SSE Proxy (session capture)                  │
│  POST /mcp ──► HTTP Streamable (VS Code, Cursor, Antigrav.) │
│  GET /health, /skills ──► REST API                          │
│                                                              │
│  Tools: list_skills · get_skill · reload_skills             │
│  Cache TTL: 5 min · SkillRegistry                           │
└──────────────────────────┬──────────────────────────────────┘
                           │ GitLab API (PAT)
┌──────────────────────────▼──────────────────────────────────┐
│                    GitLab CE (Docker)                        │
│                                                              │
│  Repositório ia-skill/                                      │
│  ├── knowledge.yaml        (bundle descriptor)              │
│  ├── skills/lgpd-brasil/SKILL.md                            │
│  ├── skills/mantine-ui/SKILL.md                             │
│  └── .gitlab-ci.yml        (validação OKF automática)       │
│                                                              │
│  Pipeline CI/CD: validate:okf (Python)                      │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 Camada de Armazenamento — GitLab CE

O GitLab CE é executado em contêiner Docker com configuração estática via `gitlab.rb` (bind mount), evitando o problema de interpolação de variáveis do `GITLAB_OMNIBUS_CONFIG`. A stack Docker Compose inclui cinco serviços com dependências explícitas:

| Serviço | Função |
|---------|--------|
| `gitlab` | GitLab CE com healthcheck em `/users/sign_in` |
| `gitlab-setup` | Cria PAT de admin via `docker exec gitlab-rails runner` |
| `gitlab-init` | Obtém runner token e desabilita signup via API REST |
| `dind` | Docker-in-Docker sem TLS em `tcp://dind:2375` |
| `gitlab-runner` | Runner auto-registrado, multi-stack |

A decisão de usar `docker exec` para criar o PAT inicial decorre de uma limitação do GitLab 19.x: a autenticação Basic Auth foi removida da API REST, tornando impossível criar o primeiro token via API sem já possuir um token.

O Docker-in-Docker opera sem TLS (`--tls=false`, porta 2375) porque o daemon gera certificados com o hostname do contêiner como SAN, mas não inclui o alias de rede `dind` — tornando a conexão TLS inválida. A comunicação ocorre dentro da rede Docker interna, sem exposição externa.

### 3.2 Formato OKF — Open Knowledge Format

Cada *skill* é um arquivo Markdown com frontmatter YAML obrigatório:

```markdown
---
name: lgpd-brasil
description: >
  Orienta sobre a LGPD (Lei 13.709/2018). Use quando o usuário
  mencionar privacidade, dados pessoais, consentimento ou DPO.
status: stable
stale_after: "2027-01-01"
---

# LGPD — Lei Geral de Proteção de Dados

[conteúdo da skill como system prompt]
```

O validador OKF (`validate_okf.py`) aplica seis regras (T1–T6) em pipeline de CI/CD:

- **T1** — `name` presente e não vazio
- **T2** — `description` com mínimo de 20 caracteres
- **T3** — `status` em `{stable, draft, deprecated}`
- **T4** — `stale_after` como data válida ISO 8601
- **T5** — conteúdo com mínimo de 100 caracteres
- **T6** — skill registrada no `knowledge.yaml`

O campo `stale_after` é particularmente relevante para domínios regulatórios: uma skill sobre LGPD criada em 2024 pode estar desatualizada em 2027 após alterações legislativas. O servidor MCP sinaliza skills expiradas com um campo `warning` na resposta, alertando o agente.

### 3.3 Servidor MCP — FastAPI + Python

O servidor é construído com FastAPI e o SDK oficial `mcp[cli]` (versão `>=1.9.0,<2.0.0`). Expõe três ferramentas MCP:

```python
@mcp.tool(name="list_skills")
async def list_skills() -> dict:
    """Lista todas as skills com metadados OKF."""

@mcp.tool(name="get_skill")
async def get_skill(skill_id: str) -> dict:
    """Retorna conteúdo completo de uma skill para uso como system prompt."""

@mcp.tool(name="reload_skills")
async def reload_skills() -> dict:
    """Força recarregamento do cache do GitLab."""
```

O `SkillRegistry` mantém um cache em memória com TTL configurável (padrão: 5 minutos), lendo as skills do GitLab via API REST com autenticação por PAT.

### 3.4 Transporte Dual — SSE e HTTP Streamable

A principal complexidade técnica do projeto foi garantir compatibilidade com múltiplas IDEs que implementam versões diferentes do protocolo MCP:

| IDE | Protocolo | Versão MCP | Endpoint |
|-----|-----------|------------|----------|
| JetBrains | SSE | 2024-11-05 | `GET /sse` + `POST /messages` |
| VS Code | HTTP Streamable | 2025-03-26 | `POST /mcp` |
| Cursor | HTTP Streamable | 2025-03-26 | `POST /mcp` |
| Antigravity | HTTP Streamable | 2026-07-28 | `POST /mcp` |

O Antigravity Desktop 2.x implementa o protocolo MCP `2026-07-28` com HTTP Streamable, enviando um método `server/discover` antes do `initialize` — comportamento não documentado que foi identificado via inspeção dos headers e body das requisições.

A solução adotada foi um **router ASGI manual** na raiz da aplicação, contornando as limitações do sistema de `Mount` do Starlette (que faz *path stripping* e não matcha paths sem trailing slash):

```python
async def _root_asgi(scope, receive, send):
    path = scope.get("path", "")
    method = scope.get("method", "")

    if path == "/sse":
        if method == "GET":
            await _sse_get(scope, receive, send)   # SSE transport
        elif method == "POST":
            await _sse_post(scope, receive, send)  # SSE proxy
    elif path == "/mcp" or path.startswith("/mcp/"):
        await _mcp_streamable(scope, receive, send)  # HTTP Streamable
    else:
        await api(scope, receive, send)  # FastAPI REST
```

O `session_manager` do HTTP Streamable requer inicialização via `lifespan` para criar o task group interno — omissão que resulta em `RuntimeError: Task group is not initialized`.

---

## 4. Desafios Técnicos e Soluções

### 4.1 Compatibilidade de Protocolo entre IDEs

O maior desafio foi a ausência de documentação oficial sobre como o Antigravity Desktop implementa o cliente MCP. A investigação foi conduzida empiricamente:

1. Erro inicial: `Method Not Allowed` — o cliente fazia `POST /sse` mas o endpoint só aceitava `GET`
2. Após expor `POST /sse`: `session not found` — o cliente não enviava `session_id`
3. Inspeção dos headers revelou `mcp-protocol-version: 2026-07-28` e método `server/discover`
4. Conclusão: o Antigravity usa HTTP Streamable, não SSE — redirecionado para `/mcp`

### 4.2 Path Stripping no Starlette Mount

O `Mount("/mcp", app)` do Starlette remove o prefixo `/mcp` do path antes de passar para a sub-aplicação. O `streamable_http_app()` do FastMCP registra internamente a rota em `/mcp` — após o stripping, o path vira `""` e não matcha nenhuma rota, resultando em 404.

A solução foi não usar `Mount` para o endpoint `/mcp` e rotear diretamente no ASGI root, preservando o path original.

### 4.3 Dupla Resposta HTTP no SSE

O `SseServerTransport.handle_post_message()` é um ASGI app completo que envia a resposta HTTP diretamente via `send`. Quando encapsulado em uma rota FastAPI/Starlette, o framework tenta enviar uma segunda resposta após o retorno da função, causando `RuntimeError: Unexpected ASGI message 'http.response.start' sent, after response already completed`.

A solução foi expor as rotas SSE como funções ASGI puras, fora do ciclo de vida de resposta do FastAPI.

### 4.4 Inicialização do Task Group

O `StreamableHTTPSessionManager` usa `anyio.create_task_group()` internamente, que deve ser inicializado dentro de um contexto assíncrono ativo. A inicialização lazy (na primeira requisição) falha porque o task group não existe ainda. A solução foi inicializar via `lifespan` do Starlette:

```python
@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield
```

---

## 5. Fluxo de Uso

```
Especialista de domínio
        │
        ▼
  Cria SKILL.md com frontmatter OKF
        │
        ▼
  git push → GitLab CE
        │
        ▼
  Pipeline CI/CD valida T1-T6
        │
        ▼
  Skill disponível no repositório
        │
        ▼ (cache TTL 5min ou reload_skills)
  Servidor MCP carrega skill
        │
        ▼
  Profissional na IDE pergunta ao agente
        │
        ▼
  Agente invoca list_skills → get_skill
        │
        ▼
  Skill injetada como contexto na conversa
        │
        ▼
  Resposta especializada ao profissional
```

---

## 6. Tecnologias Utilizadas

| Tecnologia | Versão | Função |
|------------|--------|--------|
| Python | 3.12 | Linguagem principal do servidor MCP |
| FastAPI | 0.115+ | Framework web assíncrono |
| Starlette | 0.41+ | ASGI toolkit (routing, lifespan) |
| `mcp[cli]` | >=1.9.0,<2.0.0 | SDK oficial do Model Context Protocol |
| Uvicorn | 0.32+ | Servidor ASGI de produção |
| GitLab CE | 19.x (latest) | Repositório Git + CI/CD + API REST |
| Docker | 24+ | Containerização de todos os serviços |
| Docker Compose | 2.x | Orquestração local da stack |
| Docker-in-Docker | 24-dind | Executor de jobs CI/CD |
| gitlab-runner | latest | Runner de pipelines GitLab |
| Alpine Linux | 3.x | Base do contêiner gitlab-init |
| PyYAML | 6.x | Parsing do frontmatter OKF |
| Python-dotenv | 1.x | Gerenciamento de variáveis de ambiente |

---

## 7. Resultados

A plataforma foi validada com sucesso nos seguintes cenários:

- **JetBrains PyCharm** — conexão via SSE (`/sse`), 3 tools habilitadas
- **Antigravity Desktop 2.x** — conexão via HTTP Streamable (`/mcp`), 3 tools habilitadas
- **Pipeline CI/CD** — validação OKF automática em push, com detecção de erros T1–T6
- **Cache e reload** — skills disponíveis em até 5 minutos após push, ou imediatamente via `reload_skills`
- **PAT automático** — `start.sh` atualiza `mcp-server/.env` a cada reinicialização da stack

O servidor opera com dois transportes simultâneos sem conflito, atendendo IDEs com implementações de protocolo MCP distintas a partir de um único processo Python.

---

## 8. Conclusão

Este trabalho demonstra que é possível construir uma infraestrutura de distribuição de conhecimento especializado para agentes de IA utilizando exclusivamente tecnologias open source, auto-hospedadas e de baixo custo operacional.

A combinação de GitLab CE como repositório de conhecimento, o formato OKF para estruturação e validação de *skills*, e o protocolo MCP para distribuição cria um ciclo completo: **criação → validação → versionamento → distribuição → consumo**.

O principal aprendizado técnico foi a necessidade de um router ASGI manual para suportar múltiplas versões do protocolo MCP simultaneamente — limitação não documentada que só foi identificada através de inspeção empírica do tráfego HTTP de cada cliente.

A arquitetura é preparada para produção: a transição de `http://localhost:8000` para `https://servidor-mcp.com` requer apenas a atualização da URL nos arquivos de configuração das IDEs, sem nenhuma alteração no código do servidor.

Como trabalhos futuros, destacam-se: autenticação por API key por usuário, interface web para gerenciamento de skills sem necessidade de Git, suporte a skills com conteúdo binário (imagens, diagramas), e métricas de uso por skill para identificar conhecimento mais demandado.

---

## Referências

1. Anthropic. *Model Context Protocol Specification*. 2024. Disponível em: https://modelcontextprotocol.io/specification

2. Anthropic. *Python SDK for Model Context Protocol*. GitHub, 2024. Disponível em: https://github.com/modelcontextprotocol/python-sdk

3. GitLab Inc. *GitLab CE Documentation — GitLab Rails Runner*. 2024. Disponível em: https://docs.gitlab.com/ee/administration/operations/rails_console.html

4. Starlette. *ASGI Framework Documentation — Routing and Lifespan*. 2024. Disponível em: https://www.starlette.io/routing/

5. FastAPI. *FastAPI Documentation — Advanced ASGI*. 2024. Disponível em: https://fastapi.tiangolo.com/advanced/

6. Docker Inc. *Docker-in-Docker — Official Image Documentation*. Docker Hub, 2024. Disponível em: https://hub.docker.com/_/docker

7. ABNT. *NBR ISO/IEC 27001:2022 — Segurança da Informação*. Associação Brasileira de Normas Técnicas, 2022.

8. Brasil. *Lei nº 13.709, de 14 de agosto de 2018 — Lei Geral de Proteção de Dados Pessoais (LGPD)*. Diário Oficial da União, Brasília, 2018.

9. Fielding, R. T. *Architectural Styles and the Design of Network-based Software Architectures*. Doctoral dissertation, University of California, Irvine, 2000.

10. Merkel, D. *Docker: Lightweight Linux Containers for Consistent Development and Deployment*. Linux Journal, v. 2014, n. 239, 2014.
