import { build } from 'esbuild';
import { spawnSync } from 'node:child_process';
await build({ entryPoints: ['src/runner.ts'], outfile: 'out/runner.cjs', bundle: true, platform: 'node', target: 'node22', format: 'cjs' });
await build({ entryPoints: ['src/protocol.ts'], outfile: 'out/protocol.cjs', bundle: true, platform: 'node', target: 'node22', format: 'cjs' });
await build({ entryPoints: ['src/forwarded-origin.ts'], outfile: 'out/forwarded-origin.cjs', bundle: true, platform: 'node', target: 'node22', format: 'cjs' });
await build({ entryPoints: ['aidiy_code/src/server.ts'], outfile: 'out/aidiy_code/server.cjs', bundle: true, platform: 'node', target: 'node22', format: 'cjs' });
const result = spawnSync(process.execPath, ['--test', 'checks/runner.test.cjs', 'checks/aidiy_code.test.cjs', 'checks/launcher.test.cjs', 'checks/desktop.test.cjs', 'checks/webview.test.cjs', 'checks/browser-mode.test.cjs'], { stdio: 'inherit' });
process.exitCode = result.status ?? 1;
