import { useRef, useState, useEffect } from "react";

export interface Transform {
  scale: number;
  x: number;
  y: number;
}

/**
 * Attach pan/zoom behaviour to an SVG container.
 * - Mouse wheel / pinch zooms.
 * - Click+drag or single-finger drag pans.
 * Returns a ref to attach to the container plus the current transform.
 */
export function usePanZoom(initial: Transform = { scale: 1, x: 0, y: 0 }) {
  const [transform, setTransform] = useState<Transform>(initial);
  const ref = useRef<HTMLDivElement | null>(null);
  const pointers = useRef<Map<number, { x: number; y: number }>>(new Map());
  const lastPinchDistance = useRef<number | null>(null);
  const dragging = useRef(false);
  const lastPos = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      setTransform((t) => {
        const factor = Math.exp(-e.deltaY * 0.0015);
        const nextScale = Math.min(3, Math.max(0.5, t.scale * factor));
        return { ...t, scale: nextScale };
      });
    };
    el.addEventListener("wheel", onWheel, { passive: false });

    const onPointerDown = (e: PointerEvent) => {
      el.setPointerCapture(e.pointerId);
      pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pointers.current.size === 1) {
        dragging.current = true;
        lastPos.current = { x: e.clientX, y: e.clientY };
      } else {
        dragging.current = false;
        lastPinchDistance.current = pinchDistance();
      }
    };
    const onPointerMove = (e: PointerEvent) => {
      if (!pointers.current.has(e.pointerId)) return;
      pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pointers.current.size === 1 && dragging.current && lastPos.current) {
        const dx = e.clientX - lastPos.current.x;
        const dy = e.clientY - lastPos.current.y;
        lastPos.current = { x: e.clientX, y: e.clientY };
        setTransform((t) => ({ ...t, x: t.x + dx, y: t.y + dy }));
      } else if (pointers.current.size === 2 && lastPinchDistance.current !== null) {
        const d = pinchDistance();
        if (d > 0 && lastPinchDistance.current > 0) {
          const factor = d / lastPinchDistance.current;
          setTransform((t) => ({
            ...t,
            scale: Math.min(3, Math.max(0.5, t.scale * factor)),
          }));
          lastPinchDistance.current = d;
        }
      }
    };
    const onPointerUp = (e: PointerEvent) => {
      pointers.current.delete(e.pointerId);
      if (pointers.current.size < 2) lastPinchDistance.current = null;
      if (pointers.current.size === 0) {
        dragging.current = false;
        lastPos.current = null;
      }
    };

    function pinchDistance(): number {
      const pts = Array.from(pointers.current.values());
      if (pts.length < 2) return 0;
      const [a, b] = pts;
      return Math.hypot(a.x - b.x, a.y - b.y);
    }

    el.addEventListener("pointerdown", onPointerDown);
    el.addEventListener("pointermove", onPointerMove);
    el.addEventListener("pointerup", onPointerUp);
    el.addEventListener("pointercancel", onPointerUp);

    return () => {
      el.removeEventListener("wheel", onWheel);
      el.removeEventListener("pointerdown", onPointerDown);
      el.removeEventListener("pointermove", onPointerMove);
      el.removeEventListener("pointerup", onPointerUp);
      el.removeEventListener("pointercancel", onPointerUp);
    };
  }, []);

  const reset = () => setTransform(initial);
  return { ref, transform, reset };
}
