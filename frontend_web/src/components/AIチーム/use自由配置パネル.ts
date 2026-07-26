import { onBeforeUnmount, onMounted, reactive, ref } from 'vue';

let 前面連番 = 20;

export const use自由配置パネル = (
  storageKey: string,
  /** 初期表示の横位置。`center` は親の幅に対する中央寄せ */
  initialSide: 'left' | 'center' | 'right',
  /** 初期表示の縦位置。パネル同士が重ならないように呼び出し側で上下を分ける */
  initialVertical: 'top' | 'bottom' = 'top',
) => {
  const panelRef = ref<HTMLElement | null>(null);
  const zIndex = ref(++前面連番);
  // ドラッグ（または保存位置の復元）までは初期位置へ追従する。
  // 一覧の読み込みで高さが変わっても、下寄せパネルが画面外へはみ出さないようにするため。
  let 初期位置追従 = true;
  let サイズ監視: ResizeObserver | null = null;
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
    let x = 18;
    if (panel && parent) {
      if (initialSide === 'right') x = parent.clientWidth - panel.offsetWidth - 18;
      else if (initialSide === 'center') x = (parent.clientWidth - panel.offsetWidth) / 2;
    }
    const y = initialVertical === 'bottom' && panel && parent
      ? parent.clientHeight - panel.offsetHeight - 18
      : 18;
    return 位置を制限(x, y);
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
    初期位置追従 = false;
    位置を保存();
  };

  const 位置を適用 = (次: { x: number; y: number }) => {
    位置.x = 次.x;
    位置.y = 次.y;
  };

  onMounted(() => {
    const fallback = 初期位置();
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
      const 保存あり = Number.isFinite(Number(saved.x)) && Number.isFinite(Number(saved.y));
      if (保存あり) 初期位置追従 = false;
      位置を適用(保存あり ? 位置を制限(Number(saved.x), Number(saved.y)) : fallback);
    } catch {
      位置を適用(fallback);
    }
    // 高さが変わったら、初期位置のままなら再計算し、動かした後は画面内へ収め直すだけにする
    if (typeof ResizeObserver !== 'undefined' && panelRef.value) {
      サイズ監視 = new ResizeObserver(() => {
        位置を適用(初期位置追従 ? 初期位置() : 位置を制限(位置.x, 位置.y));
      });
      サイズ監視.observe(panelRef.value);
    }
  });

  onBeforeUnmount(() => {
    サイズ監視?.disconnect();
    サイズ監視 = null;
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
