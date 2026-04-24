// -*- coding: utf-8 -*-

import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.179.1/build/three.module.js';

const SIZE = 4;
const PLAYERS = {
  black: { label: '黒', next: 'white' },
  white: { label: '白', next: 'black' },
};
const FACES = [
  { id: 'top', label: '上面', short: 'TOP', className: 'face-top' },
  { id: 'left', label: '左面', short: 'LEFT', className: 'face-left' },
  { id: 'front', label: '前面', short: 'FRONT', className: 'face-front' },
  { id: 'right', label: '右面', short: 'RIGHT', className: 'face-right' },
  { id: 'back', label: '後面', short: 'BACK', className: 'face-back' },
  { id: 'bottom', label: '下面', short: 'BOTTOM', className: 'face-bottom' },
];
const FACE_BY_ID = Object.fromEntries(FACES.map((face) => [face.id, face]));
const DIAGONAL_DIRS = [
  { dr: -1, dc: -1 },
  { dr: -1, dc: 1 },
  { dr: 1, dc: -1 },
  { dr: 1, dc: 1 },
];
const ORTHOGONAL_DIRS = ['N', 'S', 'E', 'W'];
const INNER_CELLS = [
  [1, 1], [1, 2],
  [2, 1], [2, 2],
];
const FACE_TRANSFORMS = {
  front:  { position: [0, 0, 2.02], rotation: [0, 0, 0] },
  back:   { position: [0, 0, -2.02], rotation: [0, Math.PI, 0] },
  right:  { position: [2.02, 0, 0], rotation: [0, Math.PI / 2, 0] },
  left:   { position: [-2.02, 0, 0], rotation: [0, -Math.PI / 2, 0] },
  top:    { position: [0, 2.02, 0], rotation: [-Math.PI / 2, 0, 0] },
  bottom: { position: [0, -2.02, 0], rotation: [Math.PI / 2, 0, 0] },
};
const FACE_CAMERA_TARGETS = {
  front:  { x: -0.36, y: 0.38 },
  back:   { x: -0.28, y: Math.PI + 0.36 },
  right:  { x: -0.32, y: Math.PI / 2 + 0.34 },
  left:   { x: -0.32, y: -Math.PI / 2 - 0.34 },
  top:    { x: -1.08, y: 0.38 },
  bottom: { x: 0.82, y: 0.38 },
};

// 黒石・白石のマテリアル定義
const PIECE_DEFS = {
  black: {
    color: 0x0c0c10,
    emissive: 0x103050,
    emissiveIntensity: 0.9,
    roughness: 0.38,
    metalness: 0.55,
  },
  white: {
    color: 0xf2eedd,
    emissive: 0x3a2e14,
    emissiveIntensity: 0.25,
    roughness: 0.45,
    metalness: 0.10,
  },
};

class CubeReversi {
  constructor() {
    this.board = {};
    this.currentPlayer = 'black';
    this.mode = 'normal';
    this.gameOver = false;
    this.cpuEnabled = true;
    this.cpuThinking = false;
    this.lastMove = null;
    this.lastChangedKeys = new Set();
    this.alwaysShowMoves = true;
    this.logItems = [];
    this.three = null;
    this.cellMeshes = new Map();
    this.pieceMeshes = new Map();
    this.flipAnimations = [];
    this.cameraMotion = null;
    this.cameraQueue = [];
    this.isDragging3d = false;
    this.dragMoved3d = false;
    this.dragStart = { x: 0, y: 0 };
    this.rotationStart = { x: 0, y: 0 };
    this.cubeRotation = { x: -0.36, y: 0.42 };

    this.cacheElements();
    this.bindEvents();
    this.init3d();
    this.reset();
  }

  cacheElements() {
    this.cubeNet = document.getElementById('cube-net');
    this.modeLabel = document.getElementById('mode-label');
    this.turnLabel = document.getElementById('turn-label');
    this.blackScore = document.getElementById('black-score');
    this.whiteScore = document.getElementById('white-score');
    this.emptyScore = document.getElementById('empty-score');
    this.message = document.getElementById('message');
    this.battleLog = document.getElementById('battle-log');
    this.cpuToggle = document.getElementById('cpu-toggle');
    this.canvas3d = document.getElementById('cube-3d-canvas');
  }

  bindEvents() {
    document.getElementById('reset-btn').addEventListener('click', () => this.reset());
    document.getElementById('hint-btn').addEventListener('click', () => {
      this.alwaysShowMoves = !this.alwaysShowMoves;
      this.render();
      this.setMessage(this.alwaysShowMoves ? '置ける場所を常時表示します。' : '置ける場所の常時表示を止めます。');
    });
    this.cpuToggle.addEventListener('change', () => {
      this.cpuEnabled = this.cpuToggle.checked;
      this.addLog(this.cpuEnabled ? '白CPUを有効にしました。' : '白CPUを無効にしました。');
      this.maybeCpuTurn();
    });
  }

  reset() {
    this.board = {};
    FACES.forEach((face) => {
      this.board[face.id] = Array.from({ length: SIZE }, () => Array(SIZE).fill(null));
      this.board[face.id][1][1] = 'white';
      this.board[face.id][1][2] = 'black';
      this.board[face.id][2][1] = 'black';
      this.board[face.id][2][2] = 'white';
    });
    this.currentPlayer = 'black';
    this.mode = 'normal';
    this.gameOver = false;
    this.cpuThinking = false;
    this.lastMove = null;
    this.lastChangedKeys = new Set();
    this.logItems = [];
    this.flipAnimations = [];
    this.cameraQueue = [];
    this.cpuEnabled = this.cpuToggle.checked;
    this.addLog('新しい 6 面対局を開始しました。');
    this.setMessage('黒の手番です。光っているマスに置けます。');
    this.render();
    this.sync3dBoard();
  }

  render() {
    const legalKeys = new Set(this.getLegalMoves(this.currentPlayer).map((move) => this.key(move)));
    if (this.cubeNet) {
      this.cubeNet.innerHTML = '';
      FACES.forEach((face) => {
        const faceEl = document.createElement('section');
        faceEl.className = `face ${face.className}`;
        faceEl.innerHTML = `
          <div class="face-title">
            <span>${face.label}</span>
            <small>${face.short}</small>
          </div>
        `;
        const grid = document.createElement('div');
        grid.className = 'grid';
        for (let row = 0; row < SIZE; row += 1) {
          for (let col = 0; col < SIZE; col += 1) {
            const cell = document.createElement('button');
            const move = { face: face.id, row, col };
            const key = this.key(move);
            const piece = this.board[face.id][row][col];
            cell.type = 'button';
            cell.className = 'cell';
            cell.setAttribute('aria-label', `${face.label} ${row + 1}-${col + 1}`);
            if (this.alwaysShowMoves && legalKeys.has(key)) {
              cell.classList.add(this.mode === 'challenge' ? 'challenge' : 'legal');
            }
            if (this.lastMove && this.key(this.lastMove) === key) {
              cell.classList.add('last');
            }
            if (piece) {
              const pieceEl = document.createElement('span');
              pieceEl.className = `piece ${piece}`;
              cell.appendChild(pieceEl);
            }
            cell.addEventListener('click', () => this.handleCellClick(face.id, row, col));
            grid.appendChild(cell);
          }
        }
        faceEl.appendChild(grid);
        this.cubeNet.appendChild(faceEl);
      });
    }
    this.updateStatus();
    this.renderLog();
    this.sync3dBoard();
  }

  updateStatus() {
    const score = this.countPieces();
    this.blackScore.textContent = String(score.black);
    this.whiteScore.textContent = String(score.white);
    this.emptyScore.textContent = String(score.empty);
    this.modeLabel.textContent = this.mode === 'challenge' ? 'チャレンジモード' : '通常モード';
    if (this.gameOver) {
      const result = score.black === score.white ? '引き分け' : `${score.black > score.white ? '黒' : '白'}の勝ち`;
      this.turnLabel.textContent = result;
    } else if (this.cpuThinking) {
      this.turnLabel.textContent = 'CPU思考中';
    } else {
      this.turnLabel.textContent = `${PLAYERS[this.currentPlayer].label}の手番`;
    }
  }

  renderLog() {
    this.battleLog.innerHTML = '';
    this.logItems.slice(-12).reverse().forEach((item) => {
      const p = document.createElement('p');
      p.textContent = item;
      this.battleLog.appendChild(p);
    });
  }

  handleCellClick(face, row, col) {
    if (this.gameOver || this.cpuThinking) return;
    if (this.cpuEnabled && this.currentPlayer === 'white') return;
    this.playMove({ face, row, col }, 'human');
  }

  playMove(move, actor) {
    const legalMoves = this.getLegalMoves(this.currentPlayer);
    const selected = legalMoves.find((item) => this.sameMove(item, move));
    if (!selected) {
      this.setMessage(this.mode === 'challenge' ? '空いているマスを選んでください。' : 'そこには置けません。光っているマスを選んでください。');
      return false;
    }

    const flips = selected.flips ?? [];
    const player = this.currentPlayer;
    this.board[move.face][move.row][move.col] = player;
    flips.forEach((cell) => {
      this.board[cell.face][cell.row][cell.col] = player;
    });
    this.lastMove = move;
    this.lastChangedKeys = new Set([this.key(move), ...flips.map((cell) => this.key(cell))]);
    this.addLog(`${actor === 'cpu' ? 'CPU' : PLAYERS[player].label} が ${FACE_BY_ID[move.face].label} ${move.row + 1}-${move.col + 1} に置きました。反転 ${flips.length} 枚。`);

    this.currentPlayer = PLAYERS[player].next;
    this.afterMove();
    this.start3dFlipAnimation([move, ...flips], player);
    return true;
  }

  afterMove() {
    if (this.mode === 'normal') {
      const currentLegal = this.getLegalMoves(this.currentPlayer);
      const otherLegal = this.getLegalMoves(PLAYERS[this.currentPlayer].next);
      if (currentLegal.length === 0 && otherLegal.length === 0) {
        this.enterChallengeMode();
        return;
      }
      if (currentLegal.length === 0) {
        this.addLog(`${PLAYERS[this.currentPlayer].label} は置けないためパスしました。`);
        this.currentPlayer = PLAYERS[this.currentPlayer].next;
      }
    } else if (this.countPieces().empty === 0) {
      this.finishGame();
      return;
    }

    this.render();
    this.setMessage(`${PLAYERS[this.currentPlayer].label}の手番です。`);
    this.maybeCpuTurn();
  }

  enterChallengeMode() {
    this.mode = 'challenge';
    INNER_CELLS.forEach(([row, col]) => {
      FACES.forEach((face) => {
        this.board[face.id][row][col] = null;
      });
    });
    this.lastChangedKeys = new Set(FACES.flatMap((face) => INNER_CELLS.map(([row, col]) => this.key({ face: face.id, row, col }))));
    this.addLog('両者とも通常手がなくなりました。チャレンジモード突入。全6面の内側4マスをクリア。');
    this.setMessage('チャレンジモード: 空きマスならどこでも置けます。反転できる列は反転します。');
    this.render();
    this.maybeCpuTurn();
  }

  finishGame() {
    this.gameOver = true;
    const score = this.countPieces();
    const result = score.black === score.white ? '引き分けです。' : `${score.black > score.white ? '黒' : '白'}の勝ちです。`;
    this.addLog(`終局: 黒 ${score.black} / 白 ${score.white}。${result}`);
    this.setMessage(`終局: ${result}`);
    this.render();
  }

  maybeCpuTurn() {
    if (!this.cpuEnabled || this.gameOver || this.currentPlayer !== 'white') return;
    this.cpuThinking = true;
    this.updateStatus();
    window.setTimeout(() => {
      if (!this.cpuEnabled || this.gameOver || this.currentPlayer !== 'white') {
        this.cpuThinking = false;
        this.render();
        return;
      }
      const move = this.chooseCpuMove();
      this.cpuThinking = false;
      if (move) this.playMove(move, 'cpu');
    }, 420);
  }

  chooseCpuMove() {
    const moves = this.getLegalMoves('white');
    if (moves.length === 0) return null;
    const scored = moves.map((move) => ({ move, score: this.evaluateMove(move, 'white') }));
    scored.sort((a, b) => b.score - a.score);
    const bestScore = scored[0].score;
    const bestMoves = scored.filter((item) => item.score === bestScore);
    return bestMoves[Math.floor(Math.random() * bestMoves.length)].move;
  }

  evaluateMove(move, player) {
    const flips = move.flips?.length ?? 0;
    const edge = move.row === 0 || move.row === SIZE - 1 || move.col === 0 || move.col === SIZE - 1;
    const corner = (move.row === 0 || move.row === SIZE - 1) && (move.col === 0 || move.col === SIZE - 1);
    const challengeCenter = this.mode === 'challenge' && move.row >= 2 && move.row <= 3 && move.col >= 2 && move.col <= 3;
    const boardCopy = this.cloneBoard();
    boardCopy[move.face][move.row][move.col] = player;
    (move.flips ?? []).forEach((cell) => { boardCopy[cell.face][cell.row][cell.col] = player; });
    const mobility = this.getLegalMoves(PLAYERS[player].next, boardCopy).length;
    return flips * 10 + (corner ? 30 : 0) + (edge ? 7 : 0) + (challengeCenter ? 5 : 0) - mobility * 2;
  }

  getLegalMoves(player, board = this.board) {
    const moves = [];
    FACES.forEach((face) => {
      for (let row = 0; row < SIZE; row += 1) {
        for (let col = 0; col < SIZE; col += 1) {
          if (board[face.id][row][col]) continue;
          if (this.mode === 'challenge' && board === this.board) {
            const flips = this.collectAllFlips({ face: face.id, row, col }, player, board);
            moves.push({ face: face.id, row, col, flips });
            continue;
          }
          const flips = this.collectAllFlips({ face: face.id, row, col }, player, board);
          if (flips.length > 0) moves.push({ face: face.id, row, col, flips });
        }
      }
    });
    return moves;
  }

  collectAllFlips(move, player, board) {
    const result = [];
    DIAGONAL_DIRS.forEach((dir) => {
      result.push(...this.collectDiagonalFlips(move, player, dir, board));
    });
    ORTHOGONAL_DIRS.forEach((dir) => {
      result.push(...this.collectCubeFlips(move, player, dir, board));
    });
    return this.uniqueCells(result);
  }

  collectDiagonalFlips(move, player, dir, board) {
    const opponent = PLAYERS[player].next;
    const line = [];
    let row = move.row + dir.dr;
    let col = move.col + dir.dc;
    while (row >= 0 && row < SIZE && col >= 0 && col < SIZE) {
      const piece = board[move.face][row][col];
      if (piece === opponent) {
        line.push({ face: move.face, row, col });
      } else if (piece === player) {
        return line.length > 0 ? line : [];
      } else {
        return [];
      }
      row += dir.dr;
      col += dir.dc;
    }
    return [];
  }

  collectCubeFlips(move, player, dir, board) {
    const opponent = PLAYERS[player].next;
    const line = [];
    let cursor = { ...move, dir };
    const seen = new Set();

    for (let step = 0; step < FACES.length * SIZE + 2; step += 1) {
      cursor = this.stepCube(cursor);
      if (!cursor) return [];
      const cursorKey = `${cursor.face}:${cursor.row}:${cursor.col}:${cursor.dir}`;
      if (seen.has(cursorKey)) return [];
      seen.add(cursorKey);
      const piece = board[cursor.face][cursor.row][cursor.col];
      if (piece === opponent) {
        line.push({ face: cursor.face, row: cursor.row, col: cursor.col });
      } else if (piece === player) {
        return line.length > 0 ? line : [];
      } else {
        return [];
      }
    }
    return [];
  }

  stepCube(cursor) {
    const { face, row, col, dir } = cursor;
    if (dir === 'N' && row > 0) return { face, row: row - 1, col, dir };
    if (dir === 'S' && row < SIZE - 1) return { face, row: row + 1, col, dir };
    if (dir === 'E' && col < SIZE - 1) return { face, row, col: col + 1, dir };
    if (dir === 'W' && col > 0) return { face, row, col: col - 1, dir };

    const last = SIZE - 1;
    const map = {
      front: {
        N: { face: 'top', row: last, col, dir: 'N' },
        S: { face: 'bottom', row: 0, col, dir: 'S' },
        E: { face: 'right', row, col: 0, dir: 'E' },
        W: { face: 'left', row, col: last, dir: 'W' },
      },
      right: {
        N: { face: 'top', row: last - col, col: last, dir: 'W' },
        S: { face: 'bottom', row: col, col: last, dir: 'W' },
        E: { face: 'back', row, col: 0, dir: 'E' },
        W: { face: 'front', row, col: last, dir: 'W' },
      },
      back: {
        N: { face: 'top', row: 0, col: last - col, dir: 'S' },
        S: { face: 'bottom', row: last, col: last - col, dir: 'N' },
        E: { face: 'left', row, col: 0, dir: 'E' },
        W: { face: 'right', row, col: last, dir: 'W' },
      },
      left: {
        N: { face: 'top', row: col, col: 0, dir: 'E' },
        S: { face: 'bottom', row: last - col, col: 0, dir: 'E' },
        E: { face: 'front', row, col: 0, dir: 'E' },
        W: { face: 'back', row, col: last, dir: 'W' },
      },
      top: {
        N: { face: 'back', row: 0, col: last - col, dir: 'S' },
        S: { face: 'front', row: 0, col, dir: 'S' },
        E: { face: 'right', row: 0, col: last - row, dir: 'S' },
        W: { face: 'left', row: 0, col: row, dir: 'S' },
      },
      bottom: {
        N: { face: 'front', row: last, col, dir: 'N' },
        S: { face: 'back', row: last, col: last - col, dir: 'N' },
        E: { face: 'right', row: last, col, dir: 'N' },
        W: { face: 'left', row: last, col: last - col, dir: 'N' },
      },
    };
    return map[face][dir] ?? null;
  }

  countPieces() {
    const score = { black: 0, white: 0, empty: 0 };
    FACES.forEach((face) => {
      for (let row = 0; row < SIZE; row += 1) {
        for (let col = 0; col < SIZE; col += 1) {
          const piece = this.board[face.id][row][col];
          if (piece) score[piece] += 1;
          else score.empty += 1;
        }
      }
    });
    return score;
  }

  uniqueCells(cells) {
    const seen = new Set();
    return cells.filter((cell) => {
      const key = this.key(cell);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  cloneBoard() {
    const next = {};
    FACES.forEach((face) => {
      next[face.id] = this.board[face.id].map((row) => [...row]);
    });
    return next;
  }

  sameMove(a, b) {
    return a.face === b.face && a.row === b.row && a.col === b.col;
  }

  key(move) {
    return `${move.face}:${move.row}:${move.col}`;
  }

  setMessage(text) {
    this.message.textContent = text;
  }

  addLog(text) {
    this.logItems.push(text);
  }

  // ─── 3D ───────────────────────────────────────────────────

  init3d() {
    if (!this.canvas3d || !THREE.WebGLRenderer) return;

    const renderer = new THREE.WebGLRenderer({ canvas: this.canvas3d, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    camera.position.set(0, 0, 8.4);

    const cube = new THREE.Group();
    scene.add(cube);

    // アンビエント光（全体を均一に明るく）
    scene.add(new THREE.AmbientLight(0xffffff, 0.90));
    // キーライト（上前方）
    const keyLight = new THREE.DirectionalLight(0xdcf0ff, 1.4);
    keyLight.position.set(4, 6, 8);
    scene.add(keyLight);
    // フィルライト（下後方）
    const fillLight = new THREE.DirectionalLight(0xfff0cc, 0.55);
    fillLight.position.set(-5, -4, 3);
    scene.add(fillLight);
    // リムライト（黒石のシルエット強調）
    const rimLight = new THREE.DirectionalLight(0x88ccff, 0.40);
    rimLight.position.set(0, -2, -6);
    scene.add(rimLight);

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    this.three = { renderer, scene, camera, cube, raycaster, pointer };
    this.build3dCube();
    this.bind3dControls();
    this.resize3d();
    window.addEventListener('resize', () => this.resize3d());
    this.animate3d();
  }

  build3dCube() {
    const { cube } = this.three;
    cube.clear();
    this.cellMeshes.clear();
    this.pieceMeshes.clear();

    // ボード面: 深いグリーン（伝統的なリバーシ盤）
    const boardMaterial = new THREE.MeshStandardMaterial({
      color: 0x1b5230,
      roughness: 0.70,
      metalness: 0.06,
      side: THREE.DoubleSide,
    });
    // グリッド線: 明るいグリーン
    const lineMaterial = new THREE.LineBasicMaterial({ color: 0x55cc77, transparent: true, opacity: 0.65 });
    const cellSize = 4 / SIZE;
    const gap = 0.035;

    FACES.forEach((face) => {
      const faceGroup = new THREE.Group();
      const transform = FACE_TRANSFORMS[face.id];
      faceGroup.position.set(...transform.position);
      faceGroup.rotation.set(...transform.rotation);
      cube.add(faceGroup);

      const plane = new THREE.Mesh(new THREE.PlaneGeometry(4, 4), boardMaterial.clone());
      plane.userData = { type: 'face', face: face.id };
      faceGroup.add(plane);

      for (let i = 0; i <= SIZE; i += 1) {
        const p = -2 + i * cellSize;
        const hGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-2, p, 0.015), new THREE.Vector3(2, p, 0.015)]);
        const vGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(p, -2, 0.015), new THREE.Vector3(p, 2, 0.015)]);
        faceGroup.add(new THREE.Line(hGeo, lineMaterial));
        faceGroup.add(new THREE.Line(vGeo, lineMaterial));
      }

      for (let row = 0; row < SIZE; row += 1) {
        for (let col = 0; col < SIZE; col += 1) {
          const key = this.key({ face: face.id, row, col });
          const cell = new THREE.Mesh(
            new THREE.PlaneGeometry(cellSize - gap, cellSize - gap),
            new THREE.MeshBasicMaterial({ color: 0x5effc6, transparent: true, opacity: 0, side: THREE.DoubleSide }),
          );
          cell.position.set(-2 + (col + 0.5) * cellSize, 2 - (row + 0.5) * cellSize, 0.025);
          cell.userData = { type: 'cell', face: face.id, row, col };
          faceGroup.add(cell);
          this.cellMeshes.set(key, cell);
        }
      }
    });
  }

  sync3dBoard() {
    if (!this.three) return;
    const legalKeys = new Set(this.getLegalMoves(this.currentPlayer).map((move) => this.key(move)));
    this.cellMeshes.forEach((mesh, key) => {
      const isLast = this.lastMove && this.key(this.lastMove) === key;
      const isLegal = this.alwaysShowMoves && legalKeys.has(key);
      mesh.material.opacity = isLast ? 0.50 : (isLegal ? 0.36 : 0);
      mesh.material.color.set(isLast ? 0xffe066 : (this.mode === 'challenge' ? 0xffaa33 : 0x5effc6));
    });

    FACES.forEach((face) => {
      for (let row = 0; row < SIZE; row += 1) {
        for (let col = 0; col < SIZE; col += 1) {
          const key = this.key({ face: face.id, row, col });
          const piece = this.board[face.id][row][col];
          if (!piece) {
            this.remove3dPiece(key);
          } else {
            this.ensure3dPiece({ face: face.id, row, col }, piece);
          }
        }
      }
    });
  }

  ensure3dPiece(move, player) {
    const key = this.key(move);
    const existing = this.pieceMeshes.get(key);
    const def = PIECE_DEFS[player];
    if (existing) {
      existing.userData.player = player;
      existing.material.color.set(def.color);
      existing.material.emissive.set(def.emissive);
      existing.material.emissiveIntensity = def.emissiveIntensity;
      return existing;
    }

    const cell = this.cellMeshes.get(key);
    if (!cell) return null;
    const material = new THREE.MeshStandardMaterial({
      color: def.color,
      emissive: def.emissive,
      emissiveIntensity: def.emissiveIntensity,
      roughness: def.roughness,
      metalness: def.metalness,
    });
    const piece = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.12, 40), material);
    piece.position.copy(cell.position);
    piece.position.z = 0.105;
    piece.rotation.x = Math.PI / 2;
    piece.scale.setScalar(0.01);
    piece.userData = { player, scaleTarget: 1 };
    cell.parent.add(piece);
    this.pieceMeshes.set(key, piece);
    this.flipAnimations.push({ mesh: piece, start: performance.now(), duration: 380, type: 'drop', player });
    return piece;
  }

  remove3dPiece(key) {
    const piece = this.pieceMeshes.get(key);
    if (!piece) return;
    piece.parent?.remove(piece);
    piece.geometry.dispose();
    piece.material.dispose();
    this.pieceMeshes.delete(key);
  }

  // 1枚ずつ順番にフリップ + カメラキューを積む
  start3dFlipAnimation(cells, player) {
    if (!this.three) return;
    const now = performance.now();
    const perPiece = 340;   // 次のコマが開始するまでの間隔 (ms)
    const flipDur = 420;    // 1コマのフリップ所要時間 (ms)
    const camLead = 80;     // フリップ開始より少し早くカメラを動かす

    cells.forEach((cell, index) => {
      const flipStart = now + index * perPiece;

      // 既存アニメーションと重複しないよう削除
      this.flipAnimations = this.flipAnimations.filter((a) => a.mesh !== this.pieceMeshes.get(this.key(cell)));

      if (index === 0) {
        // 置いたコマはドロップアニメーション
        const piece = this.ensure3dPiece(cell, player);
        if (!piece) return;
        this.flipAnimations = this.flipAnimations.filter((a) => a.mesh !== piece);
        this.flipAnimations.push({ mesh: piece, start: now, duration: 300, type: 'drop', player });
      } else {
        // 反転コマは順番にフリップ
        const piece = this.ensure3dPiece(cell, player);
        if (!piece) return;
        this.flipAnimations.push({ mesh: piece, start: flipStart, duration: flipDur, type: 'flip', player });
      }

      // カメラキューにその面へのフォーカスを積む
      const camTime = Math.max(now, flipStart - camLead);
      this.cameraQueue.push({ time: camTime, face: cell.face });
    });

    // カメラキューを時刻順に並べ直す
    this.cameraQueue.sort((a, b) => a.time - b.time);
  }

  focus3dCamera(face) {
    const target = FACE_CAMERA_TARGETS[face] ?? FACE_CAMERA_TARGETS.front;
    this.cameraMotion = {
      start: performance.now(),
      duration: 300,   // 短めにして次のコマに追いつけるようにする
      fromX: this.cubeRotation.x,
      fromY: this.cubeRotation.y,
      toX: target.x,
      toY: target.y,
    };
  }

  bind3dControls() {
    const canvas = this.canvas3d;
    canvas.addEventListener('pointerdown', (event) => {
      this.isDragging3d = true;
      this.dragMoved3d = false;
      this.cameraMotion = null;
      this.dragStart = { x: event.clientX, y: event.clientY };
      this.rotationStart = { ...this.cubeRotation };
      canvas.setPointerCapture(event.pointerId);
    });
    canvas.addEventListener('pointermove', (event) => {
      if (!this.isDragging3d) return;
      const dx = event.clientX - this.dragStart.x;
      const dy = event.clientY - this.dragStart.y;
      if (Math.hypot(dx, dy) > 6) this.dragMoved3d = true;
      this.cubeRotation.y = this.rotationStart.y + dx * 0.008;
      this.cubeRotation.x = Math.max(-1.35, Math.min(1.1, this.rotationStart.x + dy * 0.008));
    });
    canvas.addEventListener('pointerup', (event) => {
      this.isDragging3d = false;
      canvas.releasePointerCapture(event.pointerId);
      if (!this.dragMoved3d) {
        this.handle3dPick(event);
      }
    });
    canvas.addEventListener('pointercancel', () => {
      this.isDragging3d = false;
    });
  }

  handle3dPick(event) {
    if (!this.three || this.gameOver || this.cpuThinking) return;
    if (this.cpuEnabled && this.currentPlayer === 'white') return;
    const rect = this.canvas3d.getBoundingClientRect();
    this.three.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.three.pointer.y = -(((event.clientY - rect.top) / rect.height) * 2 - 1);
    this.three.raycaster.setFromCamera(this.three.pointer, this.three.camera);
    const hits = this.three.raycaster.intersectObjects([...this.cellMeshes.values()], false);
    const cell = hits.find((hit) => hit.object?.userData?.type === 'cell')?.object;
    if (!cell) return;
    const { face, row, col } = cell.userData;
    this.handleCellClick(face, row, col);
  }

  resize3d() {
    if (!this.three) return;
    const rect = this.canvas3d.getBoundingClientRect();
    const width = Math.max(1, Math.floor(rect.width));
    const height = Math.max(1, Math.floor(rect.height));
    this.three.renderer.setSize(width, height, false);
    this.three.camera.aspect = width / height;
    this.three.camera.updateProjectionMatrix();
  }

  animate3d() {
    if (!this.three) return;
    const now = performance.now();

    // カメラキューを処理（時刻が来たものを1つずつ発火）
    if (this.cameraQueue.length > 0 && now >= this.cameraQueue[0].time) {
      this.focus3dCamera(this.cameraQueue[0].face);
      this.cameraQueue.shift();
    }

    // カメラモーション
    if (this.cameraMotion) {
      const t = Math.min(1, (now - this.cameraMotion.start) / this.cameraMotion.duration);
      const eased = 1 - Math.pow(1 - t, 3);
      this.cubeRotation.x = this.cameraMotion.fromX + (this.cameraMotion.toX - this.cameraMotion.fromX) * eased;
      this.cubeRotation.y = this.cameraMotion.fromY + (this.cameraMotion.toY - this.cameraMotion.fromY) * eased;
      if (t >= 1) this.cameraMotion = null;
    }

    this.three.cube.rotation.x = this.cubeRotation.x;
    this.three.cube.rotation.y = this.cubeRotation.y;

    // フリップアニメーション
    this.flipAnimations = this.flipAnimations.filter((anim) => {
      const elapsed = now - anim.start;
      if (elapsed < 0) return true; // まだ開始前
      const t = Math.min(1, elapsed / anim.duration);
      const def = PIECE_DEFS[anim.player];
      if (anim.type === 'drop') {
        const eased = 1 - Math.pow(1 - t, 3);
        anim.mesh.scale.setScalar(eased);
      } else {
        const spin = Math.sin(t * Math.PI);
        anim.mesh.rotation.x = Math.PI / 2 + spin * Math.PI;
        anim.mesh.scale.setScalar(1 + spin * 0.28);
        // 折り返し点を過ぎたら色を切り替え
        if (t > 0.48) {
          anim.mesh.material.color.set(def.color);
          anim.mesh.material.emissive.set(def.emissive);
          anim.mesh.material.emissiveIntensity = def.emissiveIntensity;
        }
      }
      if (t >= 1) {
        anim.mesh.rotation.x = Math.PI / 2;
        anim.mesh.scale.setScalar(1);
        anim.mesh.material.color.set(def.color);
        anim.mesh.material.emissive.set(def.emissive);
        anim.mesh.material.emissiveIntensity = def.emissiveIntensity;
      }
      return t < 1;
    });

    this.three.renderer.render(this.three.scene, this.three.camera);
    window.requestAnimationFrame(() => this.animate3d());
  }
}

window.addEventListener('DOMContentLoaded', () => {
  new CubeReversi();
});
