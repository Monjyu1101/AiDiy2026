import { onMounted, reactive, ref } from 'vue';

let 前面連番 = 20;

export const use自由配置パネル = (
  storageKey: string,
  initialSide: 'left' | 'right',
) => {
  const panelRef = ref<HTMLElement | null>(null);
  const zIndex = ref(++前面連番);
  const 位置 = reactive({ x: 18, y: 18 });
  const ドラッグ = reactive({
    pointerId: -1,
    startX: 0,
    startY: 0,
    originX: 0,
    originY: 0,
  });

  const 位置を制限 = (x: number, y: number) => {
    const panel = panelRef.value;
    const parent = panel?.offsetParent as HTMLElement | null;
    if (!panel || !parent) return { x: Math.max(0, x), y: Math.max(0, y) };
    return {
      x: Math.min(Math.max(0, x), Math.max(0, parent.clientWidth - panel.offsetWidth)),
      y: Math.min(Math.max(0, y), Math.max(0, parent.clientHeight - panel.offsetHeight)),
    };
  };

  const 初期位置 = () => {
    const panel = panelRef.value;
    const parent = panel?.offsetParent as HTMLElement | null;
    const x = initialSide === 'right' && panel && parent
      ? parent.clientWidth - panel.offsetWidth - 18
      : 18;
    return 位置を制限(x, 18);
  };

  const 位置を保存 = () => {
    localStorage.setItem(storageKey, JSON.stringify(位置));
  };

  const ドラッグ開始 = (event: PointerEvent) => {
    if ((event.target as HTMLElement).closest('button, input, select')) return;
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
    zIndex.value = ++前面連番;
    ドラッグ.pointerId = event.pointerId;
    ドラッグ.startX = event.clientX;
    ドラッグ.startY = event.clientY;
    ドラッグ.originX = 位置.x;
    ドラッグ.originY = 位置.y;
  };

  const ドラッグ中 = (event: PointerEvent) => {
    if (ドラッグ.pointerId !== event.pointerId) return;
    const next = 位置を制限(
      ドラッグ.originX + event.clientX - ドラッグ.startX,
      ドラッグ.originY + event.clientY - ドラッグ.startY,
    );
    位置.x = next.x;
    位置.y = next.y;
  };

  const ドラッグ終了 = (event: PointerEvent) => {
    if (ドラッグ.pointerId !== event.pointerId) return;
    ドラッグ.pointerId = -1;
    位置を保存();
  };

  onMounted(() => {
    const fallback = 初期位置();
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
      const next = Number.isFinite(Number(saved.x)) && Number.isFinite(Number(saved.y))
        ? 位置を制限(Number(saved.x), Number(saved.y))
        : fallback;
      位置.x = next.x;
      位置.y = next.y;
    } catch {
      位置.x = fallback.x;
      位置.y = fallback.y;
    }
  });

  return {
    panelRef,
    位置,
    zIndex,
    ドラッグ開始,
    ドラッグ中,
    ドラッグ終了,
  };
};
