# ipaas-api-docs

Catálogo de especificações OpenAPI de apps de mercado para cadastro no **TOTVS iPaaS**.

Cada app tem uma pasta com a spec, a documentação de cadastro e os metadados. As specs são servidas pelo `raw.githubusercontent.com` e consumidas diretamente pela função **Importar Swagger** do iPaaS.

> O repositório precisa permanecer **público**. O iPaaS baixa a spec por URL anônima; em repositório privado a importação falha.

## Estrutura

```
<nome-do-app>/
├── openapi.json    # especificação OpenAPI 3.0
├── ipaas.json      # metadados de cadastro (app, ambientes, contas, serviços)
└── README.md       # como cadastrar e usar no iPaaS
```

Nome da pasta em minúsculas com hífen: `brasilapi`, `asaas`, `sendgrid`.

## Apps

| App | Autenticação | Status |
|---|---|---|
| [brasilapi](./brasilapi) | `NO_AUTH` | spec pronta |

## URL de importação

```
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/<app>/openapi.json
```

## Convenções das specs

Escreva specs **recortadas por domínio** em vez de copiar a spec oficial inteira. APIs grandes (Stripe, GitHub, Salesforce) têm centenas de endpoints e um serviço com todos eles fica inutilizável na interface do iPaaS. Prefira vários serviços pequenos e coerentes no mesmo app.

Derive os schemas de **respostas reais** da API, não da documentação. Divergência entre doc e comportamento é comum, e o contrato importado é o que os fluxos de integração vão usar.

Todas as operações precisam de `operationId` único e descritivo — é o que nomeia o recurso importado no iPaaS.

Documente as respostas de erro. Quem constrói a integração precisa saber o formato para tratar falhas.

Não versione credenciais. As contas são cadastradas na interface do iPaaS; `ipaas.json` descreve apenas o **tipo** de autenticação.

## Modelos de autenticação suportados pelo iPaaS

`NO_AUTH`, `BASIC`, `TOKEN`, `API_KEY` (header ou query), `OAUTH1`, `OAUTH2_CLIENT`, `OAUTH2_PASSWORD`, `OAUTH2_CODE`, `NTLM`, `AWS_SIGNATURE`.

Não há modelo para credenciais enviadas no corpo da requisição — o que inviabiliza apps como o Omie, que manda `app_key` e `app_secret` no body.

## Ordem de cadastro no iPaaS

```
Aplicativo → Ambiente (base path + auth) → Conta (credenciais) → Serviço → Importar Swagger
```

A conta é dispensável quando o ambiente usa `NO_AUTH`.
