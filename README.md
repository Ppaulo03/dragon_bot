# Dragon Bot

Bot de WhatsApp baseado na Evolution API, com FastAPI, triggers configuraveis via YAML e painel web para edicao dos gatilhos.

## O que este projeto faz

- Recebe webhooks da Evolution API e processa mensagens em tempo real.
- Aplica regras de disparo (triggers) por texto, regex, similaridade de imagem ou sempre.
- Responde com texto, audio, sticker ou contato.
- Usa MinIO/S3 para armazenar assets e padroes de imagem.
- Integra APIs externas (gatos, cachorros, quotes, etc) com traducao opcional.

## Arquitetura (alto nivel)

- FastAPI (app principal)
- Evolution API (provedor WhatsApp)
- MinIO (storage para assets e padroes)
- LibreTranslate (traducao opcional)
- Postgres + Redis (backing services da Evolution)
- Dashboard web para editar triggers

## Fluxo de mensagens

1. Evolution envia webhook para /webhook/evolution.
2. A mensagem e adaptada para um formato interno.
3. O TriggerManager avalia as regras (matchers).
4. A acao seleciona a resposta (texto/audio/sticker/contato).
5. A resposta e enviada de volta pela Evolution API.

## Requisitos

- Docker + Docker Compose (recomendado)
- Python 3.13 (para execucao local)
- UV (gerenciador de dependencias Python usado no Dockerfile)

## Configuracao

1. Copie o arquivo de exemplo:

```bash
copy .env.example .env
```

2. Ajuste as variaveis importantes:

- EVOLUTION_URL, EVOLUTION_TOKEN, EVOLUTION_INSTANCE
- EVOLUTION_WEBHOOK_URL (precisa ser alcançavel pela Evolution)
- BUCKET_ENDPOINT, BUCKET_ACCESS_KEY, BUCKET_SECRET_KEY, BUCKET_NAME
- TRANSLATE_URL (opcional)

Para ambiente Docker, use os hosts internos (valores padrao do .env.example).
Para ambiente local, substitua por localhost ou URL publica (ex: ngrok).

## Deploy com Docker (recomendado)

1. Suba a infraestrutura (Postgres, Redis, MinIO, LibreTranslate, Evolution):

```bash
docker compose -f infra.yml up -d
```

3. Suba a aplicacao:

```bash
docker compose up -d --build
```

Opcional: suba tudo com um comando:

```bash
docker compose -f infra.yml up -d ; docker compose up -d
```

### Endpoints principais

- App: http://localhost:8000/
- Painel de triggers: http://localhost:8000/trigger-config
- Login evolution: http://localhost:8000/evolution
- Evolution: http://localhost:8080
- MinIO Console: http://localhost:9001
- LibreTranslate: http://localhost:5000

### Primeiro uso da Evolution

1. Acesse http://localhost:8000/evolution para obter o QR code.
2. Leia o QR code no WhatsApp.
3. O status deve mudar para conectado.

## Execucao local (sem Docker para a app)

1. Ative o ambiente Python e instale dependencias:

```bash
uv sync
```

2. Ajuste a .env para apontar para services locais ou containers.

3. Execute a API:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Se voce rodar apenas a app localmente, mantenha infra.yml ativo via Docker.

## Triggers (config/triggers.yaml)

As regras ficam no arquivo config/triggers.yaml e sao carregadas no boot.
Existe uma lista principal (triggers) e uma lista de fallback (no_triggers).

Campos comuns:

- id: identificador
- name: nome da regra
- type: send_text | send_audio | send_sticker | send_contact
- matcher: text | regex | image_similarity | always
- chance: probabilidade entre 0 e 1
- params: parametros do matcher (ex: pattern, hash, threshold)
- files: lista de arquivos no bucket
- value: texto direto (quando nao usa files)
- action: acao externa (quando aplicavel)

### Acoes externas disponiveis

- cat_api, cat_photo_api
- breaking_bad, motivacional, chuck_norris
- dog_api, advice, bonk, smile
- anime_quote
- meme_contact (acao local)

## Painel web e API interna

- GET /trigger-config: tela para editar gatilhos
- GET /api/internal/config: leitura do YAML
- POST /api/internal/config: atualiza o YAML
- GET /api/internal/constants: lista matchers, actions e tipos

## Storage (MinIO/S3)

- Assets e padroes de trigger sao armazenados no bucket configurado.
- O painel faz upload automatico para a pasta assets/ ou triggers/.
- Arquivos nao utilizados sao removidos na atualizacao.

### Configuracao de Lifecycle Policy (limpeza automatica de midias)

A Evolution API armazena midias recebidas no MinIO. Para evitar preenchimento do storage, recomenda-se configurar uma politica de ciclo de vida que delete arquivos antigos automaticamente.

**Assumindo que MinIO rodando em container dragon-minio-storage:**

1. Defina um alias para acessar o MinIO:

```bash
docker exec dragon-minio-storage mc alias set meu_minio http://localhost:9000 admin admin123
```

(Substitua `admin` e `admin123` pelos valores de MINIO_ROOT_USER e MINIO_ROOT_PASSWORD do seu .env)

2. Configure a politica para expirar arquivos da Evolution apos 1 dia:

```bash
docker exec dragon-minio-storage mc ilm add meu_minio/dragon-bot-bucket --expire-days 1 --prefix "evolution-api/"
```

(Substitua `dragon-bot-bucket` pelo valor de BUCKET_NAME do seu .env)

3. Verifique a configuracao:

```bash
docker exec dragon-minio-storage mc ilm list meu_minio/dragon-bot-bucket
```

**Nota:** ajuste `--expire-days` e `--prefix` conforme necessario. Use `--prefix "assets/"` para limpar assets ou outro prefixo.

## Observacoes importantes

- Se EVOLUTION_WEBHOOK_URL nao for acessivel pela Evolution, o bot nao recebe mensagens.
- Se BUCKET_* nao estiver configurado, o storage e desativado.
- Para rodar em producao, revise tokens e credenciais no .env.

## Arquitetura das Pastas

O projeto segue uma arquitetura em camadas com separacao clara de responsabilidades:

### Raiz do Projeto

- **docker-compose.yml**: Orquestracao do servico principal da aplicacao
- **dockerfile**: Imagem Docker da aplicacao Python
- **infra.yml**: Infraestrutura dos servicos auxiliares (Postgres, Redis, MinIO, LibreTranslate, Evolution)
- **pyproject.toml**: Configuracao de dependencias Python (gerenciado pelo UV)
- **README.md**: Documentacao do projeto
- **config/**: Configuracoes da aplicacao
  - **triggers.yaml**: Arquivo de configuracao dos gatilhos do bot
  - **logs/**: Diretorio para arquivos de log

### src/app/

Codigo-fonte principal da aplicacao.

```
src/app/
├── main.py          # Ponto de entrada do FastAPI e ciclo de vida da aplicacao
├── config.py        # Carregamento de variaveis de ambiente e configuracoes globais
├── core/            # Camada de dominio (regras de negocio)
├── infrastructure/  # Camada de infraestrutura (integracoes externas)
├── utils/           # Utilitarios compartilhados
└── web/             # Camada de apresentacao (API web e dashboard)
```

### src/app/core/ (Dominio)

Contem a logica de negocio e regras de dominio, independente de implementacoes externas.

- **entities/**: Entidades do dominio
  - **trigger.py**: Definicao de triggers, matchers e acoes
- **interfaces/**: Contratos e interfaces
  - **chat.py**: Interface para provedores de chat (WhatsApp)
  - **message.py**: Interface de mensagem generica
- **logic/**: Implementacao da logica de negocio
  - **matchers/**: Implementacao dos tipos de matching
    - **base.py**: Classe base para matchers
    - **implementations.py**: Implementacoes concretas (text, regex, image_similarity, always)
    - **schemas.py**: Schemas de parametros dos matchers
  - **actions/**: Implementacao das acoes de resposta
    - **external.py**: Acoes que consomem APIs externas (cat_api, dog_api, etc)
    - **local.py**: Acoes locais (meme_contact, etc)
  - **response.py**: Interface de construcao de respostas
  - **response_impl.py**: Implementacoes concretas de respostas (texto, audio, sticker, contato)
- **services/**: Servicos de dominio
  - **config_service.py**: Servico de gerenciamento de configuracao dos triggers
  - **trigger_manager.py**: Motor de avaliacao de triggers
  - **factory.py**: Fabrica de criacao de matchers e acoes

### src/app/infrastructure/ (Infraestrutura)

Implementacoes concretas para integracao com servicos externos.

- **network/**: Cliente HTTP base
  - **base_http_client.py**: Cliente HTTP generico para requisicoes externas
- **providers/**: Provedores de servicos especificos
  - **evolution/**: Integracao com Evolution API
    - **adapter.py**: Adaptador de mensagens entre Evolution e formato interno
    - **client.py**: Cliente HTTP para Evolution API
    - **parser.py**: Parser de webhooks da Evolution
    - **route.py**: Roteador para endpoints de webhook
    - **schemas.py**: Schemas Pydantic para Evolution API
    - **template/**: Templates de mensagens Evolution
- **services/**: Servicos de infraestrutura
  - **api_client.py**: Cliente generico para APIs externas
  - **storage.py**: Cliente para MinIO/S3 (gerenciamento de assets)
  - **translate.py**: Cliente para LibreTranslate (traducao opcional)
- **webhooks/**: Processamento de webhooks
  - **evolution.py**: Handler principal de webhooks da Evolution

### src/app/utils/

Utilitarios e funcoes auxiliares compartilhadas.

- **image.py**: Processamento e comparacao de imagens (hashing, similaridade)
- **text.py**: Utilitarios de texto (normalizacao, regex)
- **logging_config.py**: Configuracao centralizada de logging

### src/app/web/ (Apresentacao)

Camada web com API REST e dashboard web.

- **api.py**: Endpoints da API interna (configuracao de triggers)
- **views.py**: Views principais (dashboard, login Evolution)
- **schemas/**: Schemas da API web
  - **view.py**: Schemas de resposta da API de configuracao
- **static/**: Arquivos estaticos (CSS, JavaScript)
- **templates/**: Templates HTML (Jinja2)
- **utils/**: Utilitarios especificos da camada web
- **views/**: Views especializadas (se houver)

### volumes/

Dados persistentes dos containers Docker (nao versionado). Criado automaticamente pelo Docker Compose.

- **evolution_instances/**: Dados das instâncias da Evolution API
- **libretranslate_data/**: Modelos e cache do LibreTranslate
- **minio_data/**: Storage do MinIO
  - **dragon-bot-bucket/**: Bucket principal
    - **assets/**: Assets gerais (audios, stickers, imagens)
    - **evolution-api/**: Midias recebidas/enviadas pela Evolution
    - **triggers/**: Padroes de imagem para triggers com image_similarity
- **postgres_data/**: Dados do banco PostgreSQL (Evolution API)
- **redis_data/**: Dados do Redis (Evolution API)

### Fluxo de Dados entre Camadas

```
Webhook → infrastructure/webhooks → infrastructure/providers/evolution (adapter)
  ↓
core/services/trigger_manager → core/logic/matchers (avaliacao)
  ↓
core/logic/actions → core/logic/response (construcao da resposta)
  ↓
infrastructure/providers/evolution/client (envio) → Evolution API
```

A arquitetura garante que:
- **core/** nunca depende de **infrastructure/** ou **web/**
- **infrastructure/** implementa contratos definidos em **core/interfaces/**
- **web/** orquestra **core/** e **infrastructure/** para expor funcionalidades