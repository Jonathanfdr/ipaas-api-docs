#!/usr/bin/env python3
"""Gera uma versão dereferenciada da spec OpenAPI para importação no TOTVS iPaaS.

O importador do iPaaS não resolve `$ref`: um response que aponta para
`#/components/schemas/X` é importado como um único campo `response` do tipo
string, em vez dos campos do objeto. Este script resolve `$ref` e mescla
`allOf`, produzindo `openapi.ipaas.json` a partir de `openapi.json`.

Uso:
    python3 tools/dereference.py brasilapi
    python3 tools/dereference.py --all
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LIMITE_PROFUNDIDADE = 40


def resolver_ponteiro(spec, ref):
    """Resolve um JSON pointer local (#/a/b/c)."""
    if not ref.startswith("#/"):
        raise ValueError(f"$ref externo não suportado: {ref}")
    no = spec
    for parte in ref[2:].split("/"):
        parte = parte.replace("~1", "/").replace("~0", "~")
        if parte not in no:
            raise KeyError(f"$ref não resolve: {ref}")
        no = no[parte]
    return no


def mesclar_all_of(partes):
    """Mescla os membros de um allOf em um único schema."""
    resultado = {"type": "object", "properties": {}}
    requeridos = []
    for parte in partes:
        if parte.get("type") and parte["type"] != "object":
            # allOf sobre tipo escalar: usa o último não-objeto
            resultado = dict(parte)
            continue
        resultado["properties"].update(parte.get("properties", {}))
        requeridos.extend(parte.get("required", []))
        for chave in ("description", "example"):
            if chave in parte and chave not in resultado:
                resultado[chave] = parte[chave]
    if requeridos:
        resultado["required"] = sorted(set(requeridos))
    if not resultado.get("properties"):
        resultado.pop("properties", None)
    return resultado


def dereferenciar(no, spec, profundidade=0, vistos=None):
    if profundidade > LIMITE_PROFUNDIDADE:
        raise RecursionError("profundidade excedida: possível $ref circular")
    vistos = vistos or frozenset()

    if isinstance(no, dict):
        if "$ref" in no:
            ref = no["$ref"]
            if ref in vistos:
                raise RecursionError(f"$ref circular: {ref}")
            alvo = resolver_ponteiro(spec, ref)
            resolvido = dereferenciar(alvo, spec, profundidade + 1, vistos | {ref})
            # preserva irmãos do $ref (ex.: description no ponto de uso)
            irmaos = {k: v for k, v in no.items() if k != "$ref"}
            if irmaos:
                resolvido = {**resolvido, **dereferenciar(irmaos, spec, profundidade + 1, vistos)}
            return resolvido

        if "allOf" in no:
            partes = [dereferenciar(p, spec, profundidade + 1, vistos) for p in no["allOf"]]
            mesclado = mesclar_all_of(partes)
            resto = {k: v for k, v in no.items() if k != "allOf"}
            return {**mesclado, **dereferenciar(resto, spec, profundidade + 1, vistos)}

        return {k: dereferenciar(v, spec, profundidade + 1, vistos) for k, v in no.items()}

    if isinstance(no, list):
        return [dereferenciar(i, spec, profundidade + 1, vistos) for i in no]

    return no


def validar_para_ipaas(spec):
    """Checa os requisitos que o importador do iPaaS impõe."""
    problemas = []
    for caminho, metodos in spec.get("paths", {}).items():
        for metodo, op in metodos.items():
            alvo = f"{metodo.upper()} {caminho}"
            if not op.get("tags"):
                problemas.append(f"{alvo}: sem 'tags' — o import falha com HTTP 500")
            if not op.get("summary"):
                problemas.append(f"{alvo}: sem 'summary' — recurso fica sem nome descritivo")
    return problemas


def processar(pasta: Path):
    origem = pasta / "openapi.json"
    if not origem.exists():
        print(f"  ignorado: {pasta.name} (sem openapi.json)")
        return True

    spec = json.loads(origem.read_text(encoding="utf-8"))
    problemas = validar_para_ipaas(spec)

    plano = dereferenciar(spec, spec)
    plano.pop("components", None)

    if json.dumps(plano, ensure_ascii=False).count('"$ref"'):
        problemas.append("ainda restam $ref após a dereferência")

    destino = pasta / "openapi.ipaas.json"
    destino.write_text(json.dumps(plano, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ops = sum(len(m) for m in plano.get("paths", {}).values())
    print(f"  {pasta.name}: {ops} operações -> {destino.name}")
    for p in problemas:
        print(f"    AVISO {p}")
    return not problemas


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1

    if args == ["--all"]:
        pastas = sorted(
            d for d in RAIZ.iterdir()
            if d.is_dir() and not d.name.startswith((".", "_")) and d.name != "tools"
        )
    else:
        pastas = [RAIZ / a for a in args]

    ok = True
    print("Gerando specs para o iPaaS:")
    for pasta in pastas:
        if not pasta.is_dir():
            print(f"  ERRO {pasta.name}: pasta não encontrada")
            ok = False
            continue
        ok = processar(pasta) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
