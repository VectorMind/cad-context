/**
 * 3D preview for GLB (primary) and STL (fallback).
 *
 * The loader is deliberately manual rather than `useGLTF`: each regeneration
 * hands us a new URL for the same fixed artifact path, and drei's cache would
 * keep every previous version alive. Here the old object is disposed the
 * moment a new one arrives.
 *
 * Exports carry raw CAD coordinates — millimetres, Z-up
 * (`specifications/exchange-formats/spec.md`) — so the model sits in a group
 * rotated -90° about X to read as Z-up in three.js's Y-up world.
 */
import { Grid, OrbitControls } from '@react-three/drei';
import { Canvas, useThree } from '@react-three/fiber';
import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';

export interface ModelViewProps {
  url: string | null;
  format: string;
  wireframe: boolean;
  showGrid: boolean;
  /** Bumping this refits the camera to the current model. */
  fitToken: number;
}

interface Loaded {
  object: THREE.Object3D;
  radius: number;
  height: number;
  url: string;
}

function disposeObject(object: THREE.Object3D): void {
  object.traverse((child) => {
    const mesh = child as THREE.Mesh;
    if (!mesh.isMesh) return;
    mesh.geometry?.dispose();
    const material = mesh.material;
    if (Array.isArray(material)) material.forEach((m) => m.dispose());
    else material?.dispose();
  });
}

function surfaceMaterial(flatShading: boolean): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color: '#b7c4d1',
    metalness: 0.25,
    roughness: 0.42,
    flatShading,
  });
}

/**
 * Give every mesh a lit surface.
 *
 * GLB written by trimesh carries positions and indices only — no NORMAL
 * attribute — and a mesh without normals is shaded as if every face pointed
 * the same way, which is what makes a part look like one flat silhouette.
 * Where normals are missing, the material switches to flat shading: three
 * derives the true per-face normal in the shader, which is also the right look
 * for a faceted CAD part. A file that does carry normals keeps them.
 */
function applySurface(object: THREE.Object3D): void {
  object.traverse((child) => {
    const mesh = child as THREE.Mesh;
    if (!mesh.isMesh) return;
    const hasNormals = Boolean(mesh.geometry?.getAttribute('normal'));
    mesh.material = surfaceMaterial(!hasNormals);
  });
}

async function loadModel(url: string, format: string): Promise<Loaded> {
  let object: THREE.Object3D;
  if (format === 'stl') {
    const geometry = await new STLLoader().loadAsync(url);
    object = new THREE.Mesh(geometry);
  } else {
    const gltf = await new GLTFLoader().loadAsync(url);
    object = gltf.scene;
  }
  applySurface(object);
  const box = new THREE.Box3().setFromObject(object);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  object.position.sub(center); // orbit around the part, not around the origin
  return {
    object,
    radius: Math.max(size.length() / 2, 1),
    height: Math.max(size.z, 1),
    url,
  };
}

/**
 * Camera framing.
 *
 * A full fit happens on the first model and whenever "fit view" is pressed.
 * After that a regenerated part only rescales the camera distance by how much
 * the part grew or shrank: the viewing angle the user orbited to survives a
 * parameter change, and the part stays in frame.
 */
function FitCamera({ radius, token }: { radius: number; token: number }) {
  const camera = useThree((state) => state.camera);
  const controls = useThree((state) => state.controls) as unknown as
    | { target: THREE.Vector3; update: () => void }
    | undefined;
  const previousRadius = useRef<number | null>(null);
  const previousToken = useRef(token);

  useEffect(() => {
    const previous = previousRadius.current;
    if (previous === null || token !== previousToken.current) {
      const distance = radius * 2.8;
      camera.position.set(distance * 0.75, distance * 0.55, distance * 0.85);
      controls?.target.set(0, 0, 0);
    } else if (previous !== radius) {
      camera.position.multiplyScalar(radius / previous);
    }
    if (camera instanceof THREE.PerspectiveCamera) {
      camera.near = Math.max(radius / 200, 0.01);
      camera.far = radius * 200;
      camera.updateProjectionMatrix();
    }
    controls?.update();
    previousRadius.current = radius;
    previousToken.current = token;
  }, [camera, controls, radius, token]);
  return null;
}

export default function ModelView({ url, format, wireframe, showGrid, fitToken }: ModelViewProps) {
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const fittedFor = useRef<string | null>(null);
  const [autoFit, setAutoFit] = useState(0);

  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    setLoading(true);
    loadModel(url, format)
      .then((next) => {
        if (cancelled) {
          disposeObject(next.object);
          return;
        }
        setError(null);
        setLoaded(next); // the previous object is disposed by the effect below
        // Fit once per generator: later regenerations keep the user's view.
        if (fittedFor.current === null) {
          fittedFor.current = url;
          setAutoFit((n) => n + 1);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : String(cause));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [url, format]);

  useEffect(() => {
    if (!loaded) return;
    loaded.object.traverse((child) => {
      const mesh = child as THREE.Mesh;
      if (!mesh.isMesh) return;
      const material = mesh.material as THREE.MeshStandardMaterial;
      material.wireframe = wireframe;
    });
  }, [loaded, wireframe]);

  useEffect(() => {
    if (!loaded) return;
    return () => disposeObject(loaded.object);
  }, [loaded]);

  const gridProps = useMemo(() => {
    const radius = loaded?.radius ?? 100;
    return {
      cellSize: Math.max(1, 10 ** Math.round(Math.log10(radius / 10))),
      sectionSize: Math.max(10, 10 ** Math.round(Math.log10(radius))),
      fadeDistance: radius * 9,
    };
  }, [loaded]);

  return (
    <div className="viewport">
      <Canvas
        camera={{ fov: 45, position: [200, 150, 200] }}
        dpr={[1, 2]}
        gl={{ alpha: true, antialias: true }}
        style={{ background: 'transparent' }}
      >
        {/*
          Three-point rig plus a sky/ground hemisphere. Directional lights are
          positioned in world space, so each face of a part picks up a
          different amount of each one — that difference is what reads as
          shape. Intensities are tuned against the flat-shaded metal surface
          above; keep the key clearly dominant or the part flattens again.
        */}
        <hemisphereLight args={['#e6eefa', '#141922', 0.9]} />
        <ambientLight intensity={0.18} />
        <directionalLight position={[60, 90, 70]} intensity={2.6} />
        <directionalLight position={[-80, 35, -40]} intensity={0.85} color="#a8c6ff" />
        <directionalLight position={[10, -60, -70]} intensity={0.3} color="#ffe6cc" />
        {loaded && (
          <>
            <group rotation={[-Math.PI / 2, 0, 0]}>
              <primitive object={loaded.object} />
            </group>
            {showGrid && (
              <Grid
                position={[0, -loaded.height / 2, 0]}
                args={[loaded.radius * 8, loaded.radius * 8]}
                cellSize={gridProps.cellSize}
                sectionSize={gridProps.sectionSize}
                cellColor="#3a4653"
                sectionColor="#55708a"
                fadeDistance={gridProps.fadeDistance}
                infiniteGrid
                followCamera={false}
              />
            )}
            <FitCamera radius={loaded.radius} token={fitToken + autoFit} />
          </>
        )}
        <OrbitControls makeDefault enableDamping dampingFactor={0.12} />
      </Canvas>
      {!loaded && !error && (
        <p className="viewport-note">{loading ? 'loading model…' : 'waiting for geometry…'}</p>
      )}
      {error && <p className="viewport-note error">{error}</p>}
    </div>
  );
}
