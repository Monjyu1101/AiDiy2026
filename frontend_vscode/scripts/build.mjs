import { build } from 'esbuild';
import { readFile, readdir, writeFile } from 'node:fs/promises';

await build({ entryPoints: ['src/extension.ts'], outfile: 'dist/extension.js', bundle: true, platform: 'node', target: 'node22', format: 'cjs', external: ['vscode'] });
await build({ entryPoints: ['src/standalone.ts'], outfile: 'dist/standalone.cjs', bundle: true, platform: 'node', target: 'node22', format: 'cjs' });
const webview = await build({ entryPoints: ['src/webview.ts'], outfile: 'dist/webview.js', bundle: true, platform: 'browser', target: 'es2022', minify: true, metafile: true });
const packages = new Set(Object.keys(webview.metafile.inputs).filter(path => path.startsWith('node_modules/')).map(path => path.split('/')[1]));
const notices = [];
for (const name of [...packages].sort()) {
  const root = `node_modules/${name}`;
  const metadata = JSON.parse(await readFile(`${root}/package.json`, 'utf8'));
  for (const file of (await readdir(root)).filter(file => /^licen[sc]e/i.test(file))) {
    notices.push(`${name} ${metadata.version}\n${'='.repeat(60)}\n${await readFile(`${root}/${file}`, 'utf8')}`);
  }
}
await writeFile('dist/THIRD_PARTY_NOTICES.txt', notices.join('\n\n'));
