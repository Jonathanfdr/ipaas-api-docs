# Brevo

Plataforma de marketing e mensageria (ex-Sendinblue): contatos, e-mail transacional, campanhas de e-mail, SMS e WhatsApp. Boa candidata para o catálogo: autenticação simples (API key em header), plano gratuito permanente e **especificação oficial publicada** pelo fornecedor.

- Documentação: https://developers.brevo.com
- Spec oficial: `https://api.brevo.com/v3/swagger_definition_v3.yml` (**exige `api-key`**, não baixa anônima)
- Espelho público da mesma spec: `https://raw.githubusercontent.com/getbrevo/brevo-go/main/api/swagger.yaml`
- Autenticação: `API_KEY` no header `api-key` (**não** usa `Authorization: Bearer`)

| Ambiente | Base URL |
|---|---|
| Produção | `https://api.brevo.com/v3` |

Não há sandbox separado — a conta é uma só. O e-mail transacional tem um **modo sandbox por header** (ver Validação, abaixo), que valida a chamada sem enviar e-mail de verdade.

## Obter a chave de API

1. Crie uma conta em https://app.brevo.com (plano gratuito permanente, sem cartão; o limite é de 300 e-mails por dia).
2. Gere a chave em **Settings → API Keys**: https://app.brevo.com/settings/keys/api
3. A chave vai no header `api-key` de toda requisição.

O header `partner-key` existe na spec oficial, é opcional e serve apenas para parceiros. Ele foi **removido** dos recortes deste repositório, senão o importador criaria esse header em todos os recursos importados como campo inútil.

## Cadastro no iPaaS

### 1. Aplicativo

| Campo | Valor |
|---|---|
| Nome | `Brevo` |
| Descrição | Plataforma de marketing e mensageria: contatos e listas, e-mails transacionais, campanhas de e-mail e SMS transacional. |

### 2. Ambiente

| Campo | Valor |
|---|---|
| Nome | `Produção` |
| Tipo | `REST` |
| Base path | `https://api.brevo.com/v3` |
| Autenticação | `API KEY` |

Os paths das specs são relativos (`/contacts`, `/smtp/email`), então o `/v3` fica no base path do ambiente.

### 3. Conta

Obrigatória — sem ela as chamadas retornam 401.

| Campo | Valor |
|---|---|
| Nome | `Produção` |
| Tipo de autenticação | `API KEY` |
| Adicionar em | `Header` |
| Chave | `api-key` |
| Valor | sua chave de API |

Não versione a chave neste repositório. O `ipaas.json` descreve apenas o formato da autenticação.

### 4. Serviços e importação

Quatro serviços, um por domínio:

| Serviço | Operações | Spec |
|---|---|---|
| `Contatos` | 29 | `openapi-contatos.ipaas.json` |
| `E-mails Transacionais` | 22 | `openapi-emails-transacionais.ipaas.json` |
| `Campanhas de E-mail` | 13 | `openapi-campanhas-email.ipaas.json` |
| `SMS Transacional` | 4 | `openapi-sms-transacional.ipaas.json` |

URLs de importação:

```
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/brevo/openapi-contatos.ipaas.json
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/brevo/openapi-emails-transacionais.ipaas.json
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/brevo/openapi-campanhas-email.ipaas.json
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/brevo/openapi-sms-transacional.ipaas.json
```

## Como as specs foram geradas

A spec oficial está em **Swagger 2.0**, e o importador do iPaaS só aceita OpenAPI 3 — em 2.0 ele quebra com HTTP 500 e NPE no backend. Por isso há um passo de conversão que os outros apps deste repositório não têm:

```bash
# 1. baixar (o endpoint oficial exige api-key; o espelho do SDK Go é a mesma spec, aberta)
curl -sL "https://raw.githubusercontent.com/getbrevo/brevo-go/main/api/swagger.yaml" -o /tmp/brevo_swagger.yaml
python3 -c "import yaml,json;json.dump(yaml.safe_load(open('/tmp/brevo_swagger.yaml')),open('/tmp/brevo_swagger.json','w'),ensure_ascii=False)"

# 2. converter Swagger 2.0 -> OpenAPI 3.0.3
npx -y swagger2openapi@7 --outfile /tmp/brevo_oas3.json --targetVersion 3.0.3 /tmp/brevo_swagger.json

# 3. remover o partner-key opcional de `security` e `components.securitySchemes`
#    (senão vira header extra em todo recurso importado)

# 4. recortar por tag e dereferenciar
python3 tools/slice_spec.py /tmp/brevo_oas3.json brevo \
    "Contacts=contatos" \
    "Transactional emails=emails-transacionais" \
    "Email Campaigns=campanhas-email" \
    "Transactional SMS=sms-transacional"

python3 tools/dereference.py brevo
```

Depois da conversão, a spec atende aos requisitos do importador: as 233 operações têm `tags` e `summary`, e o `dereference.py` não emitiu nenhum aviso.

## Validação

Validado em diagrama (`Valida Brevo`, projeto `Validação apps`): 6 steps em série cobrindo 3 dos 4 serviços, execução `DONE` em 9,4s.

| Step | Operação | Resultado |
|---|---|---|
| 1 | `GET /contacts` | 1 contato, com `attributes` e `listIds` |
| 2 | `GET /contacts/lists` | 1 lista, com contadores de inscritos |
| 3 | `GET /smtp/templates` | vazio (conta nova) |
| 4 | `POST /smtp/email` | `messageId` do relay, sem envio real |
| 5 | `GET /smtp/statistics/aggregatedReport` | 16 contadores do período |
| 6 | `GET /emailCampaigns` | vazio (conta nova) |

O envio usa o **modo sandbox**: o `POST /smtp/email` aceita `X-Sib-Sandbox: drop` **dentro do corpo**, em `headers`. A resposta é `201` com `messageId`, nenhum e-mail é enviado, nenhum log é criado e a chamada não conta nas estatísticas (`requests: 0` no dia da execução).

Como o importador do iPaaS não traz o corpo de POST/PUT, o corpo vai em `configurations.inBody` no diagrama:

```json
{
  "sender": { "name": "TOTVS", "email": "<remetente verificado na conta>" },
  "to": [{ "email": "<destinatario>", "name": "Destinatário" }],
  "subject": "Teste iPaaS Brevo",
  "htmlContent": "<p>Validação do app Brevo no iPaaS</p>",
  "headers": { "X-Sib-Sandbox": "drop" }
}
```

O remetente precisa estar verificado na conta Brevo (`GET /senders` lista os ativos), senão o envio falha independentemente do modo sandbox.

### O que não foi validado

O serviço `SMS Transacional` **não pôde ser exercitado**. Todos os endpoints respondem `500 invalid_request`, com ou sem parâmetros, porque o plano gratuito não tem crédito de SMS — `GET /account` mostra apenas `{"type":"free","credits":300,"creditsType":"sendLimit"}`. Os 4 recursos estão importados e corretos; falta uma conta com SMS habilitado para confirmar os schemas.

## Restrição de IP no lado da Brevo

A Brevo tem allowlist de IP própria, independente da chave. Com ela restritiva, **qualquer** cliente recebe `401` com `unrecognised IP address <ip>` e `code: unauthorized`, mesmo com chave válida — inclusive o iPaaS, cujo IP de saída você não controla.

Configuração em https://app.brevo.com/security/authorised_ips, com três modos: autorização automática (a Brevo libera após checagem), notificação por e-mail (aprovação manual por IP) e bloqueio de IPs desconhecidos.

Se um fluxo começar a dar 401 sem explicação, verifique essa tela antes de suspeitar da credencial.

## Domínios ainda não importados

O recorte atual cobre contatos e mensageria. Os demais domínios da spec oficial, por volume de operações:

`Master account` (24), `Ecommerce` (17), `Reseller` (16), `Deals` (11), `SMS Campaigns` (10), `WhatsApp Campaigns` (9), `Conversations` (9), `Senders` (7), `Companies` (7), `Webhooks` (6), `User` (6), `Tasks` (6), `Domains` (5), `Notes` (5), `Files` (5), `Coupons` (5), `External Feeds` (5), `Inbound Parsing` (3), `Payments` (3), `Account` (2), `Process` (2), `Transactional WhatsApp` (2), `Events` (1).

Para adicionar qualquer um, inclua o par `"Tag=slug"` no comando de recorte e crie o serviço correspondente. `Master account` e `Reseller` só fazem sentido para contas de agência/revenda.

O CRM da Brevo (`Deals`, `Companies`, `Tasks`, `Notes`) é o complemento mais óbvio para cenário de ERP — 29 operações somadas.

## Observações

Os schemas vêm da **spec oficial do fornecedor**, convertida de Swagger 2.0. Os retornos de contatos, listas, estatísticas de e-mail e campanhas foram confirmados na execução do diagrama; os demais não foram conferidos contra respostas reais.

`GET /smtp/emailStatus/{batchId}` e `GET /smtp/emailStatus/{messageId}` são o mesmo path com nomes de parâmetro diferentes na spec oficial. Mantido como está para não divergir da origem, mas no iPaaS os dois recursos apontam para a mesma rota.

O plano gratuito limita a 300 e-mails por dia e não permite remetente sem verificação. Para homologar envio real, verifique o domínio ou pelo menos o e-mail remetente antes.
