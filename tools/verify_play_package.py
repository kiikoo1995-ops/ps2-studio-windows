"""Verify ZIP structure and inventory binary hashes; license review remains separate."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

REQUIRED = {"ps2studio.exe","engine/play/play.exe","engine/play-mesa/play.exe",
            "engine/play-mesa/opengl32.dll"}
for engine in ("play","play-mesa"):
    for name in ("play-license.txt","platforms/qwindows.dll","ps2studio-profile-v1.txt"):
        REQUIRED.add("engine/"+engine+"/"+name)

def verify_package(path):
    files = {}
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            name = entry.filename.replace("\\","/")
            parts = name.rstrip("/").split("/")
            if any(p in ("", ".", "..") or ":" in p for p in parts):
                raise ValueError("Unsafe ZIP path: "+name)
            if entry.is_dir():
                continue
            key = name.casefold()
            if key in files:
                raise ValueError("Duplicate Windows path: "+name)
            if any("pcsx2" in p.casefold() for p in parts) or key.endswith((".iso",".elf",".chd",".pdb")):
                raise ValueError("Unexpected package content: "+name)
            h = hashlib.sha256()
            with archive.open(entry) as f:
                for block in iter(lambda: f.read(1048576), b""):
                    h.update(block)
            files[key] = {"path":name,"size":entry.file_size,"sha256":h.hexdigest()}
    missing = REQUIRED - files.keys()
    if missing:
        raise ValueError("Missing: "+", ".join(sorted(missing)))
    if any(files[x]["size"] == 0 for x in REQUIRED):
        raise ValueError("Empty required file")
    if "engine/play/opengl32.dll" in files:
        raise ValueError("Mesa override leaked into native engine")
    if files["engine/play/play.exe"]["sha256"] != files["engine/play-mesa/play.exe"]["sha256"]:
        raise ValueError("Engine binaries differ")
    return {"status":"structural_checks_passed","file_count":len(files),
            "dependencies":[v for k,v in sorted(files.items()) if k.endswith((".dll",".exe"))],
            "license_review":"pending: match binary inventory to licenses and source obligations",
            "limitations":"No certification of runtime behavior, legal compliance or malware safety."}

if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("zip", type=Path)
    p.add_argument("--output", type=Path)
    a=p.parse_args()
    report=json.dumps(verify_package(a.zip), indent=2)
    if a.output:
        a.output.write_text(report+"\n",encoding="utf-8")
    print(report)
