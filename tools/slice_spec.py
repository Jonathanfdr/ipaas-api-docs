#!/usr/bin/env python3
"""Recorta uma spec OpenAPI grande em specs menores, uma por tag.

APIs de mercado costumam publicar uma spec única com centenas de operações.
Importar tudo em um serviço só gera uma lista impraticável na interface do
iPaaS, então o recomendado é um serviço por domínio. Este script gera as
specs recortadas mantendo apenas os `components` alcançáveis por cada
recorte.

Uso:
    python3 tools/slice_spec.py <spec-origem> <pasta-destino> "<tag>=<slug>" [...]

Exemplo:
    python3 tools/slice_spec.py /tmp/asaas_openapi.json asaas \\
        "Clientes=clientes" "Cobranças=cobrancas" "Assinaturas=assinaturas"
"""

import json
import sys
from pathlib import Path

METODOS = ("get", "post", "put", "delete", "patch", "head", "options")
LIMITE = 60


def refs_de(no, encontrados):
    """Coleta os $ref locais de um nó, recursivamente."""
    if isinstance(no, dict):
        for k, v in no.items():
            if k == "$ref" and isinstance(v, str) and v.startswith("#/"):
                encontrados.add(v)
            else:
                refs_de(v, encontrados)
    elif isinstance(no, list):
        for i in no:
            refs_de(i, encontrados)


def resolver_ponteiro(spec, ref):
    no = spec
    for parte in ref[2:].split("/"):
        parte = parte.replace("~1", "/").replace("~0", "~")
        if parte not in no:
            return None
        no = no[parte]
    return no


def fechamento(spec, refs_iniciais):
    """Fechamento transitivo dos $ref, tolerante a referência circular."""
    vistos = set()
    fila = list(refs_iniciais)
    while fila:
        ref = fila.pop()
        if ref in vistos:
            continue
        vistos.add(ref)
        alvo = resolver_ponteiro(spec, ref)
        if alvo is None:
            print(f"    AVISO $ref não resolve: {ref}")
            continue
        novos = set()
        refs_de(alvo, novos)
        fila.extend(novos - vistos)
    return vistos


def inserir(destino, ref, valor):
    """Insere um nó no caminho do $ref dentro do dicionário destino."""
    partes = ref[2:].split("/")
    no = destino
    for p in partes[:-1]:
        no = no.setdefault(p, {})
    no[partes[-1]] = valor


def recortar(spec, tag):
    paths = {}
    for caminho, metodos in spec.get("paths", {}).items():
        selecionados = {
            m: op for m, op in metodos.items()
            if m in METODOS and tag in (op.get("tags") or [])
        }
        if selecionados:
            # preserva chaves que nao sao metodo (ex.: parameters no nivel do path)
            comuns = {k: v for k, v in metodos.items() if k not in METODOS}
            paths[caminho] = {**comuns, **selecionados}

    if not paths:
        return None

    refs = set()
    refs_de(paths, refs)
    necessarios = fechamento(spec, refs)

    novo = {
        "openapi": spec.get("openapi", "3.0.1"),
        "info": {
            **spec.get("info", {}),
            "title": f"{spec.get('info', {}).get('title', 'API')} - {tag}",
        },
        "servers": spec.get("servers", []),
        "tags": [t for t in spec.get("tags", []) if t.get("name") == tag],
        "paths": paths,
    }
    if spec.get("security"):
        novo["security"] = spec["security"]

    # securitySchemes nao e alcancado por $ref, mas `security` depende dele
    esquemas = (spec.get("components") or {}).get("securitySchemes")
    if esquemas:
        novo.setdefault("components", {})["securitySchemes"] = esquemas

    for ref in sorted(necessarios):
        alvo = resolver_ponteiro(spec, ref)
        if alvo is not None:
            inserir(novo, ref, alvo)

    return novo


def main():
    args = sys.argv[1:]
    if len(args) < 3:
        print(__doc__)
        return 1

    origem, pasta_destino, *pares = args
    spec = json.loads(Path(origem).read_text(encoding="utf-8"))
    destino = Path(pasta_destino)
    destino.mkdir(parents=True, exist_ok=True)

    disponiveis = set()
    for metodos in spec.get("paths", {}).values():
        for m, op in metodos.items():
            if m in METODOS:
                disponiveis.update(op.get("tags") or [])

    ok = True
    print(f"Recortando {origem}:")
    for par in pares:
        if "=" not in par:
            print(f"  ERRO formato inválido: {par} (use \"Tag=slug\")")
            ok = False
            continue
        tag, slug = par.split("=", 1)
        if tag not in disponiveis:
            print(f"  ERRO tag inexistente: {tag}")
            ok = False
            continue
        novo = recortar(spec, tag)
        ops = sum(
            len([m for m in v if m in METODOS]) for v in novo["paths"].values()
        )
        if ops > LIMITE:
            print(f"    AVISO {ops} operações: acima de {LIMITE}, considere recortar mais")
        arq = destino / f"openapi-{slug}.json"
        arq.write_text(json.dumps(novo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        schemas = len(novo.get("components", {}).get("schemas", {}))
        print(f"  {tag}: {ops} operações, {schemas} schemas -> {arq.name} ({arq.stat().st_size // 1024} KB)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
