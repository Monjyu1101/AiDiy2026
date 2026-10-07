// aidiy_code / aidiy_live / aidiy_discord のブラウザ版サーバーが共通に使う接続元の許可判定。
// 通常は http://127.0.0.1:ポート だけを許可し、別サイトからの操作や DNS rebinding を拒否する。
// GitHub Codespaces ではポート転送の URL（https://<名前>-<ポート>.<転送ドメイン>）から開くため、
// その環境変数がそろっている時だけ転送先も許可する。

type 環境 = Record<string, string | undefined>;

/** Codespaces のポート転送で公開されるオリジン。Codespaces 以外では undefined。 */
export function 転送オリジン(port: number, env: 環境 = process.env): string | undefined {
  const name = env.CODESPACE_NAME, domain = env.GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN;
  if (env.CODESPACES !== 'true' || !name || !domain || !/^[\w.-]+$/.test(name + domain)) return undefined;
  return `https://${name}-${port}.${domain}`;
}

export class 接続元許可 {
  readonly ローカル: string;
  readonly 転送?: string;
  private hosts: Set<string>;
  private origins: Set<string>;
  constructor(port: number, env: 環境 = process.env) {
    this.ローカル = `http://127.0.0.1:${port}`;
    this.転送 = 転送オリジン(port, env);
    // VS Code デスクトップから Codespace に接続した場合は、手元の http://localhost:ポート へ転送される。
    this.origins = new Set([this.ローカル, ...(this.転送 ? [this.転送, `http://localhost:${port}`] : [])]);
    this.hosts = new Set([...this.origins].map(origin => new URL(origin).host));
  }
  host(value: string | undefined) { return !!value && this.hosts.has(value); }
  origin(value: string | undefined) { return !!value && this.origins.has(value); }
  /** ブラウザで開く URL。Codespaces では転送先を返す。 */
  公開URL(path: string) { return (this.転送 ?? this.ローカル) + path; }
}
