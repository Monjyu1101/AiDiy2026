let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  const args = process.argv.slice(2);
  if (input === 'wait') { setInterval(() => {}, 1000); return; }
  process.stderr.write('session_id: discord-test-session\n');
  process.stdout.write(JSON.stringify({ input, args, cwd: process.cwd() }));
});
