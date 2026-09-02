# Playbook - Cadastro de apps no TOTVS iPaaS

Referência operacional para cadastrar um novo app de mercado no iPaaS. Contém a API real, os payloads que funcionam, as armadilhas já descobertas e o checklist de validação.

**Como usar:** ao pedir o cadastro de um app novo, aponte para este arquivo. Ele substitui a fase de descoberta — a API abaixo foi mapeada a partir do bundle do front-end e validada com chamadas reais.

Tudo marcado como **verificado** foi executado com sucesso. O que ainda não foi exercitado está marcado como **não verificado** — trate como hipótese.

---

## 1. Contexto do ambiente

| Item | Valor |
|---|---|
| Front-end | `https://ipaas.totvs.app` |
| API | `https://api-ipaas.totvs.app` |
| Tenant usado | `iPaaS Gateway` (produção) |
| Repositório de specs | `github.com/dugabriel/ipaas-api-docs` (público) |

### Autenticação da API

O token JWT da sessão do navegador serve como Bearer nas chamadas. Ele está no cookie `jwt.token` e vale cerca de 48 horas.

```js
const token = document.cookie.match(/(?:^|;\s*)jwt\.token=([^;]+)/)[1];
const headers = {
  authorization: 'Bearer ' + token,
  accept: 'application/json',
  'content-type': 'application/json'
};
```

Executar as chamadas de dentro da página autenticada evita lidar com login, SSO e MFA. Não é necessário extrair nem armazenar a credencial em nenhum lugar.

---

## 2. Sequência de cadastro

```
Aplicativo → Ambiente → [Conta] → Serviço → Importar Swagger → Validar
```

A conta é dispensável quando o ambiente usa `NO_AUTH` (verificado na BrasilAPI).

### 2.1 Criar o aplicativo — verificado

`POST /ipaas/api/v3/applications` → **201**

```json
{
  "name": "BrasilAPI",
  "description": "Dados públicos brasileiros: CEP, CNPJ, bancos..."
}
```

A resposta traz o id no campo **`componentId`**, não `id`. É esse valor que os passos seguintes usam como `applicationId`.

Não envie `category`: o endpoint `/v4/applications/categories` retorna 404 e nenhum dos 70 apps do tenant usa esse campo.

### 2.2 Criar o ambiente — verificado

`POST /ipaas/api/v2/environments` → **200**

```json
{
  "name": "Produção",
  "type": "REST",
  "baseURL": "https://brasilapi.com.br/api",
  "applicationId": "<componentId do app>",
  "authModelIds": ["d6a952f5-7ce3-44e4-af8e-8697c3ef4b37"],
  "active": true
}
```

O campo de vínculo é **`authModelIds`** (lista de IDs). Enviar `authModels` com objetos é aceito sem erro e **não vincula nada** — o ambiente fica silenciosamente sem autenticação.

`baseURL` sem barra no final, porque os paths do OpenAPI já começam com `/`.

A resposta do POST devolve `active: false` mesmo quando você envia `true`. É só o retorno; um GET seguido mostra `active: true`. Não tente "corrigir".

Para editar depois: `PUT /ipaas/api/v2/environments/{id}` com o mesmo corpo.

### 2.3 Criar a conta — não verificado

`POST /ipaas/api/v3/accounts`

Ainda não exercitado, porque o primeiro app usa `NO_AUTH`. O formato provável combina `componentId`, `environmentId`, o id do auth model e os campos do `inputSchema` do tipo escolhido (seção 3). **Antes de cadastrar em lote, capture o POST real** criando uma conta pela interface com a aba de rede aberta.

Validação: `GET /ipaas/api/v3/accounts/testAccount/{id}` testa a conexão de verdade.

### 2.4 Criar o serviço — verificado

`POST /ipaas/api/v3/application-services` → **201**

```json
{
  "name": "Dados Públicos",
  "description": "Consultas de CEP, CNPJ, bancos...",
  "applicationId": "<componentId do app>",
  "environmentId": "<id do ambiente>",
  "resourceType": "REST",
  "icon": "product"
}
```

Ícones vistos em uso: `product`, `light-bulb`, `adb`. A lista completa de valores válidos não foi levantada.

### 2.5 Importar o Swagger — verificado

`POST /ipaas/api/v3/rest-resources/import-swagger` → **200** com corpo vazio

```json
{
  "applicationId": "<componentId do app>",
  "serviceId": "<id do serviço>",
  "endPoint": "https://raw.githubusercontent.com/.../openapi.ipaas.json",
  "swaggerEndPoint": "https://raw.githubusercontent.com/.../openapi.ipaas.json",
  "update": true
}
```

O campo obrigatório é **`swaggerEndPoint`**. Omiti-lo retorna 400 com `NotEmpty` apontando o campo. Mande `endPoint` com o mesmo valor, que é o que o front faz.

Sucesso é **200 com corpo vazio** — não há resumo do que foi importado. Só a listagem de recursos confirma o resultado.

Para SOAP o equivalente é `POST /ipaas/api/v3/soap-resources/import-wsdl` com `soapEndPoint` (não verificado).

### 2.6 Validar — verificado

```
GET /ipaas/api/v3/rest-resources?serviceId={id}&fields=id&fields=name&page=1&pageSize=9999
GET /ipaas/api/v3/resources?serviceId={id}&id={resourceId}&expand=properties&expand=model
```

Confira: a contagem de recursos bate com a de operações da spec, e `properties.responseBody.restResourceBodyObjects` tem os campos do objeto — e não um único `response` do tipo string, que é o sintoma de `$ref` não resolvido.

---

## 3. Modelos de autenticação

IDs globais do tenant, iguais para qualquer app. Consulta: `GET /ipaas/api/v2/auth-models?page=1&pageSize=999`.

| Tipo | ID | Campos (\* = obrigatório) |
|---|---|---|
| `NO_AUTH` | `d6a952f5-7ce3-44e4-af8e-8697c3ef4b37` | — |
| `BASIC` | `4a4d0fa1-2933-438d-a6ac-36432bc2cf42` | `username*`, `password*` |
| `TOKEN` | `3ce568bb-e05a-4186-b650-9faa63c46041` | `token*` |
| `API_KEY` | `e90e6f18-c1bb-4170-9d10-5e45be5314c6` | `addTo*` (`header`/`query`), `keys` (lista de `key`/`value`) |
| `OAUTH1` | `e5e4bb18-0f2b-4e3e-be33-412fab6a6b2b` | `consumerKey*`, `consumerSecret*`, `accessToken*`, `tokenSecret*` |
| `OAUTH2_CLIENT` | `45ff3eb3-111f-4a35-b665-579519a1c87e` | `accessTokenURL*`, `client_id*`, `client_secret*`, `clientAuth*`, `scope`, `grant_type` |
| `OAUTH2_PASSWORD` | `9afef6ed-83f3-4293-ba3a-37bf6df6d8cf` | `accessTokenURL*`, `username*`, `password*`, `client_id*`, `client_secret*`, `clientAuth*` |
| `OAUTH2_CODE` | `158e40cb-53b4-4381-95a7-4857b7156019` | `authURL*`, `accessTokenURL*`, `code*`, `client_id*`, `client_secret*`, `clientAuth*` |
| `NTLM` | `0d5bba8e-d15e-4cb6-bfd4-7904fbb8cb61` | `username*`, `password*`, `domain`, `workstation` |
| `AWS_SIGNATURE` | `240ecfed-628f-436b-be67-5e8984bfcf39` | `accessKey*`, `secretKey*`, `awsRegion*`, `serviceName*`, `sessionToken` |

`clientAuth` aceita `header` (Basic Auth header) ou `body` (credenciais no corpo).

**Não existe modelo para credenciais no corpo da requisição.** Isso inviabiliza apps como o **Omie**, que manda `app_key` e `app_secret` no body de cada chamada. Ficam de fora até haver uma abordagem específica.

Priorize apps `NO_AUTH`, `BASIC`, `TOKEN` e `API_KEY`. Os fluxos OAuth2 authorization code exigem interação de navegador para obter o `code` e não são automatizáveis em lote — caso do **Bling v3**.

---

## 4. Requisitos e armadilhas do importador

Todos verificados na prática. Nenhum está documentado publicamente.

**`tags` é obrigatório em toda operação.** Sem `tags`, a importação falha com HTTP 500 e `FLUIG_CONNECTOR_IMPORT_SWAGGER_500`, sem indicar a causa. Confirmado por bissecção: a mesma spec sem tags dá 500, com tags dá 200.

**`$ref` não é resolvido.** Response apontando para `#/components/schemas/X` é importado como um único campo `response` do tipo string e os campos do objeto se perdem. Vale para objetos e arrays de objetos. Solução: `tools/dereference.py`.

**`allOf` também precisa ser resolvido.** Mesmo motivo; o script mescla os membros.

**O nome do recurso é `{MÉTODO} - {tag} - {path} - {summary}`.** O `operationId` é ignorado. `tags` e `summary` são o que determina a legibilidade da lista na interface.

**`number` pode virar `string`.** Um campo `number` foi importado como `string`; `integer` foi preservado. Prefira `integer` para valores inteiros.

**Parâmetros de path viram `{{{param}}}`.** Formato de template do iPaaS, esperado.

**Cache do `raw.githubusercontent` tem TTL de alguns minutos.** Após um push, a URL de branch pode servir a versão antiga, e query string não contorna. Para importar algo recém-publicado, use a URL por commit SHA, que é imutável:

```
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/<sha>/<app>/openapi.ipaas.json
```

**O repositório precisa ser público.** O iPaaS baixa a spec anonimamente.

**A importação aceita apenas URL, não upload de arquivo.** É a razão de existir este repositório.

---

## 5. Receita para um app novo

1. **Escolher o app** priorizando auth simples (seção 3) e verificar se há sandbox gratuita para testar a conta.
2. **Criar a pasta** `<app>/` em minúsculas com hífen.
3. **Levantar os endpoints** da fonte mais confiável disponível: spec oficial, ou o código do serviço, ou a documentação. Recortar por domínio — não importar centenas de endpoints num serviço só.
4. **Chamar a API real** para derivar os schemas de resposta. Não confiar na documentação. Se um endpoint estiver indisponível, deixá-lo fora em vez de documentar sem verificar.
5. **Escrever `openapi.json`** com `tags` e `summary` em toda operação, `$ref` livre (o script resolve), e as respostas de erro documentadas.
6. **Gerar a spec do iPaaS**: `python3 tools/dereference.py <app>`.
7. **Escrever `ipaas.json`** e `README.md` seguindo o padrão da `brasilapi/`.
8. **Commit e push**, e guardar o SHA do commit.
9. **Cadastrar** seguindo a seção 2, usando a URL por SHA na importação.
10. **Validar** conforme 2.6 e conferir na interface.

### Antes de cadastrar em lote

Faça **um** app inteiro primeiro e valide na tela. Só então repita. Criar app, ambiente e serviço são operações com `DELETE` disponível, então erros são reversíveis:

```
DELETE /ipaas/api/v3/applications/{id}
DELETE /ipaas/api/v2/environments/{id}
DELETE /ipaas/api/v3/application-services/{id}
DELETE /ipaas/api/v3/accounts/{id}
```

Lembre que o tenant em uso é **produção**. Confirme antes de criar em lote.

---

## 6. Tornar o app global

Duas rotas diferentes, com implicações distintas:

**`POST /ipaas/api/v4/applications/{id}/request-native`** (corpo `null`) — solicita que o app entre no catálogo nativo. É uma **solicitação**, sujeita a aprovação de terceiros; não é um switch. O app passa a ter `requestedNative: true`.

**`POST /ipaas/api/v4/applications/{id}/share`** — compartilha diretamente com uma lista de tenants, sem depender de aprovação. Para remover: `PUT /ipaas/api/v4/applications/{id}/remove-share` com `{ "tenantIds": [...] }`.

Se o objetivo é distribuir para clientes específicos agora, use `share`. Se é entrar no catálogo do produto, use `request-native` e aguarde. Nenhum dos dois foi executado ainda — **não verificado**.

---

## 7. Referência de endpoints

```
# Aplicativos
GET    /ipaas/api/v3/applications?page=1&pageSize=9999&expand=favorite,categories,shares,sharedWithUser,createdDate,status
POST   /ipaas/api/v3/applications
PUT    /ipaas/api/v3/applications/{id}
DELETE /ipaas/api/v3/applications/{id}
GET    /ipaas/api/v4/applications/{id}?includeFields=isCustom&includeFields=isShared&includeFields=requestedNative
PATCH  /ipaas/api/v4/applications/{id}                     # { favorite: bool }
POST   /ipaas/api/v4/applications/{id}/request-native
POST   /ipaas/api/v4/applications/{id}/share
PUT    /ipaas/api/v4/applications/{id}/remove-share        # { tenantIds: [] }
POST   /storage/api/v1/assets/upload?tags={nome}&publicFile=false   # multipart, ícone

# Ambientes
GET    /ipaas/api/v2/environments/?applicationId={id}&expand=authModels&expand=diagrams&expand=accounts&expand=environmentsChild
GET    /ipaas/api/v2/environments/{id}?expand=authModels
POST   /ipaas/api/v2/environments
PUT    /ipaas/api/v2/environments/{id}
PATCH  /ipaas/api/v2/environments/{id}                     # [{ op:"replace", path:"/disconnect", value:bool }]
DELETE /ipaas/api/v2/environments/{id}

# Autenticação
GET    /ipaas/api/v2/auth-models?page=1&pageSize=999

# Contas
GET    /ipaas/api/v3/accounts?componentId={appId}&includeFields=diagrams
GET    /ipaas/api/v3/accounts/details/{id}?expand=environments&expand=diagrams
GET    /ipaas/api/v3/accounts/testAccount/{id}
POST   /ipaas/api/v3/accounts
PUT    /ipaas/api/v3/accounts/{id}
PATCH  /ipaas/api/v3/accounts/{id}                         # [{ op:"replace", path:"/active", value:bool }]
DELETE /ipaas/api/v3/accounts/{id}

# Serviços
GET    /ipaas/api/v3/application-services?applicationId={id}
GET    /ipaas/api/v3/application-services/{id}
POST   /ipaas/api/v3/application-services
PUT    /ipaas/api/v3/application-services/{id}
DELETE /ipaas/api/v3/application-services/{id}

# Recursos e importação
GET    /ipaas/api/v3/rest-resources?serviceId={id}&fields=id&fields=name&page=1&pageSize=9999
GET    /ipaas/api/v3/resources?serviceId={id}&id={resourceId}&expand=properties&expand=model
POST   /ipaas/api/v3/rest-resources/import-swagger         # { applicationId, serviceId, endPoint, swaggerEndPoint, update }
POST   /ipaas/api/v3/rest-resources/schemas
GET    /ipaas/api/v3/soap-resources?serviceId={id}
POST   /ipaas/api/v3/soap-resources/import-wsdl            # { applicationId, serviceId, endPoint, soapEndPoint, update }
```

---

## 8. Histórico

| App | Auth | Operações | Resultado |
|---|---|---|---|
| BrasilAPI | `NO_AUTH` | 16 | 16 recursos importados e validados |
