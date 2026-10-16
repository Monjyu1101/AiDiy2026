// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

export const MAX_ELECTRON_FILES = 2048;
const fallbackLimit = 256;
const vertex = `
attribute vec3 a_position;
attribute vec3 a_orbit; // radius, electron index, count
attribute float a_phase;
uniform mat3 u_rotation;
uniform vec3 u_target, u_offset;
uniform vec2 u_viewport;
uniform float u_focal, u_time, u_dpr, u_alpha;
varying float v_alpha;
void main(){
 vec3 camera=u_rotation*(a_position-u_target)+u_offset;
 float depth=camera.z;
 float k=u_focal/max(depth,4.0);
 vec2 center=vec2(u_viewport.x*.5+camera.x*k,u_viewport.y*.5-camera.y*k);
 float angle=a_phase+a_orbit.y*6.28318530718/a_orbit.z+u_time*.65;
 float radius=max(7.0,a_orbit.x*k*1.8);
 vec2 point=center+vec2(cos(angle),sin(angle)*.65)*radius;
 gl_Position=vec4(point.x/u_viewport.x*2.0-1.0,1.0-point.y/u_viewport.y*2.0,0.0,1.0);
 gl_PointSize=4.5*u_dpr;
 v_alpha=depth>4.0?u_alpha*(.3+.7/(1.0+pow(depth/2400.0,2.0)))*min(1.0,(depth-4.0)/40.0):0.0;
}`;
const fragment = `
precision mediump float;
varying float v_alpha;
void main(){float d=length(gl_PointCoord-vec2(.5))*2.0;float a=(1.0-smoothstep(.15,1.0,d))*v_alpha;gl_FragColor=vec4(.78,.9,1.0,a);}`;

export function electronTargets(planets, counts, limit = MAX_ELECTRON_FILES) {
  // 同率は同じ個数。上限超過時だけパス順で安定させ、毎フレームの抽選や入替をしない。
  return planets.filter(file => [1, 2, 4].includes(counts[file.path])).map(file => ({ ...file, count: counts[file.path] }))
    .sort((a, b) => b.count - a.count || a.path.localeCompare(b.path)).slice(0, limit);
}
function phase(path) { let value = 2166136261; for (const char of path) value = Math.imul(value ^ char.charCodeAt(0), 16777619); return (value >>> 0) / 4294967296 * Math.PI * 2; }
export function electronBuffer(files) {
  const data = new Float32Array(files.reduce((sum, file) => sum + file.count, 0) * 7); let index = 0;
  for (const file of files) for (let i = 0; i < file.count; i++) {
    data.set([file.x, file.y, file.z, file.R, i, file.count, phase(file.path)], index); index += 7;
  }
  return data;
}

// 専用RAFを持たない。既存3Dフレームからuniformを渡し、全電子を1 drawArraysで描く。
// 対象と頂点バッファは走査/日付/フォルダ変更時だけ更新する。Canvas2Dへ1枚として合成する。
export function createElectronOrbits(doc = document) {
  const canvas = doc.createElement('canvas');
  let gl, program, buffer, uniforms, data = new Float32Array(), targets = [], lost = false, disposed = false;
  let signature = '', uploads = 0, draws = 0, total = 0, fallback = new Map();
  function release() { if (gl && !lost) { if (buffer) gl.deleteBuffer(buffer); if (program) gl.deleteProgram(program); } buffer = program = null; }
  function initialize() {
    try {
      gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: true, antialias: false, depth: false, preserveDrawingBuffer: true });
      if (!gl || typeof gl.getParameter(gl.VERSION) !== 'string') { gl = null; return; }
      const shaders = [];
      try {
        for (const [type, source] of [[gl.VERTEX_SHADER, vertex], [gl.FRAGMENT_SHADER, fragment]]) {
          const shader = gl.createShader(type); shaders.push(shader); gl.shaderSource(shader, source); gl.compileShader(shader);
          if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw Error('shader');
        }
        program = gl.createProgram(); shaders.forEach(shader => gl.attachShader(program, shader)); gl.linkProgram(program);
        if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error('program');
        buffer = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buffer); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW); uploads++;
        gl.useProgram(program);
        for (const [name, size, offset] of [['a_position', 3, 0], ['a_orbit', 3, 12], ['a_phase', 1, 24]]) {
          const location = gl.getAttribLocation(program, name); gl.enableVertexAttribArray(location); gl.vertexAttribPointer(location, size, gl.FLOAT, false, 28, offset);
        }
        uniforms = Object.fromEntries(['rotation','target','offset','viewport','focal','time','dpr','alpha'].map(name => [name, gl.getUniformLocation(program, 'u_' + name)]));
        gl.enable(gl.BLEND); gl.blendFuncSeparate(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA, gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      } finally { shaders.forEach(shader => gl.deleteShader(shader)); }
    } catch { release(); gl = null; }
  }
  function contextLost(event) { event.preventDefault(); lost = true; }
  function contextRestored() { if (disposed) return; lost = false; buffer = program = null; initialize(); }
  canvas.addEventListener?.('webglcontextlost', contextLost); canvas.addEventListener?.('webglcontextrestored', contextRestored);
  initialize();
  return {
    update(planets, counts) {
      if (disposed) return;
      total = planets.filter(file => [1, 2, 4].includes(counts[file.path])).length;
      targets = electronTargets(planets, counts);
      const next = JSON.stringify(targets.map(({ path, x, y, z, R, count }) => [path, x, y, z, R, count]));
      if (next === signature) return;
      signature = next; data = electronBuffer(targets); fallback = new Map(targets.slice(0, fallbackLimit).map(file => [file.path, file.count]));
      if (gl && !lost && buffer) { gl.bindBuffer(gl.ARRAY_BUFFER, buffer); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW); uploads++; }
    },
    render(ctx, { width, height, dpr, focal, rotation, target, offset, time, alpha, reduced }) {
      if (disposed || !gl || lost || !program || !data.length) return;
      const w = Math.round(width * dpr), h = Math.round(height * dpr);
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
      gl.viewport(0, 0, w, h); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); gl.useProgram(program);
      gl.uniformMatrix3fv(uniforms.rotation, false, rotation); gl.uniform3fv(uniforms.target, target); gl.uniform3fv(uniforms.offset, offset);
      gl.uniform2f(uniforms.viewport, width, height); gl.uniform1f(uniforms.focal, focal); gl.uniform1f(uniforms.dpr, dpr);
      gl.uniform1f(uniforms.time, reduced ? 0 : time); gl.uniform1f(uniforms.alpha, alpha);
      gl.drawArrays(gl.POINTS, 0, data.length / 7); draws++;
      ctx.save(); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.drawImage(canvas, 0, 0, width, height); ctx.restore();
    },
    // WebGL不可/喪失時は既存の惑星描画ループで静止スプライトを1枚追加するだけ。
    fallbackCount(path) { return !gl || lost ? fallback.get(path) || 0 : 0; },
    get stats() { return { mode: gl && !lost ? 'webgl' : 'static', total, files: gl && !lost ? targets.length : Math.min(targets.length, fallbackLimit), electrons: gl && !lost ? data.length / 7 : [...fallback.values()].reduce((sum, count) => sum + count, 0), uploads, draws, limit: gl && !lost ? MAX_ELECTRON_FILES : fallbackLimit }; },
    dispose() { disposed = true; canvas.removeEventListener?.('webglcontextlost', contextLost); canvas.removeEventListener?.('webglcontextrestored', contextRestored); release(); gl?.getExtension('WEBGL_lose_context')?.loseContext(); data = new Float32Array(); targets = []; fallback.clear(); },
  };
}
