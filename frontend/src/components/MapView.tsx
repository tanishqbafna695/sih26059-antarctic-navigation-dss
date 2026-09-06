import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const STATION_MARKERS = [
  { name: "Bharati", lon: 76.19, lat: -69.41, color: "#ffd166" },
  { name: "Maitri", lon: 11.73, lat: -70.77, color: "#ff7d9c" },
];

export interface RouteLine {
  id: string;
  coords: number[][];
  color: string;
  width: number;
  dashed: boolean;
  visible: boolean;
}

interface BergData {
  buffers: GeoJSON.FeatureCollection;
  fixes: GeoJSON.FeatureCollection;
}

interface MapViewProps {
  iceUrl: string;
  showIce: boolean;
  hazardUrl: string | null;
  showHazard: boolean;
  lines: RouteLine[];
  oldLine: number[][] | null;
  bergs: BergData;
  showBergs: boolean;
  bbox: [[number, number], [number, number]];
}

const IMG_COORDS: [[number, number], [number, number], [number, number], [number, number]] = [
  [0, -55],
  [95, -55],
  [95, -75],
  [0, -75],
];

const STATIONS: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [
    { type: "Feature", properties: { name: "Bharati", color: "#ffd166" },
      geometry: { type: "Point", coordinates: [76.19, -69.41] } },
    { type: "Feature", properties: { name: "Maitri", color: "#ff7d9c" },
      geometry: { type: "Point", coordinates: [11.73, -70.77] } },
  ],
};

export default function MapView(props: MapViewProps) {
  const { bbox } = props;
  const divRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const lineIdsRef = useRef<Set<string>>(new Set());
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!divRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: divRef.current,
      style: { version: 8, sources: {}, layers: [
        { id: "bg", type: "background", paint: { "background-color": "#0a0f1c" } },
      ] },
      bounds: [bbox[0], bbox[1]],
      fitBoundsOptions: { padding: 20 },
      attributionControl: false,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.on("load", () => setReady(true));
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;

    const ensureImage = (id: string, url: string) => {
      const src = map.getSource(id) as maplibregl.ImageSource | undefined;
      if (src) {
        if ((src as unknown as { url?: string }).url !== url) src.updateImage({ url });
      } else {
        map.addSource(id, { type: "image", url, coordinates: IMG_COORDS });
      }
    };
    ensureImage("ice", props.iceUrl);
    if (!map.getLayer("ice-lyr"))
      map.addLayer({ id: "ice-lyr", type: "raster", source: "ice",
        paint: { "raster-opacity": 0.9 } });
    map.setLayoutProperty("ice-lyr", "visibility",
      props.showIce ? "visible" : "none");

    if (props.hazardUrl) {
      ensureImage("hazard", props.hazardUrl);
      if (!map.getLayer("hazard-lyr"))
        map.addLayer({ id: "hazard-lyr", type: "raster", source: "hazard",
          paint: { "raster-opacity": 0.55 } });
      map.setLayoutProperty("hazard-lyr", "visibility",
        props.showHazard ? "visible" : "none");
    } else if (map.getLayer("hazard-lyr")) {
      map.setLayoutProperty("hazard-lyr", "visibility", "none");
    }

    const upsertGeo = (id: string, data: GeoJSON.FeatureCollection) => {
      const src = map.getSource(id) as maplibregl.GeoJSONSource | undefined;
      if (src) src.setData(data);
      else map.addSource(id, { type: "geojson", data });
    };
    upsertGeo("bergs-buf", props.bergs.buffers);
    upsertGeo("bergs-fix", props.bergs.fixes);
    upsertGeo("stations", STATIONS);

    // Iceberg danger buffers (pink fill)
    if (!map.getLayer("bergs-buf-lyr"))
      map.addLayer({ id: "bergs-buf-lyr", type: "fill", source: "bergs-buf",
        paint: { "fill-color": "#ff7d9c", "fill-opacity": 0.22 } });

    // Iceberg fix points (red circles)
    if (!map.getLayer("bergs-fix-lyr"))
      map.addLayer({ id: "bergs-fix-lyr", type: "circle", source: "bergs-fix",
        paint: { "circle-color": "#ff7d9c", "circle-radius": 5,
                 "circle-stroke-color": "#0b1220", "circle-stroke-width": 1.5 } });

    // Station points (colored circles)
    if (!map.getLayer("stations-lyr"))
      map.addLayer({ id: "stations-lyr", type: "circle", source: "stations",
        paint: { "circle-color": ["get", "color"], "circle-radius": 7,
                 "circle-stroke-color": "#0b1220", "circle-stroke-width": 2 } });



    const bergVis = props.showBergs ? "visible" : "none";
    map.setLayoutProperty("bergs-buf-lyr", "visibility", bergVis);
    map.setLayoutProperty("bergs-fix-lyr", "visibility", bergVis);

    // Route lines: thicker, with glow for visibility
    interface DrawLine { id: string; coords: number[][]; color: string;
      width: number; dash: number[] | null; visible: boolean }
    const all: DrawLine[] = props.lines.map((l) => ({
      ...l, width: l.width * 1.5,  // Thicker lines
      dash: l.dashed ? [3, 2] : null }));
    if (props.oldLine)
      all.push({ id: "old", coords: props.oldLine, color: "#8ea3c4",
                 width: 2.5, dash: [3, 2], visible: true });
    for (const l of all) {
      upsertGeo(`line-${l.id}`, {
        type: "FeatureCollection",
        features: [{ type: "Feature", properties: {},
          geometry: { type: "LineString", coordinates: l.coords } }],
      });
      if (!map.getLayer(`line-${l.id}`)) {
        // Glow layer (wider, transparent) underneath
        map.addLayer({
          id: `line-glow-${l.id}`, type: "line", source: `line-${l.id}`,
          paint: {
            "line-color": l.color, "line-width": l.width + 4,
            "line-opacity": 0.25,
            ...(l.dash ? { "line-dasharray": l.dash } : {}),
          } });
        // Main route line on top
        map.addLayer({
          id: `line-${l.id}`, type: "line", source: `line-${l.id}`,
          paint: {
            "line-color": l.color, "line-width": l.width,
            ...(l.dash ? { "line-dasharray": l.dash } : {}),
          } });
      } else {
        map.setPaintProperty(`line-${l.id}`, "line-color", l.color);
        map.setPaintProperty(`line-${l.id}`, "line-width", l.width);
        if (map.getLayer(`line-glow-${l.id}`)) {
          map.setPaintProperty(`line-glow-${l.id}`, "line-color", l.color);
          map.setPaintProperty(`line-glow-${l.id}`, "line-width", l.width + 4);
        }
      }
      map.setLayoutProperty(`line-${l.id}`, "visibility",
        l.visible ? "visible" : "none");
      if (map.getLayer(`line-glow-${l.id}`))
        map.setLayoutProperty(`line-glow-${l.id}`, "visibility",
          l.visible ? "visible" : "none");
      lineIdsRef.current.add(l.id);
    }
    // Remove old line layers
    for (const old of [...lineIdsRef.current]) {
      if (!all.some((l) => l.id === old)) {
        for (const prefix of ["line-", "line-glow-"]) {
          if (map.getLayer(`${prefix}${old}`)) map.removeLayer(`${prefix}${old}`);
        }
        if (map.getSource(`line-${old}`)) map.removeSource(`line-${old}`);
        lineIdsRef.current.delete(old);
      }
    }
  });

  // Add HTML markers for station labels (avoids needing a glyphs service)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const markers: maplibregl.Marker[] = [];
    for (const s of STATION_MARKERS) {
      const el = document.createElement("div");
      el.textContent = s.name;
      el.style.cssText = `color:${s.color};font-size:12px;font-weight:700;text-shadow:0 0 6px #0b1220,0 0 3px #0b1220,1px 1px 2px #0b1220;white-space:nowrap;pointer-events:none;margin-top:14px;`;
      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([s.lon, s.lat])
        .addTo(map);
      markers.push(marker);
    }
    return () => { for (const m of markers) m.remove(); };
  }, [ready]);

  return (
    <div className="map-wrap">
      <div ref={divRef} style={{ width: "100%", height: 520, borderRadius: 8, overflow: "hidden" }} />
    </div>
  );
}
