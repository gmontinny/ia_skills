# Post LinkedIn

---

🚀 **Construí uma plataforma de distribuição de conhecimento especializado para agentes de IA — e foi mais complexo do que parecia.**

A ideia era simples: versionar *skills* de domínio (LGPD, frameworks, regulações) no GitLab e distribuí-las automaticamente para qualquer IDE com suporte a IA — PyCharm, VS Code, Cursor, Antigravity — sem que o usuário final precisasse instalar nada além da própria IDE.

O resultado: um servidor MCP (Model Context Protocol) em FastAPI + Python, integrado a um GitLab CE auto-hospedado via Docker, com pipeline de CI/CD validando cada skill antes de publicar.

---

**O que parecia simples virou uma jornada de descobertas:**

🔍 **Cada IDE implementa o protocolo MCP de um jeito diferente.**
JetBrains usa SSE. VS Code e Cursor usam HTTP Streamable. O Antigravity Desktop usa HTTP Streamable com protocolo versão *2026-07-28* — com um método `server/discover` antes do `initialize` que não está documentado em lugar nenhum. Só descobrimos isso inspecionando os headers e o body das requisições em tempo real.

🔍 **O sistema de roteamento do Starlette tem um comportamento não óbvio.**
O `Mount("/mcp", app)` faz *path stripping* — remove o prefixo antes de passar para a sub-aplicação. O SDK do MCP registra a rota internamente em `/mcp`. Resultado: 404 silencioso. A solução foi um router ASGI manual na raiz, preservando o path original.

🔍 **O `SseServerTransport` é um ASGI app completo.**
Ele envia a resposta HTTP diretamente via `send`. Quando encapsulado em uma rota FastAPI, o framework tenta enviar uma segunda resposta — `RuntimeError: response already completed`. Foram várias tentativas até entender que a solução era expor as rotas SSE fora do ciclo de vida do FastAPI.

🔍 **O GitLab 19.x removeu a autenticação Basic Auth da API REST.**
Não é possível criar o primeiro PAT via API sem já ter um PAT. A solução: `docker exec gitlab gitlab-rails runner` — criando o token diretamente no banco via console Rails, automatizado no startup da stack.

🔍 **Docker-in-Docker com TLS falha silenciosamente.**
O daemon gera certificados com o hostname do contêiner como SAN, mas não inclui o alias de rede `dind`. A conexão TLS é rejeitada. Solução: `--tls=false` na porta 2375, comunicação dentro da rede Docker interna.

---

**A arquitetura final ficou assim:**

```
IDEs (JetBrains · VS Code · Cursor · Antigravity)
           │ MCP Protocol (SSE ou HTTP Streamable)
    Servidor MCP — FastAPI + Python
           │ GitLab API (PAT)
    GitLab CE — skills versionadas em Markdown + CI/CD OKF
```

Três camadas. Sem scripts locais. Sem instalação no cliente. O usuário configura a URL do servidor na IDE e começa a usar.

---

**O que aprendi com isso:**

✅ Ler a documentação oficial não é suficiente quando o cliente não segue a spec  
✅ Inspeção empírica de tráfego HTTP vale mais do que horas de especulação  
✅ Arquitetura simples no papel pode esconder complexidade real de protocolo  
✅ O valor de versionar conhecimento como código vai além do controle de versão — é rastreabilidade, validação automática e distribuição controlada

---

Se você trabalha com IA em times multidisciplinares — programadores, analistas, DBAs, auditores — e quer que todos consumam o mesmo conhecimento curado e atualizado diretamente na IDE, essa arquitetura resolve exatamente isso.

O código e a documentação completa estão no repositório. 👇

\#ModelContextProtocol \#MCP \#FastAPI \#GitLab \#Docker \#Python \#InteligenciaArtificial \#DevOps \#EngenhariadeSoftware \#LLM \#AITools
