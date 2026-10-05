import { transform } from 'esbuild';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import './build.mjs';
const root = fileURLToPath(new URL('..', import.meta.url));
await mkdir(new URL('../out/aidiy_live/', import.meta.url), { recursive: true });
for (const name of ['protocol', 'audio', 'host', 'view']) {
  const result = await transform(await readFile(new URL(`src/${name}.ts`, import.meta.url), 'utf8'), { loader: 'ts', format: 'cjs', target: 'node22' });
  await writeFile(new URL(`../out/aidiy_live/${name}.cjs`, import.meta.url), result.code);
}
const result = spawnSync(process.execPath, ['--test', 'aidiy_live/checks/live.test.cjs', 'aidiy_live/checks/view.test.cjs', 'aidiy_live/checks/host.test.cjs', 'aidiy_live/checks/extension.test.cjs', 'aidiy_live/checks/launcher.test.cjs', 'aidiy_live/checks/permissions.test.cjs'], { cwd: root, stdio: 'inherit' });
process.exitCode = result.status ?? 1;
