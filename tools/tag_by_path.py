#!/usr/bin/env python3
"""Injeta `tags` nas operações de uma spec OpenAPI a partir do path.

O importador do iPaaS exige `tags` em toda operação: sem elas a importação
falha com HTTP 500 sem indicar a causa. Algumas specs oficiais não têm tags
nenhuma (caso do Trello, com 261 operações sem tag), o que também impede o
recorte por domínio do `slice_spec.py`.

A tag é o primeiro segmento do path (`/boards/{id}/lists` -> `boards`),
opcionalmente renomeado. Operações que já têm `tags` não são alteradas.

Uso:
    python3 tools/tag_by_path.py <spec-origem> <spec-destino> ["<segmento>=<Tag>" ...]

Exemplo:
    python3 tools/tag_by_path.py /tmp/trello.json /tmp/trello_tags.json \\
        "boards=Quadros" "cards=Cartões"
"""

import json
import sys
from pathlib import Path

METODOS = ("get", "post", "put", "delete", "patch", "head", "options")


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 1

    origem, destino, *pares = args
    renomear = {}
    for par in pares:
        if "=" not in par:
            print(f"ERRO formato inválido: {par} (use \"segmento=Tag\")")
            return 1
        seg, tag = par.split("=", 1)
        renomear[seg] = tag

    spec = json.loads(Path(origem).read_text(encoding="utf-8"))

    marcadas = 0
    preservadas = 0
    contagem = {}
    for caminho, metodos in spec.get("paths", {}).items():
        segmento = caminho.strip("/").split("/")[0]
        tag = renomear.get(segmento, segmento)
        for metodo, op in metodos.items():
            if metodo not in METODOS or not isinstance(op, dict):
                continue
            if op.get("tags"):
                preservadas += 1
                continue
            op["tags"] = [tag]
            marcadas += 1
            contagem[tag] = contagem.get(tag, 0) + 1

    if not spec.get("tags"):
        spec["tags"] = [{"name": t} for t in sorted(contagem)]

    Path(destino).write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"{origem} -> {destino}")
    print(f"  {marcadas} operações marcadas, {preservadas} já tinham tags")
    for tag, n in sorted(contagem.items(), key=lambda kv: -kv[1]):
        print(f"    {n:4d}  {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
