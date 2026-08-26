/**
 * dev-filter.cjs
 * electronmon の stdout / stderr 両方から WebRTC/WGC ノイズログをフィルタするラッパー。
 */
'use strict'

const { spawn } = require('node:child_process')
const readline = require('node:readline')

const electronmonCli = require.resolve('electronmon/bin/cli.js')

const SUPPRESS_PATTERNS = [
  // WebRTC デスクトップキャプチャ系ノイズ（WGC/DXGI）を一括抑止
  /desktop_capture/i,
  /ProcessFrame failed/i,
  /DxgiDuplicator/i,
  /Duplication failed/i,
  /wgc_capture/i,
]

function shouldSuppress(line) {
  return SUPPRESS_PATTERNS.some((re) => re.test(line))
}

function pipeFiltered(input, output) {
  const rl = readline.createInterface({ input, crlfDelay: Infinity })
  rl.on('line', (line) => {
    if (!shouldSuppress(line)) {
      output.write(line + '\n')
    }
  })
}

const args = process.argv.slice(2)

const child = spawn(process.execPath, [electronmonCli, ...args], {
  stdio: ['inherit', 'pipe', 'pipe'],
  env: process.env,
})

pipeFiltered(child.stdout, process.stdout)
pipeFiltered(child.stderr, process.stderr)

child.on('error', (err) => {
  process.stderr.write(`[dev-filter] spawn error: ${err.message}\n`)
})

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal)
  } else {
    process.exit(code ?? 0)
  }
})
