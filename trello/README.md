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

A API do Trello exige **duas** credenciais, ambas em query string:

1. Crie um Power-Up em https://trello.com/power-ups/admin (é o pré-requisito para ter API key).
2. No Power-Up, aba **API Key**, use **Generate a new API Key**.
3. Na mesma tela há o link para gerar o **token** do seu usuário, que autoriza o acesso aos seus dados.

A `key` identifica a aplicação e é considerada pública pela própria Atlassian; o `token` dá acesso aos dados do usuário e **é secreto**. Ambos vão na query de toda requisição:

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

Os schemas que **existem** na spec são bons (o objeto `Board` tem 20+ campos com `example` e `pattern`), então a assimetria é só de cobertura.
