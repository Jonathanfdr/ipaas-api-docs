# ipaas-api-docs

Catálogo de especificações OpenAPI de apps de mercado para cadastro no **TOTVS iPaaS**.

Cada app tem uma pasta com a spec, a documentação de cadastro e os metadados. As specs são servidas pelo `raw.githubusercontent.com` e consumidas diretamente pela função **Importar Swagger** do iPaaS, que aceita apenas URL — não upload de arquivo.

> O repositório precisa permanecer **público**. O iPaaS baixa a spec por URL anônima; em repositório privado a importação falha.

## Para cadastrar um app novo

Leia o **[Playbook de cadastro no iPaaS](./IPAAS-PLAYBOOK.md)**, começando pela seção **0 (Arranque rápido)**.

O playbook tem a API completa, os payloads que funcionam, os IDs dos modelos de autenticação, as armadilhas do importador, o checklist de validação, o **estado atual do tenant** (o que já existe, com IDs) e a **fila de próximos apps**.

Em resumo, o caminho é:

```
Aplicativo → Ambiente → [Conta] → Serviço → Importar Swagger → Validar → Diagrama
```

## Apps

| App | Autenticação | Operações | Status |
|---|---|---|---|
| [brasilapi](./brasilapi) | `NO_AUTH` | 16 | importado e validado em diagrama |
| [asaas](./asaas) | `API_KEY` (header `access_token`) | 41 em 3 serviços | importado e validado em diagrama |

## Estrutura

```
IPAAS-PLAYBOOK.md            # referência de cadastro no iPaaS
<nome-do-app>/
├── openapi.json             # spec fonte, mantida com $ref (é esta que você edita)
├── openapi.ipaas.json       # GERADO - spec dereferenciada, é esta que o iPaaS importa
├── ipaas.json               # metadados de cadastro (app, ambientes, contas, serviços)
└── README.md                # como cadastrar e usar no iPaaS
tools/
├── slice_spec.py            # recorta uma spec grande em specs menores, por tag
└── dereference.py           # gera os *.ipaas.json a partir das specs fonte
```

Um app pode ter **várias specs, uma por serviço**, quando a API é grande. Nesse caso o nome carrega o domínio e cada uma gera seu próprio arquivo do iPaaS:

```
asaas/openapi-clientes.json    ->  asaas/openapi-clientes.ipaas.json
asaas/openapi-cobrancas.json   ->  asaas/openapi-cobrancas.ipaas.json
```

Nome da pasta em minúsculas com hífen: `brasilapi`, `asaas`, `sendgrid`.

## Fluxo de trabalho

Quando a API **já tem OpenAPI oficial** (caso do Asaas), recorte por tag e dereferencie:

```bash
curl -sL "<url da spec oficial>" -o /tmp/spec.json
python3 tools/slice_spec.py /tmp/spec.json <app> "Tag A=slug-a" "Tag B=slug-b"
python3 tools/dereference.py <app>
```

Quando **não há spec** (caso da BrasilAPI), escreva o `openapi.json` à mão derivando os schemas de chamadas reais e depois rode:

```bash
python3 tools/dereference.py <app>     # um app
python3 tools/dereference.py --all     # todos
```

O `dereference.py` existe porque o importador do iPaaS **não resolve `$ref`** — sem a dereferência, os campos da resposta se perdem e viram um único campo `response` do tipo string. Ele também valida os requisitos do importador e avisa sobre operações sem `tags` ou `summary`.

## URL de importação

```
https://raw.githubusercontent.com/dugabriel/ipaas-api-docs/main/<app>/openapi.ipaas.json
```

Use `openapi.ipaas.json`, **não** `openapi.json`.

## Convenções das specs

Escreva specs **recortadas por domínio** em vez de copiar a spec oficial inteira. APIs grandes (Stripe, GitHub, Salesforce) têm centenas de endpoints e um serviço com todos eles fica inutilizável na interface do iPaaS. Prefira vários serviços pequenos e coerentes no mesmo app.

Derive os schemas de **respostas reais** da API, não da documentação. Divergência entre doc e comportamento é comum, e o contrato importado é o que os fluxos de integração vão usar. Se um endpoint estiver indisponível, deixe-o fora em vez de documentar sem verificar.

`tags` e `summary` em toda operação. O iPaaS usa esses campos para nomear o recurso importado e a ausência de `tags` faz a importação falhar.

Documente as respostas de erro. Quem constrói a integração precisa saber o formato para tratar falhas.

Não versione credenciais. As contas são cadastradas na interface do iPaaS; `ipaas.json` descreve apenas o **tipo** de autenticação.
