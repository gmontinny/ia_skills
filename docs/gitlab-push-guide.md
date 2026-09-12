# Enviando Projetos e Skills ao GitLab

Este guia explica como criar e enviar projetos ao GitLab local, e como adicionar novas skills ao repositório `ia-skill` para que fiquem disponíveis no servidor MCP.

---

## Sumário

- [Pré-requisitos](#pré-requisitos)
- [Enviando um projeto ao GitLab](#enviando-um-projeto-ao-gitlab)
- [Estrutura do repositório ia-skill](#estrutura-do-repositório-ia-skill)
- [Adicionando uma nova skill](#adicionando-uma-nova-skill)
- [Formato OKF da skill](#formato-okf-da-skill)
- [Validando localmente](#validando-localmente)
- [Enviando ao GitLab](#enviando-ao-gitlab)
- [Verificando a pipeline](#verificando-a-pipeline)

---

## Pré-requisitos

- GitLab rodando em `http://192.168.15.4`
- Git instalado na máquina
- Usuário criado no GitLab (ou usar o `root`)

---

## Enviando um projeto ao GitLab

### 1. Crie o projeto no GitLab

1. Acesse `http://192.168.15.4`
2. Clique em **New project** → **Create blank project**
3. Preencha o nome e clique em **Create project**
4. Anote a URL do projeto. Ex: `http://192.168.15.4/gmontinny/meu-projeto.git`

### 2. Configure o Git localmente

Na pasta do seu projeto:

```bash
git init
git remote add origin http://192.168.15.4/gmontinny/meu-projeto.git
```

### 3. Configure suas credenciais

Use o PAT (Personal Access Token) gerado automaticamente pela stack.
O PAT atual está em `mcp-server/.env` na variável `GITLAB_TOKEN`.

Configure o Git para usar o PAT:

```bash
git remote set-url origin http://root:<SEU_PAT>@192.168.15.4/gmontinny/meu-projeto.git
```

> Substitua `<SEU_PAT>` pelo valor de `GITLAB_TOKEN` no `mcp-server/.env`.

### 4. Faça o primeiro push

```bash
git add .
git commit -m "feat: initial commit"
git push -u origin main
```

---

## Estrutura do repositório ia-skill

O repositório `ia-skill` fica dentro do projeto principal em `ia-skill/` e segue o padrão **OKF (Open Knowledge Format)**:

```
ia_skills/
└── ia-skill/                   # ← repositório de skills
    ├── knowledge.yaml          # Descritor do bundle de skills
    ├── .gitlab-ci.yml          # Pipeline de validação automática
    ├── scripts/
    │   └── validate_okf.py     # Script de validação OKF
    └── skills/
        ├── lgpd-brasil/
        │   ├── SKILL.md        # Conteúdo e metadados da skill
        │   └── reference.md    # Material de referência (opcional)
        └── mantine-ui/
            ├── SKILL.md
            └── reference.md
```

---

## Adicionando uma nova skill

### 1. Crie a pasta da skill

```bash
cd ia_skills/ia-skill
mkdir skills/minha-skill
```

### 2. Crie o arquivo `SKILL.md`

O arquivo deve ter um **frontmatter YAML** obrigatório seguido do conteúdo:

```markdown
---
name: minha-skill
description: >
  Descrição clara de quando usar esta skill. Use quando o usuário mencionar
  [contexto específico], [termos relacionados] ou [situações de uso].
status: stable
stale_after: "2027-01-01"
---

# Título da Skill

Conteúdo da skill aqui. Este texto será usado como system prompt pelo agente.

## Seção 1

...

## Seção 2

...
```

### 3. Registre a skill no `knowledge.yaml`

Adicione a nova skill na lista `skills:`:

```yaml
skills:
  - id: lgpd-brasil
    path: skills/lgpd-brasil/SKILL.md
    description: Orienta sobre a LGPD (Lei 13.709/2018)

  - id: minha-skill
    path: skills/minha-skill/SKILL.md
    description: Descrição curta da minha skill
```

---

## Formato OKF da skill

### Campos obrigatórios no frontmatter

| Campo         | Tipo   | Descrição                                              |
|---------------|--------|--------------------------------------------------------|
| `name`        | string | Identificador único da skill (sem espaços)             |
| `description` | string | Quando usar a skill — usado pelo agente para seleção   |
| `status`      | string | `stable`, `draft` ou `deprecated`                      |
| `stale_after` | date   | Data de expiração no formato `YYYY-MM-DD`              |

### Regras de validação (T1-T6)

- **T1** — `name` deve estar presente e não vazio
- **T2** — `description` deve ter pelo menos 20 caracteres
- **T3** — `status` deve ser `stable`, `draft` ou `deprecated`
- **T4** — `stale_after` deve ser uma data válida
- **T5** — Conteúdo do arquivo deve ter pelo menos 100 caracteres
- **T6** — A skill deve estar registrada no `knowledge.yaml`

---

## Validando localmente

Antes de enviar, valide as skills localmente:

```bash
cd ia_skills/ia-skill
python scripts/validate_okf.py
```

Saída esperada:
```
Validando skills OKF...
  ✔ lgpd-brasil
  ✔ mantine-ui
  ✔ minha-skill

Skills: 3 | Erros: 0 | Avisos: 0
PASS
```

Se houver erros, corrija antes de fazer o push.

---

## Enviando ao GitLab

```bash
cd ia_skills/ia-skill
git add .
git commit -m "feat: adiciona skill minha-skill"
git push origin main
```

A pipeline de validação dispara automaticamente após o push.

---

## Verificando a pipeline

1. Acesse `http://192.168.15.4/gmontinny/ia-skill/-/pipelines`
2. O job `validate:okf` deve aparecer como **passed** ✔

Se falhar, clique no job para ver o log de erros e corrija o `SKILL.md` ou o `knowledge.yaml`.

### Após a pipeline passar

As skills ficam disponíveis no servidor MCP em até **5 minutos** (TTL do cache).

Para disponibilizar imediatamente, use a ferramenta `reload_skills` na sua IDE:

```
recarregue as skills
```

Ou via API:

```bash
curl -X POST http://192.168.15.4:8000/skills/reload
```
