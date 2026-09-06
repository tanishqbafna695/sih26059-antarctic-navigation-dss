import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

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
    if (!map.getLayer("bergs-buf-lyr"))
      map.addLayer({ id: "bergs-buf-lyr", type: "fill", source: "bergs-buf",
        paint: { "fill-color": "#ff7d9c", "fill-opacity": 0.22 } });
    if (!map.getLayer("bergs-fix-lyr"))
      map.addLayer({ id: "bergs-fix-lyr", type: "circle", source: "bergs-fix",
        paint: { "circle-color": "#ff7d9c", "circle-radius": 5,
                 "circle-stroke-color": "#0b1220", "circle-stroke-width": 1.5 } });
    if (!map.getLayer("stations-lyr"))
      map.addLayer({ id: "stations-lyr", type: "circle", source: "stations",
        paint: { "circle-color": ["get", "color"], "circle-radius": 6,
                 "circle-stroke-color": "#0b1220", "circle-stroke-width": 2 } });
    const bergVis = props.showBergs ? "visible" : "none";
    map.setLayoutProperty("bergs-buf-lyr", "visibility", bergVis);
    map.setLayoutProperty("bergs-fix-lyr", "visibility", bergVis);

    // route lines: one layer per line for independent toggles
    interface DrawLine { id: string; coords: number[][]; color: string;
      width: number; dash: number[] | null; visible: boolean }
    const all: DrawLine[] = props.lines.map((l) => ({
      ...l, dash: l.dashed ? [2, 1.5] : null }));
    if (props.oldLine)
      all.push({ id: "old", coords: props.oldLine, color: "#8ea3c4",
                 width: 2, dash: [2, 2], visible: true });
    for (const l of all) {
      upsertGeo(`line-${l.id}`, {
        type: "FeatureCollection",
        features: [{ type: "Feature", properties: {},
          geometry: { type: "LineString", coordinates: l.coords } }],
      });
      if (!map.getLayer(`line-${l.id}`)) {
        map.addLayer({
          id: `line-${l.id}`, type: "line", source: `line-${l.id}`,
          paint: {
            "line-color": l.color, "line-width": l.width,
            ...(l.dash ? { "line-dasharray": l.dash } : {}),
          } });
      } else {
        map.setPaintProperty(`line-${l.id}`, "line-color", l.color);
        map.setPaintProperty(`line-${l.id}`, "line-width", l.width);
      }
      map.setLayoutProperty(`line-${l.id}`, "visibility",
        l.visible ? "visible" : "none");
      lineIdsRef.current.add(l.id);
    }
    // remove line layers from a previous scenario that are no longer shown
    for (const old of [...lineIdsRef.current]) {
      if (!all.some((l) => l.id === old)) {
        if (map.getLayer(`line-${old}`)) map.removeLayer(`line-${old}`);
        if (map.getSource(`line-${old}`)) map.removeSource(`line-${old}`);
        lineIdsRef.current.delete(old);
      }
    }
  });

  return <div ref={divRef} style={{ width: "100%", height: 460 }} />;
}
