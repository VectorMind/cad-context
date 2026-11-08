"""Authored solid colours survive native assembly tessellation and GLB readback."""

import json
import struct

import pytest

from cad_context import exchange
from cad_context.types import BuildResult


def test_colored_assembly_preserves_parts_colors_and_global_placement(tmp_path, cache):
    import trimesh
    from build123d import Color, Compound, Location, Solid

    bear = Solid.make_box(2, 3, 4)
    bear.label = "bear"
    bear.color = Color("#b6875a")
    turtle = Solid.make_box(1, 2, 3).moved(Location((5, 0, 0)))
    turtle.label = "turtle"
    turtle.color = Color("#a4b96b")
    native = Compound(children=[bear, turtle]).moved(Location((10, 0, 0)))
    expected = native.volume
    result = BuildResult(
        generator="colored-test",
        backend="build123d",
        kind="3d",
        params={},
        native=native,
    )
    output = exchange.export(result, ["glb"], out_dir=tmp_path, measure=False)
    assert not output["skipped"]
    data = output["files"]["glb"].read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20 : 20 + length])
    assert len(gltf["meshes"]) == 2
    assert len(gltf["materials"]) == 2
    factors = []
    for material in gltf["materials"]:
        pbr = material["pbrMetallicRoughness"]
        assert pbr["metallicFactor"] == 0
        assert pbr["roughnessFactor"] == pytest.approx(0.9)
        factors.append(pbr["baseColorFactor"])
    assert factors[0] != factors[1]
    scene = trimesh.load(output["files"]["glb"], force="scene")
    assert scene.bounds[0] == pytest.approx([10, 0, 0])
    assert scene.bounds[1] == pytest.approx([16, 3, 4])
    assert sum(mesh.volume for mesh in scene.geometry.values()) == pytest.approx(
        expected
    )
    assert native.volume == expected
