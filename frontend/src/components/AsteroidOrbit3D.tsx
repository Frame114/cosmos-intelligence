import { Pause, Play, RotateCw } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import type { AsteroidOrbitMapObject, AsteroidOrbitMapResponse } from "../types";

const AU_KM = 149_597_870.7;
const LD_KM = 384_400;

function pointAtTime(item: AsteroidOrbitMapObject, jdTdb?: number) {
  return jdTdb == null ? undefined : item.points.find((point) => Math.abs(point.jd_tdb - jdTdb) < 0.00001);
}

function AsteroidScene({ data, selectedId, currentIndex, onSelect, onError }: {
  data: AsteroidOrbitMapResponse;
  selectedId?: string;
  currentIndex: number;
  onSelect: (neoId: string) => void;
  onError: (error: string | null) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const selectedRef = useRef(selectedId);
  const indexRef = useRef(currentIndex);
  const onSelectRef = useRef(onSelect);
  const renderObjectsRef = useRef<Array<{ item: AsteroidOrbitMapObject; marker: THREE.Mesh; line: THREE.Line }>>([]);
  const sceneScale = useMemo(() => {
    const maxDistance = Math.max(...data.objects.flatMap((item) => item.points.map((point) => point.distance_au)), 0.02);
    return 4.4 / maxDistance;
  }, [data]);

  useEffect(() => { selectedRef.current = selectedId; }, [selectedId]);
  useEffect(() => { indexRef.current = currentIndex; }, [currentIndex]);
  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
    } catch {
      onError("This browser could not start WebGL for the 3D orbit viewer.");
      return;
    }
    onError(null);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(host.clientWidth, host.clientHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.setClearColor(0x06111e, 1);
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x06111e, 0.018);
    const camera = new THREE.PerspectiveCamera(45, host.clientWidth / host.clientHeight, 0.01, 150);
    camera.up.set(0, 0, 1);
    // Start from a clear oblique angle so the distance shells read as 3D
    // volumes, while leaving the ecliptic plane and vertical component visible.
    camera.position.set(8, -10, 5.2);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0, 0);
    controls.enableZoom = true;
    controls.zoomSpeed = 1.05;
    controls.enableDamping = true;
    controls.dampingFactor = 0.07;
    controls.minDistance = 0.4;
    controls.maxDistance = 45;
    controls.screenSpacePanning = true;
    controls.update();

    scene.add(new THREE.AmbientLight(0xb2d8ea, 1.5));
    const light = new THREE.PointLight(0xffedc7, 36, 70);
    light.position.set(4, -5, 8);
    scene.add(light);

    const stars = new THREE.BufferGeometry();
    const starPositions = new Float32Array(1_050 * 3);
    let seed = 24_031;
    const random = () => { seed = (seed * 16_807) % 2_147_483_647; return seed / 2_147_483_647; };
    for (let i = 0; i < 1_050; i += 1) {
      const radius = 30 + random() * 60;
      const theta = random() * Math.PI * 2;
      const z = random() * 2 - 1;
      const planar = Math.sqrt(1 - z * z);
      starPositions[i * 3] = radius * planar * Math.cos(theta);
      starPositions[i * 3 + 1] = radius * planar * Math.sin(theta);
      starPositions[i * 3 + 2] = radius * z;
    }
    stars.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
    const starField = new THREE.Points(stars, new THREE.PointsMaterial({ color: 0x8eb9cc, size: 0.055, transparent: true, opacity: 0.7, sizeAttenuation: true }));
    scene.add(starField);

    const mapGroup = new THREE.Group();
    scene.add(mapGroup);
    const grid = new THREE.GridHelper(10, 20, 0x27435a, 0x1b3045);
    grid.rotation.x = Math.PI / 2;
    const gridMaterial = grid.material as THREE.Material;
    gridMaterial.transparent = true;
    gridMaterial.opacity = 0.22;
    mapGroup.add(grid);

    const maxRadius = Math.max(...data.objects.flatMap((item) => item.points.map((point) => point.distance_au)), 0.01);
    for (const lunarDistances of [1, 10, 50, 100, 500]) {
      const radius = lunarDistances * LD_KM / AU_KM * sceneScale;
      if (radius > maxRadius * sceneScale * 1.08) continue;
      const shell = new THREE.Mesh(
        new THREE.SphereGeometry(radius, 36, 20),
        new THREE.MeshBasicMaterial({ color: 0x5d879f, transparent: true, opacity: 0.13, wireframe: true, depthWrite: false }),
      );
      shell.userData.lunarDistances = lunarDistances;
      mapGroup.add(shell);
    }

    const earth = new THREE.Mesh(new THREE.SphereGeometry(0.085, 32, 24), new THREE.MeshStandardMaterial({ color: 0x43a8cf, emissive: 0x0c4565, emissiveIntensity: 0.4, roughness: 0.58, metalness: 0.08 }));
    earth.name = "Earth";
    const earthGlow = new THREE.Mesh(new THREE.SphereGeometry(0.125, 24, 16), new THREE.MeshBasicMaterial({ color: 0x48d5ea, transparent: true, opacity: 0.09, side: THREE.BackSide }));
    mapGroup.add(earth, earthGlow);

    const diameters = data.objects.map((item) => item.diameter_km).filter((value): value is number => typeof value === "number" && value > 0);
    const minDiameter = diameters.length ? Math.min(...diameters) : 0.001;
    const maxDiameter = Math.max(...diameters, minDiameter);
    const markers: Array<{ item: AsteroidOrbitMapObject; marker: THREE.Mesh; line: THREE.Line }> = [];
    for (const item of data.objects) {
      const points = item.points.map((point) => new THREE.Vector3(point.x_au * sceneScale, point.y_au * sceneScale, point.z_au * sceneScale));
      const color = item.potentially_hazardous === true ? 0xf1ad72 : item.potentially_hazardous === false ? 0x77dce5 : 0xa5b4c5;
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.43 }));
      line.userData.neoId = item.neo_id;
      mapGroup.add(line);
      const diameter = item.diameter_km && item.diameter_km > 0 ? item.diameter_km : minDiameter;
      const relative = maxDiameter > minDiameter ? Math.log10(diameter / minDiameter) / Math.log10(maxDiameter / minDiameter) : 0.4;
      const marker = new THREE.Mesh(new THREE.SphereGeometry(0.025 + relative * 0.035, 16, 12), new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.2, roughness: 0.55 }));
      marker.userData.neoId = item.neo_id;
      marker.userData.name = item.name;
      mapGroup.add(marker);
      markers.push({ item, marker, line });
    }
    renderObjectsRef.current = markers;

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let downX = 0;
    let downY = 0;
    renderer.domElement.addEventListener("pointerdown", (event) => { downX = event.clientX; downY = event.clientY; });
    const handleClick = (event: MouseEvent) => {
      if (Math.hypot(event.clientX - downX, event.clientY - downY) > 5) return;
      const bounds = renderer.domElement.getBoundingClientRect();
      pointer.set(((event.clientX - bounds.left) / bounds.width) * 2 - 1, -((event.clientY - bounds.top) / bounds.height) * 2 + 1);
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(markers.map((entry) => entry.marker));
      const neoId = hits[0]?.object.userData.neoId as string | undefined;
      if (neoId) onSelectRef.current(neoId);
    };
    renderer.domElement.addEventListener("click", handleClick);
    const resizeObserver = new ResizeObserver(() => {
      if (!host.clientWidth || !host.clientHeight) return;
      camera.aspect = host.clientWidth / host.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(host.clientWidth, host.clientHeight);
    });
    resizeObserver.observe(host);
    renderer.setAnimationLoop(() => {
      const index = indexRef.current;
      for (const entry of markers) {
        const point = pointAtTime(entry.item, data.times[index]?.jd_tdb);
        if (point) entry.marker.position.set(point.x_au * sceneScale, point.y_au * sceneScale, point.z_au * sceneScale);
        const isSelected = entry.item.neo_id === selectedRef.current;
        (entry.line.material as THREE.LineBasicMaterial).opacity = isSelected ? 0.98 : 0.34;
        (entry.line.material as THREE.LineBasicMaterial).linewidth = isSelected ? 2 : 1;
        (entry.marker.material as THREE.MeshStandardMaterial).emissiveIntensity = isSelected ? 0.65 : 0.2;
      }
      controls.update();
      renderer.render(scene, camera);
    });

    return () => {
      resizeObserver.disconnect();
      renderer.setAnimationLoop(null);
      renderer.domElement.removeEventListener("click", handleClick);
      controls.dispose();
      mapGroup.traverse((object) => {
        if (object instanceof THREE.Mesh || object instanceof THREE.Line || object instanceof THREE.LineLoop) {
          object.geometry.dispose();
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((material) => material.dispose());
        }
      });
      stars.dispose();
      (starField.material as THREE.Material).dispose();
      renderer.dispose();
      renderer.domElement.remove();
      renderObjectsRef.current = [];
    };
  }, [data, onError, sceneScale]);

  return <div className="asteroid-3d-canvas" ref={hostRef} aria-label="Interactive 3D asteroid trajectory map" role="img" />;
}

export function AsteroidOrbit3D({ data, selectedId, onSelect }: {
  data: AsteroidOrbitMapResponse;
  selectedId?: string;
  onSelect: (neoId: string) => void;
}) {
  const [currentIndex, setCurrentIndex] = useState(Math.floor(data.times.length / 2));
  const [playing, setPlaying] = useState(false);
  const [viewerError, setViewerError] = useState<string | null>(null);
  useEffect(() => { setCurrentIndex(Math.floor(data.times.length / 2)); setPlaying(false); }, [data]);
  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => setCurrentIndex((index) => (index + 1) % data.times.length), 240);
    return () => window.clearInterval(timer);
  }, [data.times.length, playing]);
  const current = data.times[currentIndex];
  const selected = data.objects.find((item) => item.neo_id === selectedId);
  const selectedPoint = selected ? pointAtTime(selected, current?.jd_tdb) : undefined;
  const selectedDistanceKm = selectedPoint ? selectedPoint.distance_au * AU_KM : undefined;
  const diameters = data.objects.map((item) => item.diameter_km || 0.001);
  const minDiameter = diameters.length ? Math.min(...diameters) : 0.001;
  const maxDiameter = Math.max(...diameters, minDiameter);
  const diameterScale = Math.log10(Math.max(1.001, maxDiameter / minDiameter));

  return (
    <section className="panel asteroid-3d-panel" aria-labelledby="asteroid-3d-title">
      <div className="asteroid-3d-heading">
        <div><p className="eyebrow">JPL HORIZONS · INTERACTIVE ORBIT VIEWER</p><h2 id="asteroid-3d-title">Earth and near-Earth objects</h2><p>{data.objects.length} of {data.objects.length + data.unavailable.length} current-page objects mapped · Earth-centered ecliptic coordinates</p></div>
        <span className="distance-scale-pill">3D perspective · Drag to rotate · Scroll to zoom</span>
      </div>
      <div className="asteroid-3d-layout">
        <div className="asteroid-3d-main">
          <div className="asteroid-3d-stage"><AsteroidScene data={data} selectedId={selectedId} currentIndex={currentIndex} onSelect={onSelect} onError={setViewerError} />
            <div className="asteroid-3d-badge"><span className="live-dot" />LIVE EPHEMERIS · {data.sample_interval_hours}H STEPS</div>
            <div className="asteroid-3d-controls-hint"><RotateCw size={14} /> Drag to rotate <span>·</span> Hover here and use the wheel to zoom <span>·</span> Right-drag to pan</div>
          </div>
          {viewerError && <p className="asteroid-3d-error" role="alert">{viewerError}</p>}
          <div className="asteroid-time-controls">
            <button type="button" className="button button-quiet button-small" onClick={() => setPlaying((value) => !value)} aria-label={playing ? "Pause asteroid motion" : "Play asteroid motion"}>{playing ? <Pause size={14} /> : <Play size={14} />}{playing ? "Pause" : "Play"}</button>
            <input aria-label="Trajectory time" type="range" min="0" max={Math.max(0, data.times.length - 1)} value={currentIndex} onChange={(event) => { setPlaying(false); setCurrentIndex(Number(event.target.value)); }} />
            <span className="asteroid-time-label">{current?.date ?? "Time unavailable"} <small>TDB</small></span>
          </div>
          <div className="asteroid-3d-legend"><span><i className="orbit-legend-earth" />Earth</span><span><i className="orbit-legend-normal" />Asteroid path</span><span><i className="orbit-legend-hazard" />NASA hazardous flag</span><span>3D wireframe shells: lunar-distance ranges</span><span>Dot size: compressed diameter estimate</span><span>Path: real JPL X/Y/Z vectors · 6-hour samples</span></div>
        </div>
        <aside className="asteroid-3d-sidebar">
          {selected && <div className="asteroid-selected-card"><p className="eyebrow">SELECTED OBJECT</p><h3>{selected.name}</h3><div><span>Estimated diameter</span><strong>{selected.diameter_km ? `${new Intl.NumberFormat(undefined, { maximumSignificantDigits: 3 }).format(selected.diameter_km)} km` : "Not supplied"}</strong></div><div><span>Earth distance at cursor time</span><strong>{selectedDistanceKm ? `${(selectedDistanceKm / LD_KM).toFixed(2)} LD · ${Math.round(selectedDistanceKm).toLocaleString()} km` : "—"}</strong></div><div><span>NASA classification</span><strong>{selected.potentially_hazardous == null ? "Not supplied" : selected.potentially_hazardous ? "Potentially hazardous" : "Not flagged"}</strong></div></div>}
          <div className="asteroid-3d-object-list"><h3>Mapped asteroids <span>{data.objects.length}</span></h3><div className="asteroid-3d-object-scroll">{data.objects.map((item) => {
            const dot = item.potentially_hazardous ? "asteroid-list-dot hazardous" : item.potentially_hazardous === false ? "asteroid-list-dot" : "asteroid-list-dot unknown";
            const diameter = item.diameter_km && item.diameter_km > 0 ? item.diameter_km : 0.001;
            const relative = Math.max(0, Math.min(1, Math.log10(diameter / minDiameter) / diameterScale));
            const rangeAtTime = pointAtTime(item, current?.jd_tdb)?.distance_au ?? 0;
            return <button type="button" key={item.neo_id} className={`asteroid-3d-object ${selectedId === item.neo_id ? "active" : ""}`} onClick={() => onSelect(item.neo_id)}><i className={dot} style={{ width: `${7 + relative * 11}px`, height: `${7 + relative * 11}px` }} /><span><strong>{item.name}</strong><small>{item.diameter_km ? `${item.diameter_km.toPrecision(3)} km` : "Diameter unavailable"}</small></span><small className="asteroid-list-range">{(rangeAtTime * AU_KM / LD_KM).toFixed(1)} LD</small></button>;
          })}</div></div>
          {data.unavailable.length > 0 && <p className="asteroid-partial-note">JPL did not return paths for {data.unavailable.length} object{data.unavailable.length === 1 ? "" : "s"}. Their names are listed in the response below.</p>}
        </aside>
      </div>
      <p className="distance-map-disclaimer">All mapped positions and paths use Horizons heliocentric vectors converted to Earth-centered coordinates at matching timestamps. The scene auto-fits the current catalogue page. Earth and asteroid markers are enlarged for visibility; marker size is a compressed diameter scale, not physical scale. Trajectories span {data.start_date} through {data.end_date}; exact dates are shown in TDB.</p>
      {data.unavailable.length > 0 && <details className="asteroid-unavailable-list"><summary>Objects without a JPL trajectory</summary><p>{data.unavailable.map((item) => item.name).join(" · ")}</p></details>}
    </section>
  );
}
