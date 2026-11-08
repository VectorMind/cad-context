"""Live consumer/navigation checks after project publication and cleanup."""

import io
import json
import urllib.error
import urllib.request
from pathlib import Path

import trimesh

BASE = "http://127.0.0.1:4321"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=120) as response:
        assert response.status == 200
        return response.read(), response.geturl()


def main():
    listing, _ = get("/projects")
    assert b"/projects/animal-puzzle" in listing
    _, redirect = get("/project")
    assert redirect.endswith("/projects")
    page, _ = get("/projects/animal-puzzle")
    assert b"Published models" in page and b"Dated print releases" in page
    working, _ = get("/projects/animal-puzzle/workbench")
    assert b"Local cache working outputs" in working
    manifest = json.loads(
        get("/projects/animal-puzzle/files/web/latest/manifest.json")[0]
    )
    assert len(manifest["models"]) == 4
    models = {}
    for row in manifest["models"]:
        data, _ = get("/projects/animal-puzzle/files/web/latest/" + row["file"])
        scene = trimesh.load(io.BytesIO(data), file_type="glb", force="scene")
        meshes = list(scene.geometry.values())
        assert meshes and all(len(m.vertices) > 0 and len(m.faces) > 0 for m in meshes)
        assert sum(abs(m.volume) for m in meshes) > 0
        models[row["id"]] = {
            "bytes": len(data),
            "meshes": len(meshes),
            "faces": sum(len(m.faces) for m in meshes),
        }
    for row in manifest.get("references", []):
        get("/projects/animal-puzzle/files/web/latest/" + row["file"])
    release = json.loads(
        get("/projects/animal-puzzle/files/3d-print/2026-10-25/release.json")[0]
    )
    assert len(release["files"]) == 4 and release["status"] == "legacy-frozen"
    for name in release["files"]:
        get("/projects/animal-puzzle/files/3d-print/2026-10-25/" + name)
    for path in [
        "/projects/unknown-project",
        "/projects/animal-puzzle/files/README.md",
        "/projects/animal-puzzle/files/../parameters.json",
        "/projects/animal-puzzle/working/parameters.json",
    ]:
        try:
            get(path)
        except urllib.error.HTTPError as exc:
            assert exc.code in (403, 404)
        else:
            raise AssertionError("Unconfined or unknown file served: " + path)
    result = {
        "projects_index": True,
        "legacy_project_redirect": True,
        "published_and_working_modes": True,
        "published_models": models,
        "published_references": len(manifest.get("references", [])),
        "legacy_print_packages": len(release["files"]),
        "file_confinement": True,
    }
    Path(".cache/results/project-publication-live.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
