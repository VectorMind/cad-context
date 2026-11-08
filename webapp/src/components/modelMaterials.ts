import * as THREE from 'three';

function surfaceMaterial(flatShading: boolean): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color: '#b7c4d1', metalness: 0.25, roughness: 0.42, flatShading,
  });
}

export function applySurface(object: THREE.Object3D, authoredMaterials = false): void {
  object.traverse(child => {
    const mesh = child as THREE.Mesh;
    if (!mesh.isMesh) return;
    const hasNormals = Boolean(mesh.geometry?.getAttribute('normal'));
    const adapt = (original: THREE.Material): THREE.Material => {
      const material = authoredMaterials && original instanceof THREE.MeshStandardMaterial
        ? original.clone() : surfaceMaterial(!hasNormals);
      if (material instanceof THREE.MeshStandardMaterial) {
        material.flatShading = !hasNormals;
        material.needsUpdate = true;
      }
      original.dispose();
      return material;
    };
    mesh.material = Array.isArray(mesh.material)
      ? mesh.material.map(adapt) : adapt(mesh.material);
  });
}

export function applyWireframe(object: THREE.Object3D, enabled: boolean): void {
  object.traverse(child => {
    const mesh = child as THREE.Mesh;
    if (!mesh.isMesh) return;
    for (const material of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
      if (material instanceof THREE.MeshStandardMaterial) material.wireframe = enabled;
    }
  });
}
