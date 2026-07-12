(() => {
  'use strict'

  const W = 720
  const H = 1080
  const canvas = document.querySelector('#game')
  const ctx = canvas.getContext('2d')
  const el = (selector) => document.querySelector(selector)
  const ui = {
    score: el('#score'), high: el('#high-score'), multiplier: el('#multiplier'),
    heatBar: el('#heat-bar'), heatValue: el('#heat-value'), balls: el('#balls'),
    announcer: el('#announcer'), combo: el('#combo'), launch: el('#launch'), sound: el('#sound'), modeBadge: el('#mode-badge'),
    title: el('#title-screen'), pause: el('#pause-screen'), gameover: el('#gameover-screen'),
    final: el('#final-score'), flash: el('#flash')
  }

  const board = [[104,142],[218,72],[502,72],[616,142],[642,878],[516,1012],[440,1000],[412,935],[308,935],[280,1000],[204,1012],[78,878]]
  const walls = [
    [[104,142],[218,72]], [[218,72],[502,72]], [[502,72],[616,142]],
    [[104,142],[78,878]], [[78,878],[204,1012]], [[204,1012],[280,1000]],
    [[616,142],[642,878]], [[642,878],[516,1012]], [[516,1012],[440,1000]],
    [[556,390],[556,906]]
  ]
  const launchGuide = [[556,390],[556,856]]
  const core = { x: 360, y: 465, r: 61 }
  const rifts = [
    { x: 188, y: 410, r: 29, color: '#ff3b98', label: 'UMBRA' },
    { x: 472, y: 726, r: 32, color: '#3cf6ff', label: 'AURORA' }
  ]
  const moon = { angle: -1.2, orbitX: 174, orbitY: 116, r: 23, cooldown: 0 }
  const photonSail = { x: 214, y: 730, length: 174, radius: 9, cooldown: 0 }
  const bumpers = [
    { x: 246, y: 310, r: 39, color: '#ff3f63', label: 'FLARE', cooldown: 0 },
    { x: 474, y: 310, r: 39, color: '#39efff', label: 'CORONA', cooldown: 0 },
    { x: 360, y: 205, r: 34, color: '#ffb632', label: 'HELIOS', cooldown: 0 }
  ]
  const targets = [
    { x: 155, y: 500, letter: 'S', on: false, cooldown: 0 },
    { x: 150, y: 565, letter: 'O', on: false, cooldown: 0 },
    { x: 155, y: 630, letter: 'L', on: false, cooldown: 0 }
  ]
  const gates = [
    { x: 520, y: 472, on: true, phase: 0 }, { x: 528, y: 535, on: true, phase: 1 },
    { x: 526, y: 598, on: true, phase: 2 }
  ]
  const flippers = [
    { side: 'left', x: 261, y: 875, length: 116, angle: .32, rest: .32, active: -.72 },
    { side: 'right', x: 459, y: 875, length: 116, angle: Math.PI - .32, rest: Math.PI - .32, active: Math.PI + .72 }
  ]
  const keys = { left: false, right: false }
  const pointers = new Map()

  let mode = 'title'
  let demoMode = false
  let demoHeatClock = 0
  let demoElapsed = 0
  let demoRestartAt = 0
  let score = 0
  let highScore = Number(localStorage.getItem('x-pinball-sol-high') || 0)
  let lives = 3
  let heat = 0
  let multiplier = 1
  let combo = 0
  let comboTimer = 0
  let overdrive = 0
  let gravityPolarity = 1
  let polarityTimer = 0
  let phase = 'ORBITAL DAWN'
  let riftTransfers = 0
  let balls = []
  let particles = []
  let shockwaves = []
  let popups = []
  let sparks = []
  let stars = []
  let charging = false
  let charge = 0
  let shake = 0
  let chroma = 0
  let flash = 0
  let time = 0
  let last = 0
  let raf = 0
  let muted = false
  let audio = null
  let noiseBuffer = null
  let announcementTimer = 0
  let launchPointerId = null

  function random(min, max) { return min + Math.random() * (max - min) }
  function clamp(value, min, max) { return Math.max(min, Math.min(max, value)) }

  function getMoonPosition() {
    return {
      x: core.x + Math.cos(moon.angle) * moon.orbitX,
      y: core.y + Math.sin(moon.angle) * moon.orbitY,
      r: moon.r
    }
  }

  function getPhotonSail() {
    const angle = -.58 + Math.sin(time * .72) * .34 + (gravityPolarity < 0 ? .22 : 0)
    return {
      start: [photonSail.x, photonSail.y],
      end: [photonSail.x + Math.cos(angle) * photonSail.length, photonSail.y + Math.sin(angle) * photonSail.length],
      angle
    }
  }

  function updatePhase() {
    const next = overdrive > 0 ? 'SINGULARITY BLOOM' : gravityPolarity < 0 ? 'ECLIPSE REVERSE' : heat >= 66 ? 'CORONAL STORM' : heat >= 30 ? 'GRAVITY TIDE' : 'ORBITAL DAWN'
    if (next !== phase) {
      phase = next
      if (mode === 'play') announce(phase)
      updateHud()
    }
  }

  function resize() {
    const ratio = Math.min(innerWidth / W, innerHeight / H)
    const dpr = Math.min(devicePixelRatio || 1, 2)
    canvas.width = Math.round(W * ratio * dpr)
    canvas.height = Math.round(H * ratio * dpr)
    canvas.style.width = `${W * ratio}px`
    canvas.style.height = `${H * ratio}px`
    ctx.setTransform(ratio * dpr, 0, 0, ratio * dpr, 0, 0)
  }

  function initStars() {
    stars = Array.from({ length: 90 }, () => ({
      x: Math.random() * W, y: Math.random() * H, z: random(.2, 1), phase: random(0, Math.PI * 2)
    }))
  }

  function ensureAudio() {
    if (muted) return null
    try {
      audio ||= new AudioContext()
      if (audio.state === 'suspended') audio.resume()
      return audio
    } catch (_) { return null }
  }

  function tone(freq, duration = .07, type = 'sawtooth', gain = .035, sweep = 1) {
    const ac = ensureAudio()
    if (!ac) return
    const osc = ac.createOscillator()
    const amp = ac.createGain()
    const now = ac.currentTime
    osc.type = type
    osc.frequency.setValueAtTime(freq, now)
    osc.frequency.exponentialRampToValueAtTime(Math.max(30, freq * sweep), now + duration)
    amp.gain.setValueAtTime(gain, now)
    amp.gain.exponentialRampToValueAtTime(.0001, now + duration)
    osc.connect(amp).connect(ac.destination)
    osc.start(now); osc.stop(now + duration)
  }

  function noise(duration = .08, gain = .025) {
    const ac = ensureAudio()
    if (!ac) return
    if (!noiseBuffer) {
      noiseBuffer = ac.createBuffer(1, ac.sampleRate, ac.sampleRate)
      const data = noiseBuffer.getChannelData(0)
      for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1
    }
    const source = ac.createBufferSource(); const amp = ac.createGain(); const filter = ac.createBiquadFilter()
    source.buffer = noiseBuffer; filter.type = 'bandpass'; filter.frequency.value = 1400
    amp.gain.setValueAtTime(gain, ac.currentTime); amp.gain.exponentialRampToValueAtTime(.0001, ac.currentTime + duration)
    source.connect(filter).connect(amp).connect(ac.destination); source.start(); source.stop(ac.currentTime + duration)
  }

  function announce(text) {
    ui.announcer.textContent = text
    ui.announcer.classList.remove('show')
    void ui.announcer.offsetWidth
    ui.announcer.classList.add('show')
    clearTimeout(announcementTimer)
    announcementTimer = setTimeout(() => ui.announcer.classList.remove('show'), 950)
  }

  function updateHud() {
    ui.score.textContent = String(score).padStart(7, '0')
    ui.high.textContent = String(highScore).padStart(7, '0')
    ui.multiplier.textContent = `×${multiplier}`
    ui.heatBar.style.width = `${heat}%`
    ui.heatValue.textContent = overdrive > 0 ? `BLOOM ${overdrive.toFixed(1)}s` : `${Math.round(heat)}%`
    ui.modeBadge.textContent = `${demoMode ? 'AUTOPILOT' : 'PILOT'} // ${phase}`
    ui.modeBadge.classList.toggle('demo', demoMode || gravityPolarity < 0)
    ui.balls.replaceChildren(...Array.from({ length: 3 }, (_, i) => {
      const node = document.createElement('i')
      if (i >= lives) node.className = 'lost'
      return node
    }))
    ui.combo.textContent = combo > 1 ? `FLARE CHAIN ${combo} // ×${multiplier}` : ''
    ui.combo.classList.toggle('active', combo > 1)
  }

  function makeBall(x = 584, y = 904, lane = true, vx = 0, vy = 0) {
    return { x, y, vx, vy, r: 13, lane, entered: !lane, alive: true, born: time, trail: [], riftCooldown: 0, sailCooldown: 0, hue: Math.random() > .5 ? '#ffdd75' : '#5cf8ff' }
  }

  function resetRound() {
    balls = [makeBall()]
    charging = false; charge = 0
    ui.launch.classList.add('visible')
  }

  function startGame(useDemo = false) {
    ensureAudio()
    demoMode = useDemo
    demoHeatClock = 0
    demoElapsed = 0
    demoRestartAt = 0
    mode = 'play'; score = 0; lives = 3; heat = 0; multiplier = 1; combo = 0; comboTimer = 0; overdrive = 0
    gravityPolarity = 1; polarityTimer = 0; phase = 'ORBITAL DAWN'; riftTransfers = 0; moon.angle = -1.2; moon.cooldown = 0; photonSail.cooldown = 0
    particles = []; shockwaves = []; popups = []; sparks = []
    targets.forEach((target) => { target.on = false; target.cooldown = 0 })
    gates.forEach((gate) => { gate.on = true })
    ui.title.classList.remove('visible'); ui.gameover.classList.remove('visible'); ui.pause.classList.remove('visible')
    resetRound(); updateHud(); announce(demoMode ? 'AUTOPILOT ONLINE' : 'CORE LINKED'); tone(95, .35, 'sawtooth', .07, 5)
  }

  function launchBall(forcedCharge = null) {
    const ball = balls.find((item) => item.lane && item.alive)
    if (!ball || mode !== 'play') return
    const launchCharge = forcedCharge == null ? charge : clamp(forcedCharge, 0, 1)
    const power = 1 + launchCharge * .18
    ball.lane = false; ball.vx = -55 - launchCharge * 95; ball.vy = -1010 * power
    charging = false; charge = 0; ui.launch.classList.remove('visible')
    tone(85, .2, 'sawtooth', .06, 4); noise(.12, .035); burst(ball.x, ball.y, '#ff7b32', 28, 310)
  }

  function addScore(points, label, x, y, color = '#ffe177') {
    const gained = Math.round(points * multiplier)
    score += gained; combo++; comboTimer = 2.15
    multiplier = clamp(1 + Math.floor(combo / 4) + (overdrive > 0 ? 2 : 0), 1, 8)
    if (!demoMode && score > highScore) {
      highScore = score
      localStorage.setItem('x-pinball-sol-high', String(highScore))
    }
    popups.push({ x, y, text: label || `+${gained}`, color, life: 1, max: 1 })
    updateHud()
  }

  function addHeat(amount) {
    if (overdrive > 0) return
    heat = clamp(heat + amount, 0, 100)
    if (heat >= 100) activateOverdrive()
    updateHud()
  }

  function activateOverdrive() {
    heat = 100; overdrive = 12; multiplier = clamp(multiplier + 2, 3, 8); phase = 'SINGULARITY BLOOM'
    updateHud(); announce('SINGULARITY BLOOM'); flash = .8; shake = 20; chroma = 1
    burst(360, 465, '#fff3a0', 100, 520); shockwaves.push({ x: 360, y: 465, r: 25, life: 1, max: 1, color: '#ff512c' })
    if (balls.filter((ball) => ball.alive).length < 2) {
      balls.push(makeBall(340, 410, false, -270, -410), makeBall(380, 410, false, 270, -410))
      announce('PHOTON MULTIBALL')
    }
    tone(70, .55, 'sawtooth', .09, 8); setTimeout(() => tone(520, .4, 'square', .04, 2), 120)
  }

  function burst(x, y, color, count = 18, speed = 240) {
    for (let i = 0; i < count; i++) {
      const angle = random(0, Math.PI * 2); const velocity = random(speed * .25, speed)
      particles.push({ x, y, vx: Math.cos(angle) * velocity, vy: Math.sin(angle) * velocity, color, size: random(1.5, 5), life: random(.28, .8), max: .8 })
    }
  }

  function impact(x, y, color, power = 1) {
    burst(x, y, color, 12 + Math.round(power * 9), 210 + power * 90)
    shockwaves.push({ x, y, r: 5, life: .45, max: .45, color })
    shake = Math.max(shake, 3 + power * 4); chroma = Math.max(chroma, power * .28); flash = Math.max(flash, power * .09)
    noise(.04 + power * .02, .018 + power * .009); tone(170 + Math.random() * 250, .06, 'square', .025, 1.8)
  }

  function circleCollision(ball, object, restitution = 1.06) {
    const dx = ball.x - object.x; const dy = ball.y - object.y; const distance = Math.hypot(dx, dy) || .001
    const minimum = ball.r + object.r
    if (distance >= minimum) return false
    const nx = dx / distance; const ny = dy / distance; const overlap = minimum - distance
    ball.x += nx * overlap; ball.y += ny * overlap
    const along = ball.vx * nx + ball.vy * ny
    if (along < 0) {
      ball.vx -= (1 + restitution) * along * nx
      ball.vy -= (1 + restitution) * along * ny
    }
    return true
  }

  function segmentCollision(ball, start, end, radius = 0, bounce = .88) {
    const dx = end[0] - start[0]; const dy = end[1] - start[1]; const length2 = dx * dx + dy * dy
    const t = clamp(((ball.x - start[0]) * dx + (ball.y - start[1]) * dy) / length2, 0, 1)
    const px = start[0] + dx * t; const py = start[1] + dy * t
    const ox = ball.x - px; const oy = ball.y - py; const distance = Math.hypot(ox, oy) || .001
    const minimum = ball.r + radius
    if (distance >= minimum) return false
    const nx = ox / distance; const ny = oy / distance
    ball.x += nx * (minimum - distance); ball.y += ny * (minimum - distance)
    const along = ball.vx * nx + ball.vy * ny
    if (along < 0) {
      ball.vx -= (1 + bounce) * along * nx
      ball.vy -= (1 + bounce) * along * ny
    }
    return true
  }

  function applyCoreGravity(ball, dt) {
    if (!ball.entered) return
    const dx = core.x - ball.x; const dy = core.y - ball.y
    const distance = Math.max(78, Math.hypot(dx, dy))
    const influence = 1 - clamp((distance - 78) / 390, 0, 1)
    if (influence <= 0) return
    const pull = (overdrive > 0 ? 1180 : 650) * influence * gravityPolarity
    const swirl = (overdrive > 0 ? 280 : 105) * influence
    ball.vx += (dx / distance * pull - dy / distance * swirl) * dt
    ball.vy += (dy / distance * pull + dx / distance * swirl) * dt
  }

  function updateMoonCollision(ball) {
    if (!ball.entered || moon.cooldown > 0) return
    const position = getMoonPosition()
    if (!circleCollision(ball, position, 1.34)) return
    moon.cooldown = .45
    gravityPolarity = -1
    polarityTimer = 4.5
    ball.vx *= 1.16; ball.vy -= 180
    impact(position.x, position.y, '#d8e6ff', 2.2)
    addScore(1200, 'GRAVITY REVERSED', position.x, position.y - 28, '#eef5ff')
    addHeat(16); updatePhase(); tone(360, .42, 'sine', .06, .18)
  }

  function updateRifts(ball) {
    if (!ball.entered || ball.riftCooldown > 0) return
    for (let index = 0; index < rifts.length; index++) {
      const source = rifts[index]
      if (Math.hypot(ball.x - source.x, ball.y - source.y) >= source.r + ball.r - 2) continue
      const target = rifts[1 - index]
      const speed = clamp(Math.hypot(ball.vx, ball.vy) * 1.08, 440, 1080)
      const exitAngle = Math.atan2(ball.vy, ball.vx) + (index === 0 ? -.92 : .92)
      ball.vx = Math.cos(exitAngle) * speed
      ball.vy = Math.sin(exitAngle) * speed - 110
      ball.x = target.x + Math.cos(exitAngle) * (target.r + ball.r + 8)
      ball.y = target.y + Math.sin(exitAngle) * (target.r + ball.r + 8)
      ball.riftCooldown = .75
      riftTransfers++
      burst(source.x, source.y, source.color, 44, 390); burst(target.x, target.y, target.color, 44, 390)
      shockwaves.push({ x: source.x, y: source.y, r: 8, life: .7, max: .7, color: source.color }, { x: target.x, y: target.y, r: 8, life: .7, max: .7, color: target.color })
      addScore(680 + riftTransfers * 40, 'LIGHTFOLD', target.x, target.y - 35, target.color)
      addHeat(8); shake = Math.max(shake, 13); chroma = 1; tone(index ? 210 : 780, .22, 'sine', .05, index ? 3.2 : .28)
      break
    }
  }

  function updatePhotonSail(ball) {
    if (!ball.entered || ball.sailCooldown > 0) return
    const sail = getPhotonSail()
    if (!segmentCollision(ball, sail.start, sail.end, photonSail.radius, 1.08)) return
    ball.sailCooldown = .28
    ball.vx += Math.cos(sail.angle) * 190
    ball.vy -= 310
    photonSail.cooldown = .18
    const hitX = (sail.start[0] + sail.end[0]) / 2; const hitY = (sail.start[1] + sail.end[1]) / 2
    impact(hitX, hitY, '#ffd75c', 1.35); addScore(340, 'PHOTON SAIL', hitX, hitY - 20, '#fff0a1'); addHeat(6)
  }

  function updateFlipper(ball, flipper) {
    const end = [flipper.x + Math.cos(flipper.angle) * flipper.length, flipper.y + Math.sin(flipper.angle) * flipper.length]
    if (!segmentCollision(ball, [flipper.x, flipper.y], end, 11, .92)) return
    const active = keys[flipper.side]
    if (active) {
      const direction = flipper.side === 'left' ? -1 : 1
      ball.vy -= 430; ball.vx += direction * 95
      impact(ball.x, ball.y, '#62f6ff', .7)
    }
  }

  function updateBall(ball, dt) {
    if (!ball.alive) return
    if (ball.lane) {
      ball.x = 584; ball.y = 904
      return
    }
    ball.riftCooldown = Math.max(0, ball.riftCooldown - dt)
    ball.sailCooldown = Math.max(0, ball.sailCooldown - dt)
    applyCoreGravity(ball, dt)
    const speed = Math.hypot(ball.vx, ball.vy)
    if (speed > 1220) { ball.vx *= 1220 / speed; ball.vy *= 1220 / speed }
    ball.vy += 670 * dt
    ball.x += ball.vx * dt; ball.y += ball.vy * dt
    ball.vx *= Math.pow(.9985, dt * 60); ball.vy *= Math.pow(.999, dt * 60)

    walls.forEach((wall) => segmentCollision(ball, wall[0], wall[1], 0, .9))
    flippers.forEach((flipper) => updateFlipper(ball, flipper))
    updatePhotonSail(ball)
    updateMoonCollision(ball)
    updateRifts(ball)

    if (!ball.entered && ball.y < 380) {
      ball.entered = true
      ball.vx = -Math.max(240, Math.abs(ball.vx) + 100)
      impact(ball.x, ball.y, '#ffbe55', 1.1)
      addScore(150, 'ORBIT ENTRY', ball.x - 25, ball.y, '#fff09a')
      addHeat(5)
    }

    for (const bumper of bumpers) {
      if (circleCollision(ball, bumper, 1.18) && bumper.cooldown <= 0) {
        bumper.cooldown = .11; ball.vx *= 1.05; ball.vy *= 1.05
        impact(bumper.x, bumper.y, bumper.color, 1.4); addScore(180, `${bumper.label} +${180 * multiplier}`, bumper.x, bumper.y, bumper.color); addHeat(7)
      }
    }

    if (circleCollision(ball, core, 1.22) && coreCooldown <= 0) {
      coreCooldown = .12; impact(core.x, core.y, overdrive > 0 ? '#fff6b0' : '#ff7a28', 2)
      addScore(overdrive > 0 ? 750 : 300, overdrive > 0 ? 'CORE CRITICAL' : 'CORE FEED', core.x, core.y - 20); addHeat(13)
    }

    for (const target of targets) {
      if (target.cooldown > 0 || target.on) continue
      if (Math.abs(ball.x - target.x) < 27 && Math.abs(ball.y - target.y) < 25) {
        target.on = true; target.cooldown = .15; ball.vx = Math.abs(ball.vx) + 160; ball.vy -= 110
        impact(target.x, target.y, '#ff3d70', 1); addScore(260, `${target.letter} LOCKED`, target.x + 25, target.y, '#ff8b60'); addHeat(9)
        if (targets.every((item) => item.on)) {
          targets.forEach((item) => { item.on = false; item.cooldown = .8 })
          addScore(2200, 'SOL MATRIX COMPLETE', 260, 520); addHeat(35); announce('SOL MATRIX COMPLETE')
        }
      }
    }

    for (const gate of gates) {
      if (!gate.on) continue
      if (Math.abs(ball.x - gate.x) < 24 && Math.abs(ball.y - gate.y) < 22) {
        gate.on = false; ball.vx -= 210; ball.vy -= 90
        impact(gate.x, gate.y, '#50efff', .9); addScore(220, 'PHOTON GATE', gate.x - 15, gate.y, '#70f8ff'); addHeat(5)
        if (gates.every((item) => !item.on)) {
          gates.forEach((item) => { item.on = true })
          addScore(1400, 'ORBIT SYNC', 495, 555); announce('ORBIT SYNC'); multiplier = clamp(multiplier + 1, 1, 8)
        }
      }
    }

    ball.trail.push({ x: ball.x, y: ball.y, life: 1 })
    if (ball.trail.length > (overdrive > 0 ? 34 : 20)) ball.trail.shift()
    if (ball.y > 1055 || ball.x < 35 || ball.x > 685) ball.alive = false
  }

  let coreCooldown = 0
  function update(dt) {
    if (mode !== 'play') return
    moon.angle += dt * (gravityPolarity < 0 ? -1.35 : .72)
    moon.cooldown = Math.max(0, moon.cooldown - dt)
    photonSail.cooldown = Math.max(0, photonSail.cooldown - dt)
    if (polarityTimer > 0) {
      polarityTimer = Math.max(0, polarityTimer - dt)
      if (polarityTimer === 0) {
        gravityPolarity = 1
        announce('GRAVITY RESTORED')
        tone(140, .26, 'sine', .04, 3)
      }
    }
    if (demoMode) {
      demoElapsed += dt
      const laneBall = balls.find((ball) => ball.alive && ball.lane)
      if (laneBall && time - laneBall.born > .65) launchBall(.85)
      const dangerBalls = balls.filter((ball) => ball.alive && !ball.lane && ball.y > 640)
      const pulse = Math.sin(time * 11) > -.15
      keys.left = pulse && dangerBalls.some((ball) => ball.x < 390)
      keys.right = pulse && dangerBalls.some((ball) => ball.x > 330)
      demoHeatClock += dt
      if (demoHeatClock >= .5 && overdrive <= 0) {
        demoHeatClock = 0
        addHeat(4)
      }
      if (demoElapsed >= 3 && demoElapsed < 3.5 && overdrive <= 0) activateOverdrive()
    }
    if (charging) charge = clamp(charge + dt * .72, 0, 1)
    coreCooldown = Math.max(0, coreCooldown - dt)
    bumpers.forEach((bumper) => { bumper.cooldown = Math.max(0, bumper.cooldown - dt) })
    targets.forEach((target) => { target.cooldown = Math.max(0, target.cooldown - dt) })
    flippers.forEach((flipper) => {
      const target = keys[flipper.side] ? flipper.active : flipper.rest
      flipper.angle += (target - flipper.angle) * Math.min(1, dt * 28)
    })

    const steps = 3
    for (let i = 0; i < steps; i++) balls.forEach((ball) => updateBall(ball, dt / steps))
    balls = balls.filter((ball) => ball.alive)
    if (balls.length === 0) drain()

    comboTimer -= dt
    if (comboTimer <= 0 && combo > 0) { combo = 0; multiplier = overdrive > 0 ? 3 : 1; updateHud() }
    if (overdrive > 0) {
      overdrive = Math.max(0, overdrive - dt)
      heat = overdrive > 0 ? 100 : 0
      if (overdrive === 0) { announce('OVERDRIVE COOLDOWN'); multiplier = 1; combo = 0 }
      updateHud()
    } else if (heat > 0) {
      heat = Math.max(0, heat - dt * 1.25)
    }

    updatePhase()

    updateEffects(dt)
  }

  function drain() {
    lives--; updateHud(); tone(120, .35, 'sawtooth', .06, .25)
    if (lives <= 0) {
      mode = 'over'; ui.final.textContent = `FINAL ENERGY ${String(score).padStart(7, '0')}`; ui.gameover.classList.add('visible'); ui.launch.classList.remove('visible'); announce('CORE OFFLINE')
      if (demoMode) demoRestartAt = time + 2.2
      return
    }
    announce('BALL LOST'); resetRound()
  }

  function updateEffects(dt) {
    particles.forEach((particle) => {
      particle.x += particle.vx * dt; particle.y += particle.vy * dt; particle.vx *= .98; particle.vy = particle.vy * .98 + 180 * dt; particle.life -= dt
    })
    particles = particles.filter((particle) => particle.life > 0)
    shockwaves.forEach((wave) => { wave.r += 300 * dt; wave.life -= dt })
    shockwaves = shockwaves.filter((wave) => wave.life > 0)
    popups.forEach((popup) => { popup.y -= 45 * dt; popup.life -= dt })
    popups = popups.filter((popup) => popup.life > 0)
    sparks.forEach((spark) => { spark.life -= dt })
    sparks = sparks.filter((spark) => spark.life > 0)
    shake = Math.max(0, shake - dt * 42); chroma = Math.max(0, chroma - dt * 2.8); flash = Math.max(0, flash - dt * 2.5)
    ui.flash.style.opacity = String(flash)
  }

  function path(points) {
    ctx.beginPath(); ctx.moveTo(points[0][0], points[0][1])
    for (let i = 1; i < points.length; i++) ctx.lineTo(points[i][0], points[i][1])
  }

  function neonLine(points, color, width = 3, blur = 16) {
    ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = color; ctx.lineWidth = width; ctx.shadowColor = color; ctx.shadowBlur = blur
    path(points); ctx.stroke(); ctx.restore()
  }

  function drawBackground() {
    const gradient = ctx.createRadialGradient(360, 620, 20, 360, 620, 700)
    gradient.addColorStop(0, '#21051d'); gradient.addColorStop(.48, '#090615'); gradient.addColorStop(1, '#020108')
    ctx.fillStyle = gradient; ctx.fillRect(0, 0, W, H)
    for (const star of stars) {
      const flicker = .25 + .6 * Math.abs(Math.sin(time * (1 + star.z) + star.phase))
      ctx.globalAlpha = flicker; ctx.fillStyle = star.z > .7 ? '#ffc184' : '#5fdfff'
      ctx.fillRect(star.x, (star.y + time * 8 * star.z) % H, star.z * 1.8, star.z * 1.8)
    }
    ctx.globalAlpha = 1
  }

  function drawBoard() {
    for (let depth = 18; depth > 0; depth -= 3) {
      ctx.fillStyle = `rgba(${25 + depth * 2},${4 + depth / 2},${24 + depth},.9)`
      path(board.map(([x, y]) => [x, y + depth])); ctx.closePath(); ctx.fill()
    }
    const floor = ctx.createLinearGradient(0, 80, 0, 1020)
    floor.addColorStop(0, '#17102f'); floor.addColorStop(.48, '#250720'); floor.addColorStop(1, '#090b20')
    ctx.fillStyle = floor; path(board); ctx.closePath(); ctx.fill()
    ctx.save(); path(board); ctx.closePath(); ctx.clip()
    const horizon = 90
    ctx.globalCompositeOperation = 'screen'
    for (let y = 120; y < 1010; y += 55) {
      const fade = (y - horizon) / 950
      ctx.strokeStyle = `rgba(255,74,77,${.045 + fade * .07})`; ctx.lineWidth = 1
      ctx.beginPath(); ctx.moveTo(75, y); ctx.lineTo(645, y); ctx.stroke()
    }
    for (let x = -80; x < 800; x += 55) {
      ctx.strokeStyle = 'rgba(65,228,255,.075)'; ctx.beginPath(); ctx.moveTo(360 + (x - 360) * .13, horizon); ctx.lineTo(x, 1030); ctx.stroke()
    }
    const aura = ctx.createRadialGradient(360, 465, 10, 360, 465, 270)
    aura.addColorStop(0, overdrive > 0 ? 'rgba(255,240,120,.34)' : 'rgba(255,76,28,.22)'); aura.addColorStop(1, 'transparent')
    ctx.fillStyle = aura; ctx.fillRect(80, 150, 560, 620)
    ctx.restore()
    neonLine(board.concat([board[0]]), '#ff542e', 4, 20)
    neonLine([[104,142],[78,878],[204,1012]], '#ff2f6c', 3, 18)
    neonLine([[616,142],[642,878],[516,1012]], '#42eaff', 3, 18)
    neonLine(launchGuide, '#ff9b43', 2, 11)
  }

  function drawSpaceWeather() {
    ctx.save(); path(board); ctx.closePath(); ctx.clip(); ctx.globalCompositeOperation = 'screen'
    const field = ctx.createRadialGradient(core.x, core.y, 60, core.x, core.y, 430)
    field.addColorStop(0, overdrive > 0 ? 'rgba(255,242,126,.2)' : 'rgba(255,77,28,.12)')
    field.addColorStop(.52, gravityPolarity < 0 ? 'rgba(82,244,255,.1)' : 'rgba(112,22,110,.055)')
    field.addColorStop(1, 'transparent')
    ctx.fillStyle = field; ctx.fillRect(55, 80, 610, 930)

    ctx.lineWidth = 1.3
    for (let ring = 0; ring < 7; ring++) {
      const radius = 92 + ring * 41 + Math.sin(time * 1.7 + ring) * 5
      ctx.strokeStyle = ring % 2 ? 'rgba(65,239,255,.14)' : 'rgba(255,78,55,.16)'
      ctx.setLineDash([3 + ring, 10 + ring * 2]); ctx.lineDashOffset = time * (gravityPolarity < 0 ? 42 : -28) * (ring % 2 ? 1 : -1)
      ctx.beginPath(); ctx.ellipse(core.x, core.y, radius, radius * .58, -.18 + ring * .09, 0, Math.PI * 2); ctx.stroke()
    }
    ctx.setLineDash([])

    const moonPosition = getMoonPosition()
    const shadowAngle = Math.atan2(moonPosition.y - core.y, moonPosition.x - core.x)
    ctx.translate(moonPosition.x, moonPosition.y); ctx.rotate(shadowAngle)
    const shadow = ctx.createLinearGradient(0, 0, 280, 0)
    shadow.addColorStop(0, 'rgba(1,2,12,.72)'); shadow.addColorStop(1, 'transparent')
    ctx.fillStyle = shadow; ctx.beginPath(); ctx.moveTo(0, -moon.r * .72); ctx.lineTo(310, -92); ctx.lineTo(310, 92); ctx.lineTo(0, moon.r * .72); ctx.closePath(); ctx.fill()
    ctx.restore()

    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineWidth = 2
    ctx.strokeStyle = gravityPolarity < 0 ? 'rgba(87,247,255,.62)' : 'rgba(255,93,56,.42)'
    ctx.shadowColor = ctx.strokeStyle; ctx.shadowBlur = 14
    ctx.beginPath(); ctx.moveTo(112, 812); ctx.bezierCurveTo(245, 590 + Math.sin(time) * 35, 390, 850, 525, 622); ctx.stroke()
    ctx.restore()
  }

  function drawRifts() {
    rifts.forEach((rift, index) => {
      ctx.save(); ctx.translate(rift.x, rift.y); ctx.rotate(time * (index ? -.85 : 1.1)); ctx.globalCompositeOperation = 'lighter'
      for (let ring = 0; ring < 4; ring++) {
        ctx.strokeStyle = ring % 2 ? '#fff0ca' : rift.color
        ctx.globalAlpha = .82 - ring * .15; ctx.lineWidth = 2.5 - ring * .35; ctx.shadowColor = rift.color; ctx.shadowBlur = 18
        ctx.beginPath(); ctx.ellipse(0, 0, rift.r + ring * 7, rift.r * .44 + ring * 2.8, ring * .72 + Math.sin(time * 1.6 + ring) * .12, 0, Math.PI * 2); ctx.stroke()
      }
      ctx.fillStyle = '#02020d'; ctx.globalAlpha = .9; ctx.beginPath(); ctx.ellipse(0, 0, rift.r * .72, rift.r * .25, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore()
      ctx.save(); ctx.fillStyle = rift.color; ctx.shadowColor = rift.color; ctx.shadowBlur = 10; ctx.textAlign = 'center'; ctx.font = '800 8px Consolas'; ctx.fillText(rift.label, rift.x, rift.y + rift.r + 22); ctx.restore()
    })
  }

  function drawMoon() {
    const position = getMoonPosition()
    ctx.save(); ctx.translate(position.x, position.y); ctx.rotate(moon.angle * .6)
    ctx.shadowColor = gravityPolarity < 0 ? '#67f4ff' : '#b6c7ff'; ctx.shadowBlur = gravityPolarity < 0 ? 34 : 18
    const rock = ctx.createRadialGradient(-8, -9, 2, 0, 0, moon.r)
    rock.addColorStop(0, '#f7eddf'); rock.addColorStop(.28, '#9aa4b9'); rock.addColorStop(.72, '#34334d'); rock.addColorStop(1, '#0b0a18')
    ctx.fillStyle = rock; ctx.beginPath(); ctx.arc(0, 0, moon.r, 0, Math.PI * 2); ctx.fill()
    ctx.fillStyle = 'rgba(8,7,19,.5)'
    ;[[-8,-7,5],[7,-3,3],[-2,9,4]].forEach(([x, y, r]) => { ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill() })
    ctx.strokeStyle = gravityPolarity < 0 ? '#70f6ff' : '#dce7ff'; ctx.lineWidth = 1.5; ctx.stroke(); ctx.restore()
    ctx.save(); ctx.fillStyle = gravityPolarity < 0 ? '#73f7ff' : 'rgba(214,225,255,.72)'; ctx.textAlign = 'center'; ctx.font = '800 7px Consolas'; ctx.fillText('ECLIPSE MOON', position.x, position.y + 36); ctx.restore()
  }

  function drawPhotonSail() {
    const sail = getPhotonSail(); const glow = photonSail.cooldown > 0 ? '#ffffff' : '#ffe166'
    ctx.save(); ctx.lineCap = 'round'; ctx.shadowColor = glow; ctx.shadowBlur = photonSail.cooldown > 0 ? 34 : 18
    ctx.strokeStyle = 'rgba(63,20,56,.95)'; ctx.lineWidth = 23; path([sail.start, sail.end]); ctx.stroke()
    const gradient = ctx.createLinearGradient(sail.start[0], sail.start[1], sail.end[0], sail.end[1]); gradient.addColorStop(0, '#ff3e91'); gradient.addColorStop(.48, '#fff3a1'); gradient.addColorStop(1, '#49efff')
    ctx.strokeStyle = gradient; ctx.lineWidth = 6; ctx.stroke(); ctx.strokeStyle = '#fffbdc'; ctx.lineWidth = 1.5; ctx.stroke(); ctx.restore()
    ctx.save(); ctx.translate(sail.start[0], sail.start[1]); ctx.fillStyle = '#fff2a3'; ctx.shadowColor = '#ffbd3c'; ctx.shadowBlur = 15; ctx.beginPath(); ctx.arc(0, 0, 11, 0, Math.PI * 2); ctx.fill(); ctx.restore()
  }

  function drawCore() {
    ctx.save(); ctx.translate(360, 465)
    for (let ring = 0; ring < 3; ring++) {
      ctx.save(); ctx.rotate(time * (ring % 2 ? -.7 : .48) + ring)
      ctx.strokeStyle = ring === 1 ? '#46eaff' : '#ff4b35'; ctx.shadowColor = ctx.strokeStyle; ctx.shadowBlur = 15; ctx.lineWidth = 2
      ctx.beginPath(); ctx.ellipse(0, 0, 91 + ring * 18, 34 + ring * 12, ring * .75, 0, Math.PI * 2); ctx.stroke(); ctx.restore()
    }
    const pulse = 1 + Math.sin(time * (overdrive > 0 ? 15 : 5)) * .08
    ctx.scale(pulse, pulse)
    const sun = ctx.createRadialGradient(-18, -20, 4, 0, 0, 63)
    sun.addColorStop(0, '#fffde8'); sun.addColorStop(.18, '#ffe26b'); sun.addColorStop(.54, '#ff6928'); sun.addColorStop(.82, '#b70d47'); sun.addColorStop(1, '#2b082c')
    ctx.fillStyle = sun; ctx.shadowColor = overdrive > 0 ? '#fff07e' : '#ff3e24'; ctx.shadowBlur = overdrive > 0 ? 65 : 35
    ctx.beginPath(); ctx.arc(0, 0, 61, 0, Math.PI * 2); ctx.fill()
    ctx.globalAlpha = .72; ctx.strokeStyle = '#fff5b0'; ctx.lineWidth = 2
    for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.arc(0, 0, 19 + i * 9 + Math.sin(time * 4 + i) * 3, i, i + 2.7); ctx.stroke() }
    ctx.restore()
    ctx.save(); ctx.textAlign = 'center'; ctx.fillStyle = '#fff0c0'; ctx.shadowColor = '#ff572d'; ctx.shadowBlur = 10; ctx.font = '900 13px Consolas'; ctx.fillText(overdrive > 0 ? 'CRITICAL' : 'SOL CORE', 360, 470); ctx.restore()
  }

  function drawBumpers() {
    bumpers.forEach((bumper) => {
      ctx.save(); ctx.translate(bumper.x, bumper.y)
      const pulse = 1 + Math.sin(time * 5 + bumper.x) * .06
      ctx.scale(pulse, pulse); ctx.shadowColor = bumper.color; ctx.shadowBlur = 27
      const gradient = ctx.createRadialGradient(-12, -14, 3, 0, 0, bumper.r)
      gradient.addColorStop(0, '#fff'); gradient.addColorStop(.23, bumper.color); gradient.addColorStop(.72, '#4b1538'); gradient.addColorStop(1, '#120a24')
      ctx.fillStyle = gradient; ctx.beginPath(); ctx.arc(0, 0, bumper.r, 0, Math.PI * 2); ctx.fill()
      ctx.strokeStyle = bumper.color; ctx.lineWidth = 3; ctx.stroke()
      ctx.fillStyle = '#fff'; ctx.font = '800 8px Consolas'; ctx.textAlign = 'center'; ctx.fillText(bumper.label, 0, 3)
      ctx.restore()
    })
  }

  function drawTargets() {
    targets.forEach((target) => {
      ctx.save(); ctx.translate(target.x, target.y); ctx.transform(1, 0, -.16, 1, 0, 0)
      ctx.fillStyle = target.on ? '#ff9b40' : '#31132d'; ctx.strokeStyle = target.on ? '#fff1a0' : '#ff3f75'; ctx.lineWidth = 2
      ctx.shadowColor = '#ff436d'; ctx.shadowBlur = target.on ? 25 : 8; ctx.fillRect(-18, -22, 36, 44); ctx.strokeRect(-18, -22, 36, 44)
      ctx.fillStyle = target.on ? '#fff' : '#ff7492'; ctx.font = '900 21px Consolas'; ctx.textAlign = 'center'; ctx.fillText(target.letter, 0, 8); ctx.restore()
    })
    gates.forEach((gate) => {
      ctx.save(); ctx.translate(gate.x, gate.y); ctx.globalAlpha = gate.on ? 1 : .18
      ctx.strokeStyle = '#44efff'; ctx.fillStyle = '#10243e'; ctx.shadowColor = '#26e8ff'; ctx.shadowBlur = gate.on ? 17 : 0; ctx.lineWidth = 3
      ctx.beginPath(); ctx.moveTo(-15, -18); ctx.lineTo(13, -13); ctx.lineTo(16, 16); ctx.lineTo(-12, 20); ctx.closePath(); ctx.fill(); ctx.stroke()
      ctx.fillStyle = '#fff'; ctx.font = '700 8px Consolas'; ctx.textAlign = 'center'; ctx.fillText(String(gate.phase + 1), 1, 4); ctx.restore()
    })
  }

  function drawFlippers() {
    flippers.forEach((flipper) => {
      const endX = flipper.x + Math.cos(flipper.angle) * flipper.length; const endY = flipper.y + Math.sin(flipper.angle) * flipper.length
      ctx.save(); ctx.lineCap = 'round'; ctx.shadowColor = flipper.side === 'left' ? '#ff3f70' : '#3feeff'; ctx.shadowBlur = 25
      ctx.strokeStyle = '#351535'; ctx.lineWidth = 28; ctx.beginPath(); ctx.moveTo(flipper.x, flipper.y); ctx.lineTo(endX, endY); ctx.stroke()
      ctx.strokeStyle = flipper.side === 'left' ? '#ff5578' : '#55efff'; ctx.lineWidth = 5; ctx.stroke()
      ctx.strokeStyle = '#fff8d2'; ctx.lineWidth = 2; ctx.stroke(); ctx.restore()
    })
  }

  function drawBalls() {
    for (const ball of balls) {
      if (!ball.alive) continue
      ctx.save(); ctx.globalCompositeOperation = 'lighter'
      ball.trail.forEach((trail, index) => {
        const alpha = (index / ball.trail.length) * (overdrive > 0 ? .34 : .2)
        ctx.globalAlpha = alpha; ctx.fillStyle = ball.hue; ctx.beginPath(); ctx.arc(trail.x, trail.y, ball.r * index / ball.trail.length, 0, Math.PI * 2); ctx.fill()
      }); ctx.restore()
      ctx.save(); ctx.shadowColor = ball.hue; ctx.shadowBlur = overdrive > 0 ? 34 : 20
      const gradient = ctx.createRadialGradient(ball.x - 5, ball.y - 6, 1, ball.x, ball.y, ball.r)
      gradient.addColorStop(0, '#fff'); gradient.addColorStop(.25, '#fffbd2'); gradient.addColorStop(.6, ball.hue); gradient.addColorStop(1, '#251344')
      ctx.fillStyle = gradient; ctx.beginPath(); ctx.arc(ball.x, ball.y, ball.r, 0, Math.PI * 2); ctx.fill(); ctx.restore()
    }
  }

  function drawEffects() {
    ctx.save(); ctx.globalCompositeOperation = 'lighter'
    particles.forEach((particle) => {
      ctx.globalAlpha = clamp(particle.life / particle.max, 0, 1); ctx.fillStyle = particle.color; ctx.shadowColor = particle.color; ctx.shadowBlur = 9
      ctx.beginPath(); ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2); ctx.fill()
    })
    shockwaves.forEach((wave) => {
      ctx.globalAlpha = wave.life / wave.max; ctx.strokeStyle = wave.color; ctx.shadowColor = wave.color; ctx.shadowBlur = 18; ctx.lineWidth = 4
      ctx.beginPath(); ctx.arc(wave.x, wave.y, wave.r, 0, Math.PI * 2); ctx.stroke()
    }); ctx.restore()
    popups.forEach((popup) => {
      ctx.save(); ctx.globalAlpha = popup.life / popup.max; ctx.fillStyle = popup.color; ctx.shadowColor = popup.color; ctx.shadowBlur = 15; ctx.textAlign = 'center'; ctx.font = '900 16px Consolas'; ctx.fillText(popup.text, popup.x, popup.y); ctx.restore()
    })
  }

  function drawCharge() {
    if (!charging) return
    ctx.save(); ctx.fillStyle = 'rgba(28,5,25,.8)'; ctx.strokeStyle = '#ff8b3c'; ctx.lineWidth = 2; ctx.fillRect(568, 762, 31, 128); ctx.strokeRect(568, 762, 31, 128)
    const height = 124 * charge; const gradient = ctx.createLinearGradient(0, 890, 0, 762); gradient.addColorStop(0, '#ff214e'); gradient.addColorStop(1, '#fff19a')
    ctx.fillStyle = gradient; ctx.shadowColor = '#ff5c26'; ctx.shadowBlur = 16; ctx.fillRect(572, 886 - height, 23, height); ctx.restore()
  }

  function draw() {
    drawBackground()
    ctx.save()
    if (shake > 0) ctx.translate(random(-shake, shake), random(-shake, shake))
    if (chroma > .05) {
      ctx.save(); ctx.globalAlpha = chroma * .12; ctx.translate(-chroma * 7, 0); drawBoard(); ctx.restore()
      ctx.save(); ctx.globalAlpha = chroma * .09; ctx.translate(chroma * 7, 0); drawBoard(); ctx.restore()
    }
    drawBoard(); drawSpaceWeather(); drawRifts(); drawCore(); drawMoon(); drawBumpers(); drawTargets(); drawPhotonSail(); drawFlippers(); drawBalls(); drawEffects(); drawCharge()
    ctx.restore()
  }

  function frame(timestamp) {
    raf = requestAnimationFrame(frame)
    const dt = Math.min(.033, (timestamp - last || 0) / 1000)
    last = timestamp; time += dt
    if (demoMode && mode === 'over' && demoRestartAt > 0 && time >= demoRestartAt) startGame(true)
    update(dt); draw()
  }

  function togglePause(forceResume = false) {
    if (mode === 'play') { mode = 'paused'; ui.pause.classList.add('visible'); keys.left = keys.right = false }
    else if (mode === 'paused' || forceResume) { mode = 'play'; ui.pause.classList.remove('visible'); last = performance.now() }
  }

  function keyInput(event, pressed) {
    if (event.repeat) return
    if ((event.key === 'p' || event.key === 'P' || event.key === 'Escape') && pressed && (mode === 'play' || mode === 'paused')) { togglePause(); return }
    if (mode === 'title' && pressed && event.key === 'Enter') { startGame(); return }
    if (mode === 'over' && pressed && event.key === 'Enter') { startGame(); return }
    if (mode !== 'play') return
    if (['ArrowLeft','a','A'].includes(event.key)) { keys.left = pressed; event.preventDefault() }
    if (['ArrowRight','d','D','l','L'].includes(event.key)) { keys.right = pressed; event.preventDefault() }
    if ([' ','ArrowDown'].includes(event.key)) {
      const hasLaneBall = balls.some((ball) => ball.lane)
      if (hasLaneBall) { if (pressed) { charging = true; charge = 0 } else launchBall() }
      event.preventDefault()
    }
  }

  addEventListener('keydown', (event) => keyInput(event, true))
  addEventListener('keyup', (event) => keyInput(event, false))
  addEventListener('blur', () => { keys.left = keys.right = false; charging = false })
  document.addEventListener('visibilitychange', () => { if (document.hidden && mode === 'play') togglePause() })
  addEventListener('resize', resize)

  canvas.addEventListener('pointerdown', (event) => {
    if (mode !== 'play') return
    const side = event.clientX < innerWidth / 2 ? 'left' : 'right'
    keys[side] = true; pointers.set(event.pointerId, side); canvas.setPointerCapture(event.pointerId)
  })
  function releasePointer(event) {
    const side = pointers.get(event.pointerId)
    if (!side) return
    pointers.delete(event.pointerId)
    if (![...pointers.values()].includes(side)) keys[side] = false
  }
  canvas.addEventListener('pointerup', releasePointer)
  canvas.addEventListener('pointercancel', releasePointer)
  ui.launch.addEventListener('pointerdown', (event) => {
    event.preventDefault(); event.stopPropagation(); ensureAudio(); charging = true; charge = 0; launchPointerId = event.pointerId
    ui.launch.setPointerCapture(event.pointerId)
  })
  const finishLaunchPointer = (event) => {
    if (launchPointerId !== event.pointerId) return
    event.preventDefault(); event.stopPropagation(); launchPointerId = null; launchBall()
  }
  ui.launch.addEventListener('pointerup', finishLaunchPointer)
  ui.launch.addEventListener('pointercancel', (event) => {
    if (launchPointerId !== event.pointerId) return
    launchPointerId = null; charging = false; charge = 0
  })
  ui.launch.addEventListener('click', () => launchBall(.45))
  el('#start').addEventListener('click', () => startGame(false))
  el('#demo-start').addEventListener('click', () => startGame(true))
  el('#restart').addEventListener('click', () => startGame(false))
  el('#resume').addEventListener('click', () => togglePause(true))
  ui.sound.addEventListener('click', () => {
    muted = !muted; ui.sound.textContent = muted ? 'SOUND OFF' : 'SOUND ON'
    if (!muted) tone(420, .08, 'square', .025, 1.4)
  })
  window.XPinballSol = Object.freeze({
    getState: () => ({
      mode, demoMode, demoElapsed, score, highScore, lives, heat, multiplier, overdrive, charging, charge, phase, gravityPolarity, polarityTimer, riftTransfers,
      moon: getMoonPosition(), photonSail: getPhotonSail(),
      balls: balls.map((ball) => ({ x: Math.round(ball.x), y: Math.round(ball.y), vx: Math.round(ball.vx), vy: Math.round(ball.vy), lane: ball.lane, entered: ball.entered, alive: ball.alive }))
    }),
    startDemo: () => startGame(true),
    startGame: () => startGame(false),
    launch: () => launchBall(1),
    triggerEclipse: () => { gravityPolarity = -1; polarityTimer = 4.5; updatePhase() },
    triggerBloom: () => activateOverdrive(),
    probeRift: () => {
      if (mode !== 'play') startGame(false)
      const ball = balls.find((item) => item.alive) || makeBall()
      if (!balls.includes(ball)) balls.push(ball)
      Object.assign(ball, { x: rifts[0].x, y: rifts[0].y, vx: 430, vy: -180, lane: false, entered: true, riftCooldown: 0 })
      updateRifts(ball)
    },
    probeMoon: () => {
      if (mode !== 'play') startGame(false)
      const ball = balls.find((item) => item.alive) || makeBall()
      if (!balls.includes(ball)) balls.push(ball)
      const position = getMoonPosition()
      Object.assign(ball, { x: position.x, y: position.y, vx: 220, vy: 180, lane: false, entered: true })
      moon.cooldown = 0; updateMoonCollision(ball)
    }
  })
  addEventListener('pagehide', () => { cancelAnimationFrame(raf); clearTimeout(announcementTimer); if (audio) audio.close() }, { once: true })

  resize(); initStars(); updateHud(); raf = requestAnimationFrame(frame)
})()
