# Trello

Gestão de trabalho em quadros kanban. É o primeiro app do catálogo com **`API_KEY` em `query`** — os outros usam header.

- Documentação: https://developer.atlassian.com/cloud/trello/rest/
- Spec oficial: `https://developer.atlassian.com/cloud/trello/swagger.v3.json` (OpenAPI 3.0.0, baixa anônima)
- Autenticação: dois parâmetros de **query string**, `key` e `token`

| Ambiente | Base URL |
|---|---|
| Produção | `https://api.trello.com/1` |

Não há sandbox. Crie um workspace/quadro só para teste.

## Obter as credenciais

A API do Trello exige **duas** credenciais, ambas em query string. Cuidado para não confundir com o *secret*, que é uma terceira coisa:

| Credencial | Para que serve |
|---|---|
| **API key** | identifica o Power-Up; vai em `?key=` |
| **Secret** | assinatura OAuth1; o modelo `API_KEY` do iPaaS **não usa** |
| **Token** | autoriza acesso aos dados do usuário; vai em `?token=` |

1. Crie um Power-Up em https://trello.com/power-ups/admin (é o pré-requisito para ter API key).
2. No Power-Up, aba **API Key**, use **Generate a new API Key**.
3. Gere o token autorizando o app:

```
https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&name=TOTVS%20iPaaS&key=<APIKey>
```

`expiration=never` evita que a conta no iPaaS pare de funcionar em 30 dias. `scope=read` basta se o fluxo só consulta.

Passar o secret no lugar do token responde `401 invalid key` — mensagem que não indica a causa. Um token malformado responde `401 invalid app token`, o que serve para confirmar que a `key` está correta.

A `key` é considerada pública pela própria Atlassian; o `token` dá acesso aos dados do usuário e **é secreto**. Ambos vão na query de toda requisição:

```
GET https://api.trello.com/1/members/me/boards?key=<key>&token=<token>
```

## Cadastro no iPaaS

### 1. Aplicativo

| Campo | Valor |
|---|---|
| Nome | `Trello` |
| Descrição | Gestão de trabalho em quadros kanban: quadros, listas, cartões, checklists e membros. |

### 2. Ambiente

| Campo | Valor |
|---|---|
| Nome | `Produção` |
| Tipo | `REST` |
| Base path | `https://api.trello.com/1` |
| Autenticação | `API KEY` |

Os paths das specs são relativos (`/boards/{id}`, `/cards`), então o `/1` fica no base path.

### 3. Conta

| Campo | Valor |
|---|---|
| Nome | `Produção` |
| Tipo de autenticação | `API KEY` |
| Adicionar em | `Query` |
| Chaves | `key` = API key do Power-Up, `token` = token do usuário |

O modelo `API_KEY` do iPaaS aceita **lista** de chaves, então os dois parâmetros vão na mesma conta. É o que diferencia este app dos anteriores, onde a lista tinha um único par.

### 4. Serviços e importação

Cinco serviços, um por domínio:

| Serviço | Operações | Spec |
|---|---|---|
| `Quadros` | 41 | `openapi-quadros.ipaas.json` |
| `Cartões` | 42 | `openapi-cartoes.ipaas.json` |
| `Listas` | 11 | `openapi-listas.ipaas.json` |
| `Checklists` | 12 | `openapi-checklists.ipaas.json` |
| `Membros` | 45 | `openapi-membros.ipaas.json` |

URLs de importação:

```
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/trello/openapi-quadros.ipaas.json
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/trello/openapi-cartoes.ipaas.json
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/trello/openapi-listas.ipaas.json
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/trello/openapi-checklists.ipaas.json
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/trello/openapi-membros.ipaas.json
```

## Como as specs foram geradas

A spec oficial já é OpenAPI 3, mas **nenhuma das 261 operações tem `tags`** — condição em que o importador do iPaaS falha com HTTP 500, e que também impede o recorte por domínio. Por isso há um passo a mais que os outros apps não têm: derivar a tag do primeiro segmento do path.

```bash
curl -sL "https://developer.atlassian.com/cloud/trello/swagger.v3.json" -o /tmp/trello.json

python3 tools/tag_by_path.py /tmp/trello.json /tmp/trello_tags.json \
    "boards=Quadros" "cards=Cartões" "lists=Listas" "checklists=Checklists" "members=Membros"

python3 tools/slice_spec.py /tmp/trello_tags.json trello \
    "Quadros=quadros" "Cartões=cartoes" "Listas=listas" "Checklists=checklists" "Membros=membros"

python3 tools/dereference.py trello
```

A spec do Trello também usa `parameters` no nível do path (34 ocorrências), o que expôs um bug no `dereference.py` — ele tratava toda chave do path item como operação. Corrigido.

## A armadilha que custou a importação: `securitySchemes` em query

A primeira tentativa de importar os 5 serviços falhou com `HTTP 500 FLUIG_CONNECTOR_IMPORT_SWAGGER_500` — a mesma mensagem que o importador dá quando falta `tags`, o que levou a um diagnóstico errado no começo.

A causa real: **o importador não aceita `securitySchemes` de `type: apiKey` com `in: query`**. Basta declarar o esquema para quebrar; não precisa estar referenciado em `security`. Isolado por bissecção:

| Variante testada | Resultado |
|---|---|
| dois esquemas `in: query` (como o Trello publica) | 500 |
| um esquema `in: query` | 500 |
| esquemas `in: query` declarados, `security` ausente | 500 |
| mesmo esquema com `in: header` | 200 |
| sem `securitySchemes` | 200 |

Descartadas no caminho: `oneOf` nos parâmetros, `parameters` no nível do path, respostas sem `content`, quantidade de operações e operações individuais (as 12 do serviço `Checklists` importam uma por uma).

O `dereference.py` passou a remover esses esquemas ao gerar o `.ipaas.json`, avisando no console. As specs fonte mantêm o que o fornecedor publica. Nada se perde em execução: quem injeta `key` e `token` na query é a conta do iPaaS.

## Escrita vai em query, não em corpo

`POST /cards` tem 18 parâmetros, **todos `in: query`**, e nenhum `requestBody`. O mesmo vale para as demais operações de escrita da API. Isso significa que a limitação do importador do iPaaS — que ignora o corpo de POST/PUT — **não afeta este app**: os campos de escrita chegam no `inQuery` do recurso e o diagrama preenche `configurations.inQuery`, sem precisar montar `inBody` à mão.

## Validação

Validado em diagrama (`Valida Trello`, projeto `Validação apps`): 6 steps em série cobrindo 4 dos 5 serviços, execução `DONE` em 8,2s.

| Step | Operação | Resultado |
|---|---|---|
| 1 | `GET /members/me` | usuário autenticado |
| 2 | `GET /boards/{id}` | quadro com `name` e `url` |
| 3 | `GET /boards/{id}/lists` | as 4 listas do quadro |
| 4 | `POST /cards` | cartão criado de verdade, objeto completo na resposta |
| 5 | `GET /cards/{id}` | cartão lido com `inPath` = `{{{id4.id}}}` |
| 6 | `GET /lists/{id}` | lista com `name` |

Isso exercitou o que faltava no catálogo: `API_KEY` em **query** com **duas chaves** na mesma conta, escrita via `inQuery` e encadeamento `{{{idN.campo}}}` entre steps.

O step 3 é a prova prática sobre as respostas sem schema: `GET /boards/{id}/lists` não tem schema na spec oficial e ainda assim devolveu as 4 listas no payload. O contrato ausente afeta o builder, não a execução.

Não foi validado o serviço `Checklists`, cujas 12 operações estão importadas mas não entraram no diagrama.

O quadro usado no teste foi `Meu quadro do Trello`, lista `Hoje`. **Cada execução do diagrama cria um cartão novo** — não há sandbox, então o efeito é na conta real.

## Limitação da spec oficial: respostas sem schema

**91 das 151 operações recortadas não declaram schema de resposta.** Não é problema do recorte nem da dereferência: a spec oficial simplesmente não descreve o retorno dessas operações. A cobertura por serviço:

| Serviço | Com schema | Sem schema |
|---|---|---|
| `Membros` | 29 | 16 |
| `Cartões` | 11 | 31 |
| `Quadros` | 11 | 30 |
| `Listas` | 1 | 10 |
| `Checklists` | 0 | 12 |

Entre as que faltam estão leituras centrais: `GET /boards/{id}/cards`, `GET /lists/{id}`, `GET /checklists/{id}`, `GET /cards/{id}/checklists`.

Consequência prática: o recurso importa e **executa** normalmente, e o payload inteiro continua disponível no diagrama via `{{{idN}}}`. O que se perde é o mapeamento campo a campo na interface do builder — quem montar o fluxo não vê os campos da resposta para escolher, tem que saber o nome de cor.

Os schemas que **existem** na spec são bons (o objeto `Board` tem 20+ campos com `example` e `pattern`), então a assimetria é só de cobertura. Confirmado no iPaaS: `GET /boards/{id}` importou com 26 campos de resposta, `inPath(1)` e `inQuery(16)`; `GET /boards/{id}/cards` importou com 0 campos de resposta.
