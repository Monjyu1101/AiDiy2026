import { build } from 'esbuild';
import { spawnSync } from 'node:child_process';
await build({ entryPoints: ['src/runner.ts'], outfile: 'out/runner.cjs', bundle: true, platform: 'node', target: 'node22', format: 'cjs' });
await build({ entryPoints: ['src/protocol.ts'], outfile: 'out/protocol.cjs', bundle: true, platform: 'node', target: 'node22', format: 'cjs' });
await build({ entryPoints: ['src/standalone.ts'], outfile: 'out/standalone.cjs', bundle: true, platform: 'node', target: 'node22', format: 'cjs' });
const result = spawnSync(process.execPath, ['--test', 'test/runner.test.cjs', 'test/standalone.test.cjs'], { stdio: 'inherit' });
process.exitCode = result.status ?? 1;
