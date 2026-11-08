import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from 'three';
import { applySurface, applyWireframe } from '../src/components/modelMaterials.ts';

test('authored GLB colours and matte materials survive lighting and wireframe setup', () => {
  const original = new THREE.MeshStandardMaterial({ color: '#81adbf', metalness: 0, roughness: .9 });
  const object = new THREE.Mesh(new THREE.BoxGeometry(), original);
  applySurface(object, true);
  assert.equal(object.material.color.getHexString(), '81adbf');
  assert.equal(object.material.metalness, 0);
  assert.equal(object.material.roughness, .9);
  assert.notEqual(object.material, original);
  applyWireframe(object, true);
  assert.equal(object.material.wireframe, true);
  assert.equal(object.material.color.getHexString(), '81adbf');
});

test('uncoloured meshes retain the default CAD surface', () => {
  const object = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial());
  applySurface(object, false);
  assert.equal(object.material.color.getHexString(), 'b7c4d1');
});

test('material arrays preserve each colour and toggle wireframe together', () => {
  const object = new THREE.Mesh(new THREE.BoxGeometry(), [
    new THREE.MeshStandardMaterial({ color: '#b6875a' }),
    new THREE.MeshStandardMaterial({ color: '#a4b96b' }),
  ]);
  applySurface(object, true);
  applyWireframe(object, true);
  assert.deepEqual(object.material.map(material => material.color.getHexString()), ['b6875a', 'a4b96b']);
  assert.ok(object.material.every(material => material.wireframe));
});
