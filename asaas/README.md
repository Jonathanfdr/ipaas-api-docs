# Asaas

Plataforma brasileira de cobranças e pagamentos. Boa candidata para o catálogo: autenticação simples (API key em header), sandbox gratuito e independente, e **especificação OpenAPI oficial publicada** pelo próprio fornecedor.

- Documentação: https://docs.asaas.com
- Spec oficial: `https://www.asaas.com/openApi/document?version=3&languageCode=pt-BR`
- Autenticação: `API_KEY` no header `access_token` (**não** usa `Authorization: Bearer`)

| Ambiente | Base URL |
|---|---|
| Sandbox | `https://api-sandbox.asaas.com` |
| Produção | `https://api.asaas.com` |

Os paths das specs já incluem o prefixo `/v3`, então o base path do ambiente **não** deve conter `/v3`.

## Obter a chave de API do sandbox

1. Crie uma conta em https://sandbox.asaas.com (é independente da conta de produção; ter conta em produção não dá acesso ao sandbox).
2. Gere uma chave de API na área de integrações. Apenas usuários administradores podem gerar chave.
3. Use sempre a chave do mesmo ambiente da URL: chave de sandbox só funciona na URL de sandbox.

Contas, dados e chaves não são compartilhados entre sandbox e produção.

## Cadastro no iPaaS

### 1. Aplicativo

| Campo | Valor |
|---|---|
| Nome | `Asaas` |
| Descrição | Plataforma brasileira de cobranças e pagamentos: clientes, cobranças (boleto, Pix, cartão) e assinaturas recorrentes. |

### 2. Ambiente

| Campo | Valor |
|---|---|
| Nome | `Sandbox` |
| Tipo | `REST` |
| Base path | `https://api-sandbox.asaas.com` |
| Autenticação | `API KEY` |

Cadastre também `Produção` com `https://api.asaas.com` quando for para valer.

### 3. Conta

Diferente da BrasilAPI, aqui a conta é **obrigatória** — sem ela as chamadas retornam 401.

| Campo | Valor |
|---|---|
| Nome | `Sandbox` |
| Tipo de autenticação | `API KEY` |
| Adicionar em | `Header` |
| Chave | `access_token` |
| Valor | sua chave de API do sandbox |

Depois de salvar, use **Testar conta** na interface (`GET /accounts/testAccount/{id}` na API) para confirmar que a credencial funciona.

Não versione a chave neste repositório. O `ipaas.json` descreve apenas o formato da autenticação.

### 4. Serviços e importação

Três serviços, um por domínio:

| Serviço | Operações | Spec |
|---|---|---|
| `Clientes` | 7 | `openapi-clientes.ipaas.json` |
| `Cobranças` | 20 | `openapi-cobrancas.ipaas.json` |
| `Assinaturas` | 14 | `openapi-assinaturas.ipaas.json` |

URLs de importação:

```
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/asaas/openapi-clientes.ipaas.json
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/asaas/openapi-cobrancas.ipaas.json
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/asaas/openapi-assinaturas.ipaas.json
```

## Como as specs foram geradas

A spec oficial tem **213 operações em 34 tags** — importar tudo em um serviço só produziria uma lista impraticável. O recorte é feito por tag:

```bash
curl -sL "https://www.asaas.com/openApi/document?version=3&languageCode=pt-BR" -o /tmp/asaas_openapi.json

python3 tools/slice_spec.py /tmp/asaas_openapi.json asaas \
    "Clientes=clientes" "Cobranças=cobrancas" "Assinaturas=assinaturas"

python3 tools/dereference.py asaas
```

A spec oficial já atende aos requisitos do importador do iPaaS: todas as 213 operações têm `tags`, `summary` e `operationId`, e não há `allOf`. Só faltava dereferenciar os 1139 `$ref`.

## Domínios ainda não importados

O recorte atual cobre o núcleo de cobranças. Os demais domínios da spec oficial, por volume de operações:

`Cobranças com dados resumidos` (11), `Link de pagamentos` (11), `Parcelamentos` (10), `Informações fiscais` (10), `Negativações` (9), `Informações e personalização da conta` (9), `Subcontas Asaas` (9), `Antecipações` (8), `Pix` (8), `Pix Automático` (7), `Conta Escrow` (6), `Notas fiscais` (6), `Configurações de Webhooks` (6), `Documentos de cobranças` (5), `Transações Pix` (5), `Pix Recorrente` (5), `Transferências` (5), `Pagamento de contas` (5), `Recargas de celular` (5), `Envio de documentos White Label` (5), `Splits` (4), `Cartão de crédito` (3), `Chargeback` (3), `Consulta Serasa` (3), `Informações financeiras` (3), `Ações em sandbox` (3), `Checkout` (2), `Estornos` (2), `Notificações` (2), `Extrato` (1), `Registro de Recebíveis` (1).

Para adicionar qualquer um, basta incluir o par `"Tag=slug"` no comando de recorte e criar o serviço correspondente.

## Observações

Os schemas vêm da **spec oficial do fornecedor**, não de chamadas à API. Isso difere da BrasilAPI, onde não havia spec e os schemas foram derivados de respostas reais. Confirmei que a base URL do sandbox responde e que sem a chave retorna `401`, mas os payloads de resposta não foram verificados contra a API por falta de credencial de sandbox.

`POST /v3/payments` e `POST /v3/payments/` (com barra final) existem os dois na spec oficial, assim como em assinaturas. É duplicação da origem, mantida no recorte para não divergir da spec publicada.

O sandbox tem comportamentos próprios: aprovação automática de contas, confirmação manual de cobranças e cartões fictícios. Nem toda funcionalidade tem a mesma cobertura de produção — vale conferir "O que pode ser testado" na documentação antes de homologar.
