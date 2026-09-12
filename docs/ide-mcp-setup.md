# Configurando o Servidor MCP nas IDEs

O servidor MCP expõe 3 ferramentas para uso em IDEs com suporte a Model Context Protocol:

| Ferramenta      | Descrição                                              |
|-----------------|--------------------------------------------------------|
| `list_skills`   | Lista todas as skills disponíveis com metadados OKF    |
| `get_skill`     | Retorna o conteúdo completo de uma skill pelo ID       |
| `reload_skills` | Força recarregamento das skills do GitLab              |

**URL do servidor:** `http://192.168.15.4:8000/mcp`

> Antes de configurar qualquer IDE, certifique-se que o servidor MCP está rodando:
> ```bash
> cd mcp-server
> .venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000
> ```
> Teste: `curl http://192.168.15.4:8000/health` deve retornar `{"status":"ok"}`

---

## Visual Studio Code

### Pré-requisitos

- Extensão **GitHub Copilot** instalada e ativa
- VS Code 1.99 ou superior

### Configuração

1. Abra a paleta de comandos: `Ctrl+Shift+P`
2. Digite `MCP: Add Server` e selecione
3. Escolha **HTTP (streamable)** como tipo de transporte
4. Preencha:
   - **URL:** `http://192.168.15.4:8000/mcp`
   - **Server ID:** `ia-skills-mcp`
5. Confirme. O VS Code adiciona automaticamente ao `settings.json`

Ou adicione manualmente em `.vscode/mcp.json` no workspace:

```json
{
  "servers": {
    "ia-skills-mcp": {
      "type": "http",
      "url": "http://192.168.15.4:8000/mcp"
    }
  }
}
```

### Verificando

- Abra o painel **Copilot Chat** (`Ctrl+Alt+I`)
- Clique no ícone de ferramentas (🔧) — deve aparecer `ia-skills-mcp` com as 3 ferramentas
- Teste digitando no chat: `liste as skills disponíveis`

---

## JetBrains (IntelliJ, PyCharm, WebStorm, etc.)

### Pré-requisitos

- Plugin **AI Assistant** instalado (JetBrains AI)
- Versão 2024.2 ou superior

### Configuração

1. Vá em `Settings` → `Tools` → `AI Assistant` → `Model Context Protocol (MCP)`
2. Clique em **Add** (`+`)
3. Selecione **SSE or HTTP** como tipo
4. Preencha:
   - **Name:** `ia-skills-mcp`
   - **URL:** `http://192.168.15.4:8000/mcp`
5. Clique em **OK** e depois **Apply**

Ou edite diretamente o arquivo de configuração MCP da JetBrains:

- Windows: `%APPDATA%\JetBrains\<produto>\mcp.json`
- Linux/macOS: `~/.config/JetBrains/<produto>/mcp.json`

```json
{
  "servers": {
    "ia-skills-mcp": {
      "type": "http",
      "url": "http://192.168.15.4:8000/mcp"
    }
  }
}
```

### Verificando

- Abra o painel **AI Assistant** (`Alt+\`)
- As ferramentas MCP aparecem automaticamente no contexto do chat
- Teste digitando: `quais skills estão disponíveis?`

---

## Cursor

### Configuração

1. Vá em `Cursor Settings` → `MCP`
2. Clique em **Add new MCP server**
3. Edite o arquivo `~/.cursor/mcp.json` que será aberto:

```json
{
  "mcpServers": {
    "ia-skills-mcp": {
      "url": "http://192.168.15.4:8000/mcp"
    }
  }
}
```

4. Salve e reinicie o Cursor

### Verificando

- Abra o chat (`Ctrl+L`) no modo **Agent**
- Clique no ícone de ferramentas — deve listar `list_skills`, `get_skill`, `reload_skills`
- Teste: `liste as skills disponíveis`

---

## Google Antigravity

### Pré-requisitos

- Antigravity IDE, 2.0 ou CLI instalado ([antigravity.google](https://antigravity.google))
- Servidor MCP rodando em `http://192.168.15.4:8000/mcp`

### Antigravity IDE

1. Abra o painel lateral do **Agent**
2. Clique no botão `...` no canto superior direito do painel
3. Selecione **MCP Servers**
4. Clique em **Manage MCP Servers** → **View raw config**
5. O arquivo `mcp_config.json` será aberto. Adicione:

```json
{
  "mcpServers": {
    "ia-skills-mcp": {
      "url": "http://192.168.15.4:8000/mcp",
      "transport": "http"
    }
  }
}
```

### Antigravity 2.0 (Desktop)

1. Clique em **Settings** no canto inferior esquerdo
2. Selecione a aba **Customizations**
3. Localize a seção **Installed MCP Servers**
4. Adicione o servidor com a URL `http://192.168.15.4:8000/mcp`

### Antigravity CLI

Digite `/mcp` no painel de prompt para abrir o gerenciador interativo e adicione o servidor.

### Localização dos arquivos de configuração

| Escopo | Caminho |
|--------|---------|
| Global (todos os projetos) | `~/.gemini/config/mcp_config.json` |
| Por projeto (workspace) | `.agents/mcp_config.json` na raiz do projeto |

### Verificando

- No painel do Agent, as ferramentas `list_skills`, `get_skill` e `reload_skills` devem aparecer
- Teste digitando no chat: `liste as skills disponíveis`

---

## Usando as ferramentas no chat

Após configurar qualquer IDE, você pode usar as skills diretamente no chat:

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

- Verifique se o servidor está rodando: `curl http://192.168.15.4:8000/health`
- Confirme que a porta `8000` está acessível na rede
- Reinicie a IDE após adicionar o servidor

### Ferramentas aparecem mas retornam erro

- Verifique se o GitLab está rodando: `docker ps | grep gitlab`
- Verifique se o PAT está válido no `mcp-server/.env`
- Rode `reload_skills` para forçar recarregamento do cache

### Skills desatualizadas

O cache tem TTL de 5 minutos (`SKILL_CACHE_TTL=300` no `.env`).
Para forçar atualização imediata use a ferramenta `reload_skills` no chat.
