import { createHighlighter, type BuiltinLanguage } from 'shiki';

const 使用テーマ = 'github-dark';
const 使用言語: BuiltinLanguage[] = [
  'python',
  'vue',
  'html',
  'css',
  'scss',
  'javascript',
  'typescript',
  'json',
  'markdown',
  'yaml',
  'bash',
  'powershell',
  'sql',
  'xml',
  'ini',
  'toml',
];

const 拡張子と言語: Record<string, BuiltinLanguage> = {
  py: 'python',
  vue: 'vue',
  html: 'html',
  htm: 'html',
  css: 'css',
  scss: 'scss',
  sass: 'scss',
  less: 'css',
  js: 'javascript',
  jsx: 'javascript',
  ts: 'typescript',
  tsx: 'typescript',
  json: 'json',
  md: 'markdown',
  yml: 'yaml',
  yaml: 'yaml',
  sh: 'bash',
  bat: 'bat',
  ps1: 'powershell',
  sql: 'sql',
  xml: 'xml',
  ini: 'ini',
  env: 'ini',
  toml: 'toml',
};

let highlighterPromise: ReturnType<typeof createHighlighter> | null = null;

const ハイライター取得 = () => {
  if (!highlighterPromise) {
    highlighterPromise = createHighlighter({
      themes: [使用テーマ],
      langs: 使用言語,
    });
  }
  return highlighterPromise;
};

const 末尾拡張子取得 = (ファイル名: string): string => {
  const クエリ除去 = (ファイル名 ?? '').split(/[?#]/u, 1)[0] ?? '';
  const 最後のスラッシュ位置 = Math.max(クエリ除去.lastIndexOf('/'), クエリ除去.lastIndexOf('\\'));
  const ベース名 = 最後のスラッシュ位置 >= 0 ? クエリ除去.slice(最後のスラッシュ位置 + 1) : クエリ除去;
  const ドット位置 = ベース名.lastIndexOf('.');
  if (ドット位置 < 0) return '';
  return ベース名.slice(ドット位置 + 1).toLowerCase();
};

export const シキ言語推定 = (ファイル名: string): BuiltinLanguage | null => {
  const 拡張子 = 末尾拡張子取得(ファイル名);
  return 拡張子と言語[拡張子] ?? null;
};

const 背景色透過化 = (html: string): string => {
  return html
    .replace(/background-color:[^;"']*;?/gi, 'background-color: transparent;')
    .replace(/<pre class="shiki/g, '<pre class="shiki shiki-pre');
};

const HTMLエスケープ = (テキスト: string): string => {
  return テキスト
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
};

const プレーンHTML生成 = (コード: string): string => {
  return `<pre class="shiki shiki-pre"><code>${HTMLエスケープ(コード)}</code></pre>`;
};

export const シキHTML生成 = async (コード: string, ファイル名: string): Promise<string> => {
  if (!コード) return '';
  const highlighter = await ハイライター取得();
  const 推定言語 = シキ言語推定(ファイル名);
  if (!推定言語) {
    return プレーンHTML生成(コード);
  }

  try {
    const html = highlighter.codeToHtml(コード, { lang: 推定言語, theme: 使用テーマ });
    return 背景色透過化(html);
  } catch {
    return プレーンHTML生成(コード);
  }
};
