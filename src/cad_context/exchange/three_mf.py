"""Geometry-only single-piece 3MF export and independent package inspection."""

from __future__ import annotations

import posixpath
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

from ..types import BackendUnavailable

CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
MODEL_REL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"


def read_metrics(path: Path) -> dict[str, Any]:
    """Read the package's built mesh without repairing topology or losing transforms.

    This intentionally uses ZIP/XML and trimesh, independently of the writer's
    lib3mf wrapper. Component assemblies are outside the single-piece contract.
    """
    import numpy as np
    import trimesh

    try:
        with ZipFile(path) as archive:
            if len(archive.namelist()) != len(set(archive.namelist())):
                raise ValueError("3MF contains duplicate package entries")
            relationships = ET.fromstring(archive.read("_rels/.rels"))
            targets = [
                r.attrib["Target"]
                for r in relationships.findall(f"{REL}Relationship")
                if r.get("Type") == MODEL_REL and r.get("TargetMode") != "External"
            ]
            if len(targets) != 1:
                raise ValueError("3MF requires one internal model relationship")
            target = targets[0].lstrip("/")
            if posixpath.normpath(target) != target or "\\" in target:
                raise ValueError("invalid 3MF model path")
            root = ET.fromstring(archive.read(target))
            content_types = ET.fromstring(archive.read("[Content_Types].xml"))
            model_type = "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"
            if not any(
                c.get("ContentType") == model_type
                and (c.get("PartName") == "/" + target or c.get("Extension") == "model")
                for c in content_types
            ):
                raise ValueError("3MF model content type missing")
    except (BadZipFile, KeyError, ET.ParseError) as exc:
        raise ValueError(f"invalid 3MF package: {exc}") from exc
    if root.tag != f"{CORE}model":
        raise ValueError("invalid 3MF model namespace")
    if root.get("unit") != "millimeter":
        raise ValueError("3MF requires explicit millimeter units")
    resources = root.find(f"{CORE}resources")
    build = root.find(f"{CORE}build")
    if resources is None or build is None:
        raise ValueError("3MF resources/build missing")
    ids = [r.get("id") for r in resources]
    if None in ids or len(ids) != len(set(ids)):
        raise ValueError("3MF resource IDs must be present and unique")
    objects = {o.get("id"): o for o in resources.findall(f"{CORE}object")}
    meshes = [o for o in objects.values() if o.find(f"{CORE}mesh") is not None]
    items = build.findall(f"{CORE}item")
    if len(meshes) != 1 or len(items) != 1:
        raise ValueError("3MF requires exactly one mesh object and one build item")
    obj, item = meshes[0], items[0]
    if item.get("objectid") != obj.get("id") or obj.get("type", "model") != "model":
        raise ValueError("3MF build must reference the printable mesh directly")
    for component in resources.iter(f"{CORE}component"):
        if component.get("objectid") != obj.get("id"):
            raise ValueError("invalid 3MF component reference")
    mesh_xml = obj.find(f"{CORE}mesh")
    vertices = np.array(
        [
            [float(v.attrib[a]) for a in ("x", "y", "z")]
            for v in mesh_xml.findall(f"{CORE}vertices/{CORE}vertex")
        ],
        dtype=float,
    )
    faces = np.array(
        [
            [int(t.attrib[a]) for a in ("v1", "v2", "v3")]
            for t in mesh_xml.findall(f"{CORE}triangles/{CORE}triangle")
        ],
        dtype=np.int64,
    )
    if vertices.ndim != 2 or faces.ndim != 2:
        raise ValueError("3MF mesh is empty")
    if (
        not np.isfinite(vertices).all()
        or faces.min() < 0
        or faces.max() >= len(vertices)
    ):
        raise ValueError("3MF nonfinite coordinates or invalid triangle indices")
    transform = np.eye(4)
    if item.get("transform"):
        values = np.array([float(v) for v in item.get("transform").split()])
        if len(values) != 12 or not np.isfinite(values).all():
            raise ValueError("invalid 3MF build transform")
        transform[:3, :] = values.reshape(4, 3).T
        if abs(np.linalg.det(transform[:3, :3])) < 1e-12:
            raise ValueError("singular 3MF build transform")
    vertex_count = len(vertices)
    # Weld only exactly identical coordinates for adjacency. Avoid trimesh's
    # rounded welding, face removal, winding correction or normal repair.
    vertices, inverse = np.unique(vertices, axis=0, return_inverse=True)
    mesh = trimesh.Trimesh(vertices=vertices, faces=inverse[faces], process=False)
    mesh.apply_transform(transform)
    unique_faces = np.unique(np.sort(mesh.faces, axis=1), axis=0)
    edge_counts = np.bincount(mesh.edges_unique_inverse)
    components = trimesh.graph.connected_components(
        mesh.face_adjacency, nodes=np.arange(len(mesh.faces)), min_len=1
    )
    checks = {
        "units_mm": True,
        "single_mesh_and_build_item": True,
        "connected": len(components) == 1,
        "edge_manifold": bool(np.all(edge_counts == 2)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "positive_volume": bool(mesh.volume > 0),
        "no_duplicate_faces": len(unique_faces) == len(mesh.faces),
        "no_degenerate_faces": bool(mesh.nondegenerate_faces(height=1e-12).all()),
    }
    return {
        "units": "mm",
        "mesh_objects": len(meshes),
        "build_items": len(items),
        "vertices": vertex_count,
        "faces": len(mesh.faces),
        "volume": float(mesh.volume),
        "area": float(mesh.area),
        "bounds_min": mesh.bounds[0].tolist(),
        "bounds_max": mesh.bounds[1].tolist(),
        "watertight": checks["watertight"],
        "checks": checks,
    }


def bounds_match(actual: Any, expected: Any, native_min: Any, native_max: Any) -> bool:
    """Translation-invariant mesh bounds budget, capped by tessellation accuracy."""
    import numpy as np

    from .export3d import LINEAR_TOLERANCE

    extent = np.asarray(native_max) - np.asarray(native_min)
    budget = np.maximum(1e-6, np.minimum(LINEAR_TOLERANCE, 0.01 * extent))
    return bool(np.all(np.abs(np.asarray(actual) - np.asarray(expected)) <= budget))


def write(build_result: Any, path: Path) -> Path:
    """Export a native single solid, validating before atomic publication."""
    import numpy as np

    if build_result.backend != "build123d":
        raise ValueError("3MF export requires a build123d single solid")
    try:
        from build123d import Mesher, Unit

        mesher = Mesher(unit=Unit.MM)
    except (ImportError, OSError) as exc:
        raise BackendUnavailable(f"3MF runtime unavailable: {exc}") from exc
    solids = build_result.native.solids()
    if len(solids) != 1:
        raise ValueError(
            "3MF requires exactly one solid; use separate generators per piece"
        )
    if any(
        len(getattr(build_result.native, topology)())
        != len(getattr(solids[0], topology)())
        for topology in ("faces", "edges", "vertices")
    ):
        raise ValueError("3MF requires one solid without extra shells, faces or wires")
    from .export3d import ANGULAR_TOLERANCE, LINEAR_TOLERANCE

    quality = build_result.tessellation
    try:
        mesher.add_shape(
            solids[0],
            linear_deflection=(
                quality.linear_deflection if quality else LINEAR_TOLERANCE
            ),
            angular_deflection=(
                quality.angular_deflection if quality else ANGULAR_TOLERANCE
            ),
        )
        mesher.write(path)
    except RuntimeError as exc:
        # Malformed geometry must not enter exchange's optional-skip path.
        raise ValueError(f"3MF export failed: {exc}") from exc
    measured = read_metrics(path)
    if not all(measured["checks"].values()):
        raise ValueError(f"3MF topology failed: {measured['checks']}")
    solid = solids[0]
    bbox = solid.bounding_box()
    if not np.isclose(measured["volume"], solid.volume, rtol=0.01, atol=1e-6):
        raise ValueError("3MF volume disagrees with native solid")
    for key, expected in (
        ("bounds_min", list(bbox.min)),
        ("bounds_max", list(bbox.max)),
    ):
        if not bounds_match(measured[key], expected, list(bbox.min), list(bbox.max)):
            raise ValueError(f"3MF {key} disagrees with native solid")
    return path
