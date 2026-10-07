/** Node の fetch は通信エラーを cause に包むため、実際の接続先と原因も表示する。 */
export function 接続エラー詳細(target: URL, error: unknown): string {
  const details: string[] = [];
  let current = error;
  for (let depth = 0; current && depth < 4; depth++) {
    if (!(current instanceof Error)) { details.push(String(current)); break; }
    const code = (current as NodeJS.ErrnoException).code;
    details.push(`${code ? `${code}: ` : ''}${current.message}`);
    current = current.cause;
  }
  return `AIコアとの通信に失敗しました。接続先: ${target.origin}\n${details.join('\n')}`;
}
