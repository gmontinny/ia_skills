# Configurando o Servidor MCP nas IDEs

O servidor MCP expõe 3 ferramentas para uso em IDEs com suporte a Model Context Protocol:

| Ferramenta      | Descrição                                              |
|-----------------|--------------------------------------------------------|
| `list_skills`   | Lista todas as skills disponíveis com metadados OKF    |
| `get_skill`     | Retorna o conteúdo completo de uma skill pelo ID       |
| `reload_skills` | Força recarregamento das skills do GitLab              |

## Endpoints do servidor

| Endpoint | Protocolo | IDEs compatíveis |
|----------|-----------|-----------------|
| `http://localhost:8000/sse` | SSE | JetBrains (PyCharm, IntelliJ, WebStorm...) |
| `http://localhost:8000/mcp` | HTTP Streamable | VS Code, Cursor, Antigravity |

> Antes de configurar qualquer IDE, certifique-se que o servidor MCP está rodando.
> Teste: `curl http://localhost:8000/health` deve retornar `{"status":"ok"}`

---

## JetBrains (PyCharm, IntelliJ, WebStorm...)

1. Vá em `Settings` → `Tools` → `AI Assistant` → `Model Context Protocol (MCP)`
2. Clique em **Add** (`+`) → selecione **SSE or HTTP**
3. Preencha:
   - **Name:** `ia-skills-mcp`
   - **URL:** `http://localhost:8000/sse`
4. Clique em **OK** e **Apply**

Ou edite `.ai/mcp/mcp.json` na raiz do projeto:

```json
{
  "mcpServers": {
    "ia-skills-mcp": {
      "url": "http://localhost:8000/sse",
      "type": "sse"
    }
  }
}
```

---

## Visual Studio Code

Adicione em `.vscode/mcp.json` no workspace:

```json
{
  "servers": {
    "ia-skills-mcp": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Ou via paleta de comandos: `Ctrl+Shift+P` → `MCP: Add Server` → **HTTP (streamable)** → URL: `http://localhost:8000/mcp`

---

## Cursor

Edite `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ia-skills-mcp": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

## Antigravity Desktop

O Antigravity usa protocolo MCP `2026-07-28` via HTTP Streamable.

### Configuração por workspace (recomendado)

Crie `.agents/mcp_config.json` na raiz do projeto:

```json
{
  "mcpServers": {
    "ia-skills-mcp": {
      "serverUrl": "http://localhost:8000/mcp"
    }
  }
}
```

### Configuração global

**Windows:** `%USERPROFILE%\.gemini\config\mcp_config.json`

**Mac/Linux:** `~/.gemini/config/mcp_config.json`

```json
{
  "mcpServers": {
    "ia-skills-mcp": {
      "serverUrl": "http://localhost:8000/mcp"
    }
  }
}
```

> Em produção, substitua `http://localhost:8000` pelo domínio do servidor, ex: `https://server-mcp.com`

---

## Usando as ferramentas no chat

**Listar skills disponíveis:**
```
liste as skills disponíveis
```

**Usar uma skill específica:**
```
use a skill lgpd-brasil para me ajudar com essa questão de privacidade
```

**Recarregar após adicionar nova skill no GitLab:**
```
recarregue as skills
```

---

## Problemas comuns

### Servidor não aparece na IDE
- Verifique se o servidor está rodando: `curl http://localhost:8000/health`
- Reinicie a IDE após adicionar o servidor

### Ferramentas aparecem mas retornam erro
- Verifique se o GitLab está rodando: `docker ps | grep gitlab`
- Verifique se o PAT está válido no `mcp-server/.env`
- Use `reload_skills` no chat para forçar recarregamento

### Skills desatualizadas
O cache tem TTL de 5 minutos (`SKILL_CACHE_TTL=300` no `.env`).
Use `reload_skills` no chat para atualização imediata.
