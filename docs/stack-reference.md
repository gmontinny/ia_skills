# Referência Técnica — GitLab CE Stack

## Sumário

- [Pré-requisitos](#pré-requisitos)
- [Estrutura de arquivos](#estrutura-de-arquivos)
- [Serviços e ordem de inicialização](#serviços-e-ordem-de-inicialização)
- [Configuração antes de subir](#configuração-antes-de-subir)
- [Subindo do zero (passo a passo)](#subindo-do-zero-passo-a-passo)
- [Acompanhando a inicialização](#acompanhando-a-inicialização)
- [Verificando o runner](#verificando-o-runner)
- [Reiniciar do zero](#reiniciar-do-zero)
- [Backup manual](#backup-manual)
- [Decisões de arquitetura](#decisões-de-arquitetura)
- [Problemas conhecidos e soluções](#problemas-conhecidos-e-soluções)

---

## Pré-requisitos

- Docker Engine 24+ com Docker Compose plugin
- `/var/run/docker.sock` acessível no host (necessário para o `gitlab-setup`)
- IP fixo na rede local (ex: `192.168.15.4`)
- Mínimo recomendado: 4 GB RAM, 20 GB disco

---

## Estrutura de arquivos

```
.
├── docker-compose.yml
├── .env
├── gitlab-config/
│   └── gitlab.rb               # Configuração estática montada como bind mount
├── gitlab-init/
│   └── Dockerfile              # Alpine + curl + bash; executa init-gitlab.sh
├── runner/
│   └── Dockerfile              # gitlab-runner + Java 21 + Python 3 + Node 20 + Docker CLI
├── scripts/
│   ├── setup-gitlab.sh         # Cria PAT via docker exec no container gitlab
│   ├── init-gitlab.sh          # Obtém runner token e desabilita signup via API
│   └── register-runner.sh      # Registra o runner e inicia o processo
└── docs/
    └── stack-reference.md      # Este documento
```

---

## Serviços e ordem de inicialização

| Serviço         | Imagem                    | Restart  | Descrição                                                 |
|-----------------|---------------------------|----------|-----------------------------------------------------------|
| `gitlab`        | `gitlab/gitlab-ce:latest` | always   | GitLab CE com healthcheck em `/users/sign_in`             |
| `gitlab-setup`  | `docker:24-cli`           | no       | Cria PAT de admin via `docker exec gitlab gitlab-rails`   |
| `gitlab-init`   | custom (alpine)           | no       | Obtém runner token e desabilita signup via API REST        |
| `dind`          | `docker:24-dind`          | always   | Docker-in-Docker sem TLS, escuta em `tcp://0.0.0.0:2375`  |
| `gitlab-runner` | custom                    | always   | Runner auto-registrado, conecta ao dind via TCP sem TLS   |

### Grafo de dependências

```
gitlab (healthy)
    └── gitlab-setup (completed)
            └── gitlab-init (completed)
                    └── gitlab-runner
dind (started)
    └── gitlab-runner
```

O Compose aguarda cada condição antes de iniciar o próximo serviço.

---

## Configuração antes de subir

### 1. `gitlab-config/gitlab.rb`

Edite com seu IP e senha antes de qualquer `docker compose up`:

```ruby
external_url 'http://SEU_IP'
gitlab_rails['gitlab_shell_ssh_port'] = 2222
gitlab_rails['initial_root_password'] = 'SuaSenha'
gitlab_rails['initial_shared_runners_registration_token'] = 'initial-runner-token'
```

Regras para a senha (GitLab 19.x):
- Mínimo 8 caracteres
- Não pode conter palavras comuns do dicionário
- Não pode conter `$` (causa interpolação no Docker Compose)
- Use sequências aleatórias: ex. `Xk9mP2vL7nQ4wRst`

> O arquivo é montado como bind mount em `/etc/gitlab/gitlab.rb`.
> Isso evita o problema de interpolação de variáveis do `GITLAB_OMNIBUS_CONFIG`.

### 2. `.env`

```bash
GITLAB_HOSTNAME=192.168.15.4
GITLAB_EXTERNAL_URL=http://192.168.15.4
SSH_PORT=2222

GITLAB_ROOT_PASSWORD=Xk9mP2vL7nQ4wRst
GITLAB_ROOT_EMAIL=admin@example.com
GITLAB_ROOT_NAME=Administrator

RUNNER_NAME=docker-dind-runner
RUNNER_TAGS=docker,java,python,nodejs,vuejs,react,dind
RUNNER_CONCURRENT=4
```

> `GITLAB_ROOT_PASSWORD` no `.env` é apenas referência — a senha real que o GitLab usa
> é a definida em `gitlab.rb`. Mantenha os dois sincronizados.

---

## Subindo do zero (passo a passo)

### Passo 1 — Configurar IP e senha

```bash
# Edite com seu IP e senha
notepad gitlab-config/gitlab.rb   # Windows
# ou
nano gitlab-config/gitlab.rb      # Linux/macOS
```

### Passo 2 — Subir a stack

```bash
docker compose up -d
```

O Compose constrói as imagens customizadas (`gitlab-init`, `gitlab-runner`) na primeira vez.
Isso pode levar alguns minutos dependendo da conexão.

### Passo 3 — Aguardar o GitLab ficar healthy

O GitLab executa migrations de banco no primeiro boot. Pode levar **5 a 15 minutos**.

```bash
docker logs -f gitlab
```

Aguarde aparecer:
```
gitlab Reconfigured!
```

O healthcheck confirma quando o serviço está pronto (verifica `/users/sign_in` a cada 60s,
com `start_period` de 600s).

### Passo 4 — Acompanhar o gitlab-setup

Após o GitLab ficar healthy, o `gitlab-setup` cria o PAT de admin:

```bash
docker logs -f gitlab-setup
```

Saída esperada:
```
[gitlab-setup] Aguardando gitlab-rails ficar pronto...
[gitlab-setup] PAT salvo com sucesso.
```

O PAT é salvo em `/shared-config/admin-pat` (volume `shared_config`).

### Passo 5 — Acompanhar o gitlab-init

```bash
docker logs -f gitlab-init
```

Saída esperada:
```
[gitlab-init] GitLab está pronto!
[gitlab-init] PAT válido!
[gitlab-init] Token do runner salvo: initial-runner-token
[gitlab-init] Signup desabilitado.
[gitlab-init] Inicialização concluída!
```

### Passo 6 — Acompanhar o registro do runner

```bash
docker logs -f gitlab-runner
```

Saída esperada:
```
[runner-register] Token encontrado!
[runner-register] API disponível!
[runner-register] Registrando runner com token: initial-runner-token
[runner-register] Runner registrado com sucesso!
[runner-register] config.toml atualizado.
[runner-register] Iniciando gitlab-runner...
```

### Passo 7 — Acessar o GitLab

- URL: `http://SEU_IP`
- Usuário: `root`
- Senha: valor de `initial_root_password` em `gitlab.rb`

### Passo 8 — Verificar o runner

`Admin Area > CI/CD > Runners`

O runner `docker-dind-runner` deve aparecer como **online** com as tags:
`docker, java, python, nodejs, vuejs, react, dind`

---

## Acompanhando a inicialização

Todos os serviços de uma vez (requer `docker compose` 2.x):

```bash
docker compose logs -f
```

Ou por serviço:

```bash
docker logs -f gitlab
docker logs -f gitlab-setup
docker logs -f gitlab-init
docker logs -f gitlab-runner
docker logs -f gitlab-dind
```

---

## Verificando o runner

```bash
# Status do container
docker ps | grep gitlab-runner

# Logs em tempo real
docker logs -f gitlab-runner

# Verificar config.toml gerado
docker exec gitlab-runner cat /home/gitlab-runner/.gitlab-runner/config.toml
```

---

## Reiniciar do zero

> Use `--reset` apenas quando: mudar senha, mudar IP, runner duplicado, ou qualquer problema
> de inicialização parcial. No uso normal, preserve os dados.

```bash
bash start.sh           # religar sem perder dados (uso normal)
bash start.sh --reset   # apagar tudo e subir do zero
```

O `--reset` executa `docker compose down -v` antes de subir, removendo os volumes:
- `gitlab_data` — banco PostgreSQL e dados do GitLab
- `gitlab_runner_config` — `config.toml` do runner
- `shared_config` — PAT e runner token
- `dind_storage` — camadas Docker do dind

Sem `--reset`, o GitLab não re-executa o seed e todos os repositórios e configurações são preservados.

---

## Backup manual

```bash
docker exec -it gitlab gitlab-backup create
# Arquivo salvo em: /var/opt/gitlab/backups/
```

Para copiar o backup para o host:

```bash
docker cp gitlab:/var/opt/gitlab/backups/<arquivo>.tar .
```

---

## Decisões de arquitetura

### Por que `gitlab.rb` como bind mount?

O bloco `GITLAB_OMNIBUS_CONFIG` no `docker-compose.yml` sofre interpolação de variáveis
pelo Docker Compose. Qualquer `$` na configuração (ex: senhas, tokens) é interpretado
como variável de ambiente e trunca o valor. O bind mount de um arquivo estático elimina
esse problema completamente.

### Por que `docker exec` para criar o PAT?

O GitLab 19.x removeu a autenticação Basic Auth da API REST. Não é possível criar o
primeiro PAT via API sem já ter um PAT. A solução é usar `gitlab-rails runner` dentro
do container `gitlab` para criar o PAT diretamente no banco, via `docker exec`.

### Por que dind sem TLS?

O `docker:24-dind` gera certificados TLS com o hostname do container (ex: `60c66981c0e8`)
como SAN, mas não inclui o alias de rede `dind`. O runner tenta conectar em `https://dind:2376`
e o certificado é rejeitado por não ser válido para esse hostname.

Solução: rodar o dind com `--tls=false` na porta `2375`. A comunicação ocorre dentro da
rede Docker interna `gitlab_net`, sem exposição externa.

### Por que verificar `config.toml` antes de registrar?

O runner persiste o `config.toml` no volume `gitlab_runner_config`. Se o container
reiniciar sem `down -v`, o script detecta o arquivo existente e pula o registro,
evitando runners duplicados no GitLab.

### Por que `--docker-network-mode ia_skills_gitlab_net`?

Os jobs do runner precisam se comunicar com o GitLab (para clonar repositórios, reportar
status). Ao usar a mesma rede `gitlab_net`, os containers de job resolvem `gitlab` pelo
alias de rede interno, sem depender de DNS externo ou IP do host.

---

## Problemas conhecidos e soluções

### TLS: `certificate is valid for ..., not dind`

**Causa**: dind gerou cert sem o alias `dind` como SAN.  
**Solução**: já resolvido — dind roda com `--tls=false` na porta `2375`.  
**Não fazer**: tentar passar `DOCKER_TLS_HOSTNAME` ou montar certs manualmente.

### `network ia_skills_gitlab_net not found`

**Causa**: o `--docker-network-mode` no registro do runner aponta para a rede do host (`ia_skills_gitlab_net`), mas os jobs são executados pelo daemon do **dind**, que é um Docker separado e não enxerga redes do host.  
**Solução**: já resolvido — `--docker-network-mode` removido do registro do runner. Os jobs usam a rede padrão do dind.  
**Não fazer**: tentar passar o nome da rede do Compose para o runner.

### GitLab demora para ficar healthy

**Causa**: migrations de banco no primeiro boot.  
**Solução**: aguardar. O `start_period: 600s` dá 10 min antes de contar falhas.  
**Se demorar mais**: verificar RAM disponível. Com menos de 4 GB o PostgreSQL fica lento.

### `gitlab-setup` falha ao criar PAT

**Causa**: `docker exec` via socket não está acessível.  
**Verificar**:
```bash
docker exec gitlab-setup docker ps   # deve listar containers
```
**Solução**: garantir que `/var/run/docker.sock` está montado no host e acessível.

### Runners duplicados

**Causa**: reinicialização parcial sem `down -v` — o volume `gitlab_runner_config` foi
removido mas o runner já estava registrado no GitLab.  
**Solução**:
```bash
docker compose down -v && docker compose up -d
```
Ou remover manualmente em `Admin Area > CI/CD > Runners`.

### Pipeline falha com `exec format error`

**Causa**: imagem do job incompatível com a arquitetura do host (ex: `amd64` vs `arm64`).  
**Solução**: usar imagens multi-arch ou especificar `--platform` no `docker pull`.

### Senha rejeitada pelo GitLab

**Causa**: GitLab 19.x rejeita senhas com palavras comuns ou muito simples.  
**Solução**: usar sequência aleatória sem palavras do dicionário. Ex: `Xk9mP2vL7nQ4wRst`.  
**Lembrar**: fazer `down -v` após mudar a senha no `gitlab.rb`.
