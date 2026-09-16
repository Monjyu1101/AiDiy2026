// 実際の子プロセスとの stdin/stdout/stderr 契約を検証する。
const { spawn } = require('node:child_process');
const { writeFileSync } = require('node:fs');
const mode = process.argv[2];
if (mode === 'wait') {
  const child = spawn(process.execPath, ['-e', 'setInterval(() => {}, 1000)'], { stdio: 'ignore', windowsHide: true });
  writeFileSync(process.argv[3], JSON.stringify({ parent: process.pid, child: child.pid }));
  process.stderr.write('waiting\n');
  setInterval(() => {}, 1000);
} else if (mode === 'fail') {
  process.stderr.write('provider authentication failed\n');
  process.exitCode = 7;
  process.stdin.resume();
} else {
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
    process.stderr.write('\x1b[32m[step] 日本語の進捗\x1b[0m\n');
    const utf8 = Buffer.from(JSON.stringify({ input, args: process.argv.slice(3), cwd: process.cwd(), envCwd: process.env.TERMINAL_CWD }));
    // UTF-8 マルチバイト文字・session_id をチャンクの境界で分ける。
    process.stdout.write(utf8.subarray(0, 13));
    setTimeout(() => {
      process.stdout.write(utf8.subarray(13));
      process.stderr.write('session_');
      setTimeout(() => process.stderr.write('id: test-session-001'), 10);
    }, 10);
  });
}
