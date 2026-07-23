export type エージェント状態 = '作業中' | '相談中' | '瞑想中' | '移動中' | '召喚中';

export type エージェント = {
  id: string;
  名前: string;
  役割: string;
  人格情報: string;
  色: number;
  色CSS: string;
  状態: エージェント状態;
  作業内容: string;
  ひとこと: string;
  状態更新時刻: number;
};

export type チーム要員 = {
  要員ID: string;
  要員名: string;
  役割: string;
  人格情報: string;
  有効: boolean;
};

export type チーム作業 = {
  利用者ID: string;
  作業ID: string;
  プロジェクト: string;
  タイトル: string;
  要求内容: string;
  TEAM_AI_NAME: string;
  TEAM_AI_MODEL: string;
  TASK_AI_NAME: string;
  TASK_AI_MODEL: string;
  タスクID: string;
  実行有効: boolean | number;
  状態: '準備開始' | '準備中' | '準備完了' | '待機' | '実行中' | 'エラー' | '完了' | '中止';
  PID: string;
  開始日時: string;
  終了日時: string;
  実行回数: number;
  応答タイトル: string;
  応答内容: string;
  更新日時: string;
};

export type 稼働要員 = {
  エージェントID: string;
  エージェント名: string;
  役割: string;
  人格情報: string;
  状態: エージェント状態;
  作業内容: string;
  ひとこと: string;
};

export type 状態表示 = Record<エージェント状態, { 色: string; 記号: string }>;

export const 状態情報: 状態表示 = {
  作業中: { 色: '#65e8b7', 記号: '●' },
  相談中: { 色: '#8bb8ff', 記号: '◆' },
  瞑想中: { 色: '#ffd580', 記号: '◉' },
  移動中: { 色: '#b8a7ff', 記号: '→' },
  召喚中: { 色: '#f58cff', 記号: '✦' },
};

export const 要員色一覧 = [
  { 色: 0x5bd9ff, 色CSS: '#5bd9ff' },
  { 色: 0x8d7dff, 色CSS: '#9d91ff' },
  { 色: 0x5ce3a1, 色CSS: '#5ce3a1' },
  { 色: 0xff7eb6, 色CSS: '#ff8fc2' },
  { 色: 0xffc35b, 色CSS: '#ffd078' },
  { 色: 0x66a4ff, 色CSS: '#78afff' },
  { 色: 0xd07dff, 色CSS: '#d893ff' },
  { 色: 0x65e5d6, 色CSS: '#74e9dc' },
];
