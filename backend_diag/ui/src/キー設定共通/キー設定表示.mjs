// サーバーの登録順を変えず、各キーを必ず一方の画面へ分類する。
export const 外部連携ID = Object.freeze(['huggingface_read', 'huggingface_write', 'discord']);
export const 外部連携か = item => 外部連携ID.includes(item.id);
export const 設定表示 = item => item.設定済み === null ? '確認不可' : item.設定済み ? '設定済' : '未設定';
