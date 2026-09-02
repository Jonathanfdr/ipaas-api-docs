# BrasilAPI

Dados públicos brasileiros em uma API REST gratuita e **sem autenticação**. Boa candidata para ser o primeiro app do catálogo: valida o fluxo de importação de ponta a ponta sem nenhuma credencial envolvida.

- Site: https://brasilapi.com.br
- Código: https://github.com/BrasilAPI/BrasilAPI
- Base URL: `https://brasilapi.com.br/api`
- Autenticação: nenhuma (`NO_AUTH`)

## Cadastro no iPaaS

### 1. Aplicativo

Em **Ferramentas → Aplicativos → Cadastrar aplicativo**:

| Campo | Valor |
|---|---|
| Nome | `BrasilAPI` |
| Descrição | Dados públicos brasileiros: CEP, CNPJ, bancos, DDD, feriados, IBGE, PIX, taxas, NCM e domínios .br |

### 2. Ambiente

Dentro do app, aba de ambientes:

| Campo | Valor |
|---|---|
| Nome | `Produção` |
| Tipo | `REST` |
| Base path | `https://brasilapi.com.br/api` |
| Autenticação | `NO AUTH` |

O base path **não** deve incluir barra no final. Os paths do OpenAPI já começam com `/`.

### 3. Conta

Não é necessária. Com `NO_AUTH` o ambiente funciona sem conta associada — o app de referência `PetStore` no tenant segue esse mesmo padrão, com ambiente ativo e lista de contas vazia.

### 4. Serviço e importação das APIs

Crie o serviço e use **Importar Swagger** apontando para a URL raw deste repositório:

```
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/brasilapi/openapi.json
```

| Campo | Valor |
|---|---|
| Nome | `Dados Públicos` |
| Ambiente | `Produção` |
| Tipo | `REST` |

A importação aceita **URL**, não upload de arquivo. O repositório precisa continuar público para o iPaaS conseguir baixar a spec.

## Endpoints incluídos

16 operações, todas verificadas contra a API em produção:

| Operação | Método | Path |
|---|---|---|
| Buscar endereço por CEP | GET | `/cep/v1/{cep}` |
| Buscar CEP com geolocalização | GET | `/cep/v2/{cep}` |
| Consultar CNPJ | GET | `/cnpj/v1/{cnpj}` |
| Listar bancos | GET | `/banks/v1` |
| Buscar banco por código | GET | `/banks/v1/{code}` |
| Buscar estado e cidades por DDD | GET | `/ddd/v1/{ddd}` |
| Listar feriados nacionais | GET | `/feriados/v1/{ano}` |
| Listar estados | GET | `/ibge/uf/v1` |
| Buscar estado | GET | `/ibge/uf/v1/{code}` |
| Listar municípios de um estado | GET | `/ibge/municipios/v1/{uf}` |
| Listar participantes do PIX | GET | `/pix/v1/participants` |
| Listar taxas e índices | GET | `/taxas/v1` |
| Buscar taxa por sigla | GET | `/taxas/v1/{sigla}` |
| Listar códigos NCM | GET | `/ncm/v1` |
| Buscar NCM por código | GET | `/ncm/v1/{code}` |
| Consultar domínio .br | GET | `/registrobr/v1/{domain}` |

## Escopo e o que ficou de fora

A BrasilAPI expõe cerca de 88 rotas. Importar todas em um único serviço geraria uma lista difícil de navegar na interface, então esta spec cobre os domínios de maior uso. O restante deve entrar como **serviços separados** no mesmo app, cada um com sua própria spec:

- **FIPE** — `/fipe/*`. Fora desta versão porque a fonte de dados estava indisponível (`Fonte de dados FIPE temporariamente indisponível`) no momento em que os schemas foram levantados. Documentar sem verificar geraria contrato errado.
- **CPTEC** — clima, previsão e ondas.
- **CVM** — corretoras e fundos.
- **Saúde** — hospitais, CID-10, TUSS.
- **Fiscal estendido** — IBPT (LC116, NBS, NCM por UF), CNAE.
- **Diversos** — eleições, universidades, ISBN, câmbio, IGP-M, tickers B3, geolocation, dias úteis.

## Observações de uso

O campo `service` na resposta de CEP indica qual provedor respondeu (`open-cep`, `viacep`, `correios`). A BrasilAPI consulta vários em paralelo e devolve o primeiro que responder, então esse valor varia entre chamadas para o mesmo CEP.

Erros seguem o formato `{ "message", "type", "name" }`. A consulta de CEP acrescenta um array `errors` com o resultado de cada provedor.

`GET /ncm/v1` e `GET /pix/v1/participants` retornam listas grandes, sem paginação. Considere cache nas integrações que usarem esses endpoints.

Não há SLA. É um serviço comunitário e gratuito, e algumas rotas dependem de fontes externas que saem do ar (foi o caso da FIPE). Integrações críticas devem tratar indisponibilidade como cenário esperado, não excepcional.

Alguns campos de CNPJ vêm `null` conforme o cadastro na Receita (`email`, `opcao_pelo_mei`, `pais`). O schema marca esses casos como `nullable`.
