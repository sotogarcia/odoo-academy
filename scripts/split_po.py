from __future__ import annotations

import copy
import sys
from pathlib import Path

try:
    import polib
except ImportError:
    print("ERROR: No está instalado el paquete 'polib'.")
    print()
    print("Instálalo ejecutando:")
    print("    pip install polib")
    print()
    input("Pulsa Intro para cerrar...")
    sys.exit(1)


def is_fully_translated(entry: polib.POEntry) -> bool:
    """
    Devuelve True si la entrada está completamente traducida
    y no está marcada como fuzzy.
    """
    if entry.obsolete:
        return False

    if "fuzzy" in entry.flags:
        return False

    # Entrada con plurales
    if entry.msgid_plural:
        if not entry.msgstr_plural:
            return False

        return all(value.strip() for value in entry.msgstr_plural.values())

    # Entrada normal
    return bool(entry.msgstr.strip())


def create_po_from(source: polib.POFile) -> polib.POFile:
    """
    Crea un PO nuevo conservando cabecera, metadatos y configuración
    del archivo original.
    """
    result = polib.POFile(
        encoding=source.encoding,
        wrapwidth=source.wrapwidth,
    )

    result.metadata = copy.deepcopy(source.metadata)
    result.header = source.header

    return result


def split_po(file_path: Path) -> None:
    print(f"\nProcesando: {file_path}")

    if not file_path.exists():
        print(f"ERROR: El archivo no existe: {file_path}")
        return

    if file_path.suffix.lower() != ".po":
        print(f"ERROR: No es un archivo .po: {file_path}")
        return

    try:
        po = polib.pofile(str(file_path))
    except Exception as exc:
        print(f"ERROR al leer el archivo: {exc}")
        return

    translated = create_po_from(po)
    pending = create_po_from(po)

    translated_count = 0
    untranslated_count = 0
    fuzzy_count = 0
    obsolete_count = 0

    for entry in po:
        if entry.obsolete:
            obsolete_count += 1
            continue

        if is_fully_translated(entry):
            translated.append(copy.deepcopy(entry))
            translated_count += 1
        else:
            pending.append(copy.deepcopy(entry))

            if "fuzzy" in entry.flags:
                fuzzy_count += 1
            else:
                untranslated_count += 1

    translated_path = file_path.with_name(f"{file_path.stem}_translated.po")
    pending_path = file_path.with_name(f"{file_path.stem}_pending.po")

    translated.save(str(translated_path))
    pending.save(str(pending_path))

    print()
    print("Resultado:")
    print(f"  Traducidas:      {translated_count}")
    print(f"  Sin traducir:    {untranslated_count}")
    print(f"  Fuzzy:           {fuzzy_count}")
    print(f"  Obsoletas:       {obsolete_count} (excluidas)")
    print()
    print(f"  -> {translated_path.name}")
    print(f"  -> {pending_path.name}")


def main() -> None:
    # Permite arrastrar uno o varios archivos .po sobre el script.
    if len(sys.argv) > 1:
        paths = [Path(arg.strip('"')) for arg in sys.argv[1:]]
    else:
        print("Separador de archivos PO")
        print("========================")
        print()
        value = input("Introduce la ruta del archivo .po: ").strip().strip('"')

        if not value:
            return

        paths = [Path(value)]

    for path in paths:
        split_po(path)

    print()
    input("Pulsa Intro para cerrar...")


if __name__ == "__main__":
    main()
