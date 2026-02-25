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
docker compose -f infra.yml -f docker-compose.yml up -d --build
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

## Estrutura de pastas (resumo)

- src/app/main.py: entrada do FastAPI e ciclo de vida
- src/app/core: regras de negocio e triggers
- src/app/infrastructure: integracoes (Evolution, storage, translate)
- src/app/web: painel web e API interna
- config/triggers.yaml: regras do bot