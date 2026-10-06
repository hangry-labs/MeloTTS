import { AudioEditor } from './audio-editor.js'
import { browserLanguage, initializeI18n, t } from './i18n.js'

await initializeI18n()

const $ = (selector, root = document) => root.querySelector(selector)
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)]
const UI_SESSION_KEY = 'melotts-ui-state-v1'
const GPU_SESSION_KEY = 'melotts-gpu-history-v1'
const GPU_HISTORY_RETENTION_MS = 10 * 60 * 1000
const GPU_POLL_INTERVAL_MS = 1000
const GPU_METRICS = [
  { key: 'utilization', label: t('gpu.metric.gpu'), color: '#ff7a1a' },
  { key: 'memory_utilization', label: t('gpu.metric.memoryActivity'), color: '#c586c0' },
  { key: 'memory_used', label: t('gpu.metric.vram'), color: '#72a7ff' },
  { key: 'temperature', label: t('gpu.metric.temperature'), color: '#ef6b73' },
  { key: 'power', label: t('gpu.metric.power'), color: '#f2c94c' },
  { key: 'fan_speed', label: t('gpu.metric.fan'), color: '#55c58a' },
  { key: 'graphics_clock', label: t('gpu.metric.graphicsClock'), color: '#9cdcfe' },
  { key: 'memory_clock', label: t('gpu.metric.memoryClock'), color: '#ce9178' },
]

const state = {
  activeTab: 'generate',
  headerCollapsed: false,
  defaults: null,
  status: null,
  voices: [],
  streamAbort: null,
  streamPlayback: null,
  gpuHistory: new Map(),
  gpuStats: [],
  gpuWindowMs: 60 * 1000,
  gpuTimer: null,
  gpuRefreshActive: false,
  gpuHovering: false,
  headerAnimation: null,
}

const generateOutput = new AudioEditor($('#generate-output'), { label: t('editor.generatedAudio') })
const streamOutput = new AudioEditor($('#stream-output'), { label: t('editor.streamedAudio') })

function setStatus(message, tone = 'neutral') {
  const status = $('#global-status')
  status.textContent = message
  status.dataset.tone = tone
}

function showToast(message, tone = 'error') {
  const toast = $('#toast')
  toast.textContent = message
  toast.dataset.tone = tone
  toast.hidden = false
  clearTimeout(showToast.timer)
  showToast.timer = setTimeout(() => { toast.hidden = true }, 5000)
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error)
}

async function responseError(response) {
  const text = await response.text()
  try {
    const payload = JSON.parse(text)
    return payload.detail || payload.error?.message || text
  } catch {
    return text || `HTTP ${response.status}`
  }
}

async function fetchJson(path, options) {
  const response = await fetch(path, options)
  if (!response.ok) throw new Error(await responseError(response))
  return response.json()
}

function readSessionJson(key) {
  try { return JSON.parse(sessionStorage.getItem(key) || 'null') } catch { return null }
}

function persistUiSession() {
  try {
    sessionStorage.setItem(UI_SESSION_KEY, JSON.stringify({
      activeTab: state.activeTab,
      headerCollapsed: state.headerCollapsed,
      gpuWindowMs: state.gpuWindowMs,
    }))
  } catch {}
}

function persistGpuSession() {
  try {
    sessionStorage.setItem(GPU_SESSION_KEY, JSON.stringify({
      savedAt: Date.now(),
      stats: state.gpuStats,
      history: Object.fromEntries(state.gpuHistory),
    }))
  } catch {}
}

function restoreSessionState() {
  const ui = readSessionJson(UI_SESSION_KEY)
  if (['generate', 'stream', 'api', 'system'].includes(ui?.activeTab)) state.activeTab = ui.activeTab
  if (typeof ui?.headerCollapsed === 'boolean') state.headerCollapsed = ui.headerCollapsed
  if ([60 * 1000, 10 * 60 * 1000].includes(ui?.gpuWindowMs)) state.gpuWindowMs = ui.gpuWindowMs

  const cached = readSessionJson(GPU_SESSION_KEY)
  const cutoff = Date.now() - GPU_HISTORY_RETENTION_MS
  if (!cached || !Number.isFinite(cached.savedAt) || cached.savedAt < cutoff) return
  if (Array.isArray(cached.stats)) state.gpuStats = cached.stats
  Object.entries(cached.history || {}).forEach(([index, samples]) => {
    const recent = Array.isArray(samples)
      ? samples.filter((sample) => Number.isFinite(sample?.timestamp) && sample.timestamp >= cutoff)
      : []
    if (recent.length) state.gpuHistory.set(Number(index), recent)
  })
}

function setHeroCollapsed(collapsed, persist = true, animate = true) {
  const hero = $('#brand-hero')
  const toggle = $('#hero-toggle')
  state.headerAnimation?.cancel()
  const startHeight = hero.getBoundingClientRect().height
  state.headerCollapsed = collapsed
  document.documentElement.dataset.headerCollapsed = String(collapsed)
  hero.dataset.collapsed = String(collapsed)
  toggle.setAttribute('aria-expanded', String(!collapsed))
  toggle.setAttribute('aria-label', collapsed ? 'Expand header' : 'Collapse header')
  toggle.title = toggle.getAttribute('aria-label')
  toggle.querySelector('i').className = collapsed ? 'icon-chevron-down' : 'icon-chevron-up'
  const endHeight = hero.getBoundingClientRect().height
  if (animate && !matchMedia('(prefers-reduced-motion: reduce)').matches && Math.abs(startHeight - endHeight) > 1) {
    hero.classList.add('is-rolling')
    const animation = hero.animate(
      [{ height: `${startHeight}px` }, { height: `${endHeight}px` }],
      { duration: 320, easing: 'cubic-bezier(0.22, 1, 0.36, 1)', fill: 'both' },
    )
    state.headerAnimation = animation
    animation.finished.catch(() => {}).finally(() => {
      if (state.headerAnimation !== animation) return
      hero.classList.remove('is-rolling')
      state.headerAnimation = null
      animation.cancel()
    })
  }
  if (persist) persistUiSession()
}

$('#hero-toggle').addEventListener('click', () => setHeroCollapsed(!state.headerCollapsed))

function activateTab(name) {
  state.activeTab = name
  persistUiSession()
  $$('.tab-button').forEach((button) => {
    const active = button.dataset.tab === name
    button.classList.toggle('active', active)
    button.setAttribute('aria-selected', String(active))
  })
  $$('.tab-panel').forEach((panel) => { panel.hidden = panel.dataset.panel !== name })
  const synthesisView = name === 'generate' || name === 'stream'
  $('#composer').hidden = !synthesisView
  $('.settings-panel').hidden = !synthesisView
  $('.workspace').dataset.view = name
  if (name === 'api') refreshApiStatus()
  if (name === 'system') {
    refreshSystem()
    startGpuMonitor()
  } else {
    state.gpuHovering = false
    stopGpuMonitor()
  }
}

$$('.tab-button').forEach((button) => button.addEventListener('click', () => activateTab(button.dataset.tab)))

function clampNumericInput(input) {
  const value = Number(input.value)
  if (!Number.isFinite(value)) return null
  return Math.min(Number(input.max), Math.max(Number(input.min), value))
}

$$('input[type="range"][data-value-input]').forEach((slider) => {
  const valueInput = $(`#${slider.dataset.valueInput}`)
  slider.addEventListener('input', () => { valueInput.value = slider.value })
})

$$('input[type="number"][data-range-input]').forEach((valueInput) => {
  const slider = $(`#${valueInput.dataset.rangeInput}`)
  valueInput.addEventListener('input', () => {
    const value = clampNumericInput(valueInput)
    if (value !== null) slider.value = String(value)
  })
  valueInput.addEventListener('change', () => {
    const value = clampNumericInput(valueInput)
    valueInput.value = String(value ?? slider.value)
    slider.value = valueInput.value
  })
})

function setControlValue(name, value) {
  const input = $(`#${name}`)
  input.value = String(value)
  $(`#${input.dataset.rangeInput}`).value = String(value)
}

function setSelectOptions(select, entries, selectedValue) {
  select.replaceChildren(...entries.map(({ value, label, disabled = false }) => {
    const option = document.createElement('option')
    option.value = value
    option.textContent = label
    option.disabled = disabled
    return option
  }))
  if (entries.some((entry) => entry.value === selectedValue && !entry.disabled)) select.value = selectedValue
}

function selectedPreset() {
  return state.defaults?.presets?.[$('#preset').value] || state.defaults?.presets?.Balanced
}

function applyPreset(name = $('#preset').value) {
  const preset = state.defaults?.presets?.[name]
  if (!preset) return
  setControlValue('speed', preset.speed)
  setControlValue('sdp-ratio', preset.sdp_ratio)
  setControlValue('noise-scale', preset.noise_scale)
  setControlValue('noise-scale-w', preset.noise_scale_w)
}

function applyAudioControlDefaults() {
  const controls = state.defaults?.audio_controls || {
    pitch_semitones: 0,
    tempo: 1,
    volume: 1,
    normalize: false,
  }
  setControlValue('pitch', controls.pitch_semitones)
  setControlValue('tempo', controls.tempo)
  setControlValue('volume', controls.volume)
  $('#normalize').checked = controls.normalize
  updateNormalizationState()
}

function updateNormalizationState() {
  const normalized = $('#normalize').checked
  $('#volume').disabled = normalized
  $('#volume-slider').disabled = normalized
  $('#volume-control').classList.toggle('setting-disabled', normalized)
}

$('#normalize').addEventListener('change', updateNormalizationState)

$('#preset').addEventListener('change', () => applyPreset())
$('#reset-voice-controls').addEventListener('click', () => {
  $('#preset').value = Object.hasOwn(state.defaults?.presets || {}, 'Balanced') ? 'Balanced' : $('#preset').options[0]?.value
  applyPreset()
  applyAudioControlDefaults()
  setStatus('Voice controls reset', 'success')
})

function updateTextMetrics() {
  const text = $('#text-input').value
  const words = text.trim() ? text.trim().split(/\s+/u).length : 0
  $('#text-metrics').textContent = `${text.length} characters / ${words} words`
}

$('#text-input').addEventListener('input', updateTextMetrics)
$('#normalize-button').addEventListener('click', () => {
  $('#text-input').value = $('#text-input').value.replace(/\s+/gu, ' ').trim()
  updateTextMetrics()
})

function inventoryForLanguage(language) {
  return state.voices.find((entry) => entry.language === language)
}

function refreshVoiceOptions(preferred) {
  const inventory = inventoryForLanguage($('#language').value)
  const speakers = inventory?.speakers || []
  setSelectOptions($('#voice'), speakers.map((speaker) => ({ value: speaker, label: speaker })), preferred || speakers[0])
}

$('#language').addEventListener('change', () => {
  refreshVoiceOptions()
  const text = state.defaults?.texts?.[$('#language').value]
  if (text) {
    $('#text-input').value = text
    updateTextMetrics()
  }
})

$('#sample-button').addEventListener('click', () => {
  const language = $('#language').value
  const quotes = state.defaults?.quotes?.[language] || []
  if (!quotes.length) return
  $('#text-input').value = quotes[Math.floor(Math.random() * quotes.length)]
  updateTextMetrics()
  setStatus('Random quote ready', 'success')
})

function requestPayload(outputFormat = $('#output-format').value) {
  return {
    text: $('#text-input').value,
    language: $('#language').value,
    speaker_id: $('#voice').value,
    speed: Number($('#speed').value),
    sdp_ratio: Number($('#sdp-ratio').value),
    noise_scale: Number($('#noise-scale').value),
    noise_scale_w: Number($('#noise-scale-w').value),
    pitch_semitones: Number($('#pitch').value),
    tempo: Number($('#tempo').value),
    volume: $('#normalize').checked ? 1 : Number($('#volume').value),
    normalize: $('#normalize').checked,
    format: outputFormat,
  }
}

function responseFilename(response, fallback) {
  const disposition = response.headers.get('content-disposition') || ''
  const match = disposition.match(/filename="?([^";]+)"?/i)
  return match?.[1] || fallback
}

$('#generate-button').addEventListener('click', async () => {
  const payload = requestPayload()
  if (!payload.text.trim()) return showToast('Enter text before generating audio.')
  const button = $('#generate-button')
  button.disabled = true
  setStatus('Generating audio')
  const started = performance.now()
  try {
    const response = await fetch('/tts/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!response.ok) throw new Error(await responseError(response))
    const blob = await response.blob()
    await generateOutput.load(blob, responseFilename(response, `melotts_${payload.language}.${payload.format}`))
    await generateOutput.play().catch(() => {})
    setStatus(`Generated in ${((performance.now() - started) / 1000).toFixed(2)}s`, 'success')
  } catch (error) {
    setStatus('Generation failed', 'error')
    showToast(errorMessage(error))
  } finally {
    button.disabled = false
  }
})

function setStreaming(active) {
  $('#stream-start').disabled = active
  $('#stream-stop').disabled = !active
  $('#stream-progress').hidden = !active
}

class IncrementalAudioPlayback {
  static async create() {
    if (!window.MediaSource || !MediaSource.isTypeSupported('audio/mpeg')) return null
    const mediaSource = new MediaSource()
    const objectUrl = URL.createObjectURL(mediaSource)
    const audio = new Audio(objectUrl)
    await new Promise((resolve, reject) => {
      mediaSource.addEventListener('sourceopen', resolve, { once: true })
      mediaSource.addEventListener('error', reject, { once: true })
    })
    try {
      return new IncrementalAudioPlayback(mediaSource, audio, objectUrl)
    } catch {
      URL.revokeObjectURL(objectUrl)
      return null
    }
  }

  constructor(mediaSource, audio, objectUrl) {
    this.mediaSource = mediaSource
    this.audio = audio
    this.objectUrl = objectUrl
    this.sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg')
    this.queue = Promise.resolve()
    this.started = false
  }

  append(chunk) {
    const bytes = chunk.buffer.slice(chunk.byteOffset, chunk.byteOffset + chunk.byteLength)
    this.queue = this.queue.then(() => new Promise((resolve, reject) => {
      const done = () => {
        this.sourceBuffer.removeEventListener('error', failed)
        resolve()
      }
      const failed = () => {
        this.sourceBuffer.removeEventListener('updateend', done)
        reject(new Error(t('errors.streamBuffer', {}, 'Browser could not buffer streamed MP3 audio.')))
      }
      this.sourceBuffer.addEventListener('updateend', done, { once: true })
      this.sourceBuffer.addEventListener('error', failed, { once: true })
      this.sourceBuffer.appendBuffer(bytes)
    })).then(() => {
      if (!this.started) {
        this.started = true
        this.audio.play().catch(() => {})
      }
    })
    return this.queue
  }

  async finish() {
    await this.queue
    if (this.mediaSource.readyState === 'open') this.mediaSource.endOfStream()
  }

  currentTime() {
    return this.audio.currentTime || 0
  }

  stop() {
    this.audio.pause()
    if (this.mediaSource.readyState === 'open') {
      try { this.mediaSource.endOfStream() } catch {}
    }
    URL.revokeObjectURL(this.objectUrl)
  }
}

async function loadStreamResult(chunks, language, autoplay) {
  if (!chunks.length) return
  const blob = new Blob(chunks, { type: 'audio/mpeg' })
  await streamOutput.load(blob, `melotts_${language}_stream.mp3`)
  if (autoplay) await streamOutput.play().catch(() => {})
}

$('#stream-start').addEventListener('click', async () => {
  const payload = { ...requestPayload('mp3'), stream_format: 'mp3' }
  if (!payload.text.trim()) return showToast('Enter text before streaming audio.')
  const controller = new AbortController()
  state.streamAbort = controller
  streamOutput.clear()
  setStreaming(true)
  setStatus('Starting stream')
  const chunks = []
  const started = performance.now()
  let playback = null
  try {
    playback = await IncrementalAudioPlayback.create()
    state.streamPlayback = playback
    const response = await fetch('/tts/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })
    if (!response.ok) throw new Error(await responseError(response))
    if (!response.body) throw new Error('Streaming response body is unavailable in this browser.')
    const reader = response.body.getReader()
    let totalBytes = 0
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      chunks.push(value)
      totalBytes += value.byteLength
      if (playback) playback.append(value).catch((error) => showToast(errorMessage(error)))
      setStatus(`Streaming ${(totalBytes / 1024).toFixed(0)} KiB`)
    }
    let resumeAt = 0
    if (playback) {
      await playback.finish()
      resumeAt = playback.currentTime()
      playback.stop()
      playback = null
      state.streamPlayback = null
    }
    await loadStreamResult(chunks, payload.language, !resumeAt)
    if (resumeAt) await streamOutput.playFrom(resumeAt).catch(() => {})
    setStatus(`Stream complete in ${((performance.now() - started) / 1000).toFixed(2)}s`, 'success')
  } catch (error) {
    if (error.name === 'AbortError') {
      await loadStreamResult(chunks, payload.language, false)
      setStatus('Stream stopped', 'success')
    } else {
      setStatus('Stream failed', 'error')
      showToast(errorMessage(error))
    }
  } finally {
    playback?.stop()
    state.streamAbort = null
    state.streamPlayback = null
    setStreaming(false)
  }
})

$('#stream-stop').addEventListener('click', () => {
  setStatus('Stopping stream')
  state.streamAbort?.abort()
  state.streamPlayback?.stop()
})

function jsonPrimitive(value) {
  const span = document.createElement('span')
  if (value === null) {
    span.className = 'json-null'
    span.textContent = 'null'
  } else if (typeof value === 'string') {
    span.className = 'json-string'
    span.textContent = JSON.stringify(value)
  } else if (typeof value === 'number') {
    span.className = 'json-number'
    span.textContent = String(value)
  } else {
    span.className = 'json-boolean'
    span.textContent = String(value)
  }
  return span
}

function jsonKey(key) {
  const span = document.createElement('span')
  span.className = 'json-key'
  span.textContent = `${typeof key === 'number' ? key : JSON.stringify(String(key))}: `
  return span
}

function createJsonNode(value, key, depth, expandDepth) {
  if (value === null || typeof value !== 'object') {
    const row = document.createElement('div')
    row.className = 'json-row'
    if (key !== null) row.append(jsonKey(key))
    row.append(jsonPrimitive(value))
    return row
  }
  const array = Array.isArray(value)
  const entries = Object.entries(value)
  const details = document.createElement('details')
  details.className = 'json-branch'
  details.open = depth < expandDepth
  const summary = document.createElement('summary')
  if (key !== null) summary.append(jsonKey(key))
  const opening = document.createElement('span')
  opening.className = 'json-bracket'
  opening.textContent = array ? '[' : '{'
  const count = document.createElement('span')
  count.className = 'json-count'
  count.textContent = `${entries.length} ${entries.length === 1 ? 'item' : 'items'}`
  const closing = document.createElement('span')
  closing.className = 'json-bracket json-collapsed-close'
  closing.textContent = array ? ']' : '}'
  summary.append(opening, count, closing)
  const children = document.createElement('div')
  children.className = 'json-children'
  entries.forEach(([entryKey, entryValue]) => children.append(createJsonNode(entryValue, array ? Number(entryKey) : entryKey, depth + 1, expandDepth)))
  const closeRow = document.createElement('div')
  closeRow.className = 'json-close'
  closeRow.textContent = array ? ']' : '}'
  details.append(summary, children, closeRow)
  return details
}

function renderJsonTree(container, value, expandDepth = 1) {
  container.replaceChildren(createJsonNode(value, null, 0, expandDepth))
}

async function refreshApiStatus() {
  $('#api-output').textContent = 'Loading...'
  const paths = ['/tts/ping', '/tts/status', '/tts/defaults', '/tts/formats', '/tts/stream-formats', '/tts/languages', '/tts/voices', '/v1/models', '/v1/audio/voices']
  const values = await Promise.all(paths.map(async (path) => {
    try { return [path, await fetchJson(path)] } catch (error) { return [path, { error: errorMessage(error) }] }
  }))
  renderJsonTree($('#api-output'), { 'Melo TTS API': Object.fromEntries(values) })
}

$('#api-refresh').addEventListener('click', refreshApiStatus)

function modelActionButton(label, action, language, primary = false) {
  const button = document.createElement('button')
  button.className = primary ? 'primary-button model-action' : 'secondary-button model-action'
  button.type = 'button'
  button.textContent = label
  button.addEventListener('click', async () => {
    button.disabled = true
    try {
      await fetchJson(`/tts/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language }),
      })
      await refreshSystem()
      await loadWorkspace(false)
      showToast(action === 'load' ? `${language} loaded` : `Kept ${language} loaded`, 'success')
    } catch (error) {
      showToast(errorMessage(error))
    } finally {
      button.disabled = false
    }
  })
  return button
}

function renderModelResidency(status) {
  const loaded = new Set(status.loaded_languages || [])
  const container = $('#model-settings-groups')
  container.replaceChildren()
  ;(status.configured_languages || []).forEach((language) => {
    const section = document.createElement('section')
    section.className = 'model-setting model-residency-row'
    const copy = document.createElement('span')
    copy.className = 'model-setting-copy'
    const name = document.createElement('strong')
    name.textContent = language
    const residency = document.createElement('span')
    residency.textContent = loaded.has(language) ? 'Loaded in memory' : 'Configured, not loaded'
    copy.append(name, residency)
    const actions = document.createElement('div')
    actions.className = 'model-residency-actions'
    if (!loaded.has(language)) actions.append(modelActionButton('Load', 'load', language, true))
    if (loaded.size > 1 && loaded.has(language)) actions.append(modelActionButton('Keep only', 'purge', language))
    section.append(copy, actions)
    container.append(section)
  })
}

async function refreshSystem() {
  try {
    const [status, voices] = await Promise.all([fetchJson('/tts/status'), fetchJson('/tts/voices')])
    state.status = status
    renderModelResidency(status)
    renderJsonTree($('#runtime-output'), status, 1)
    renderJsonTree($('#voices-output'), voices, 1)
  } catch (error) {
    showToast(errorMessage(error))
  }
}

function element(tag, className, text) {
  const node = document.createElement(tag)
  if (className) node.className = className
  if (text !== undefined) node.textContent = text
  return node
}

function mergeGpuHistory(historyPayload) {
  const cutoff = Date.now() - GPU_HISTORY_RETENTION_MS
  Object.entries(historyPayload || {}).forEach(([index, incoming]) => {
    if (!Array.isArray(incoming)) return
    const samplesByTimestamp = new Map()
    ;[...(state.gpuHistory.get(Number(index)) || []), ...incoming].forEach((sample) => {
      if (Number.isFinite(sample?.timestamp) && sample.timestamp >= cutoff) {
        samplesByTimestamp.set(sample.timestamp, sample)
      }
    })
    const merged = [...samplesByTimestamp.values()].sort((left, right) => left.timestamp - right.timestamp)
    if (merged.length) state.gpuHistory.set(Number(index), merged)
  })
  state.gpuHistory.forEach((samples, index) => {
    const recent = samples.filter((sample) => sample.timestamp >= cutoff)
    if (recent.length) state.gpuHistory.set(index, recent)
    else state.gpuHistory.delete(index)
  })
  persistGpuSession()
}

function gpuHistoryPoints(samples, now, windowMs, metricKey, maximum, width = 300, height = 70) {
  const windowStart = now - windowMs
  return samples.filter((sample) => Number.isFinite(sample[metricKey])).map((sample) => {
    const x = Math.min(width, Math.max(0, (sample.timestamp - windowStart) / windowMs * width))
    const y = height - (Math.min(maximum, Math.max(0, sample[metricKey])) / maximum * height)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

function addGpuChartGrid(svg, width, height) {
  for (let column = 0; column <= 10; column += 1) {
    const x = column * width / 10
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
    line.setAttribute('class', 'gpu-grid-line')
    line.setAttribute('x1', String(x))
    line.setAttribute('x2', String(x))
    line.setAttribute('y1', '0')
    line.setAttribute('y2', String(height))
    svg.append(line)
  }
  for (let row = 0; row <= 4; row += 1) {
    const y = row * height / 4
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
    line.setAttribute('class', 'gpu-grid-line')
    line.setAttribute('x1', '0')
    line.setAttribute('x2', String(width))
    line.setAttribute('y1', String(y))
    line.setAttribute('y2', String(y))
    svg.append(line)
  }
}

function gpuMetricMaximum(metric, gpu, history) {
  const observed = Math.max(1, ...history.map((sample) => sample[metric.key] || 0))
  if (['utilization', 'memory_utilization', 'temperature', 'fan_speed'].includes(metric.key)) return 100
  if (metric.key === 'memory_used' && Number.isFinite(gpu.memory_total)) return Math.max(1, gpu.memory_total)
  if (metric.key === 'power' && Number.isFinite(gpu.power_limit)) return Math.max(1, gpu.power_limit)
  if (metric.key === 'graphics_clock' && Number.isFinite(gpu.graphics_clock_max)) return Math.max(1, gpu.graphics_clock_max)
  if (metric.key === 'memory_clock' && Number.isFinite(gpu.memory_clock_max)) return Math.max(1, gpu.memory_clock_max)
  return Math.ceil(observed * 1.1)
}

function formatGpuMetric(metric, value) {
  if (!Number.isFinite(value)) return 'N/A'
  if (['utilization', 'memory_utilization', 'fan_speed'].includes(metric.key)) return `${Math.round(value)}%`
  if (metric.key === 'memory_used') return `${(value / 1024).toFixed(1)} GB`
  if (metric.key === 'temperature') return `${Math.round(value)} C`
  if (metric.key === 'power') return `${Math.round(value)} W`
  return `${Math.round(value)} MHz`
}

function attachGpuChartHover(plot, samples, metric, now) {
  const line = element('div', 'gpu-hover-line')
  const tooltip = element('div', 'gpu-hover-tooltip')
  line.hidden = true
  tooltip.hidden = true
  plot.append(line, tooltip)

  plot.addEventListener('pointermove', (event) => {
    state.gpuHovering = true
    const bounds = plot.getBoundingClientRect()
    const offset = Math.min(bounds.width, Math.max(0, event.clientX - bounds.left))
    const ratio = bounds.width ? offset / bounds.width : 0
    const targetTime = now - state.gpuWindowMs + (ratio * state.gpuWindowMs)
    const nearest = samples.reduce((best, sample) => {
      if (!best) return sample
      return Math.abs(sample.timestamp - targetTime) < Math.abs(best.timestamp - targetTime) ? sample : best
    }, null)
    const tolerance = Math.max(1500, state.gpuWindowMs * 10 / Math.max(1, bounds.width))
    const hasSample = nearest && Math.abs(nearest.timestamp - targetTime) <= tolerance
    const shownTime = new Date(hasSample ? nearest.timestamp : targetTime).toLocaleTimeString(browserLanguage())
    tooltip.textContent = hasSample
      ? `${formatGpuMetric(metric, nearest[metric.key])} / ${shownTime}`
      : `${t('gpu.noSample')} / ${shownTime}`
    const percent = ratio * 100
    line.style.left = `${percent}%`
    tooltip.style.left = `${percent}%`
    tooltip.classList.toggle('align-start', percent < 18)
    tooltip.classList.toggle('align-end', percent > 82)
    line.hidden = false
    tooltip.hidden = false
  })
  plot.addEventListener('pointerleave', () => {
    state.gpuHovering = false
    line.hidden = true
    tooltip.hidden = true
    renderGpuMonitor(state.gpuStats)
  })
}

function createGpuChart(metric, gpu, history, now) {
  const current = gpu[metric.key]
  if (!Number.isFinite(current)) return null
  const samples = history.filter((sample) => Number.isFinite(sample[metric.key]))
  const maximum = gpuMetricMaximum(metric, gpu, samples)
  const average = samples.length ? samples.reduce((sum, sample) => sum + sample[metric.key], 0) / samples.length : current
  const peak = samples.length ? Math.max(...samples.map((sample) => sample[metric.key])) : current
  const width = 300
  const height = 70
  const points = gpuHistoryPoints(samples, now, state.gpuWindowMs, metric.key, maximum, width, height)
  const chart = element('div', 'gpu-metric-chart')
  chart.style.setProperty('--chart-color', metric.color)
  const scale = element('div', 'gpu-chart-scale')
  scale.append(element('span', '', metric.label), element('strong', '', formatGpuMetric(metric, current)))
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.setAttribute('class', 'gpu-sparkline')
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`)
  svg.setAttribute('preserveAspectRatio', 'none')
  svg.setAttribute('aria-label', t('gpu.historyAria', {
    metric: metric.label,
    average: formatGpuMetric(metric, average),
    peak: formatGpuMetric(metric, peak),
  }))
  svg.setAttribute('role', 'img')
  addGpuChartGrid(svg, width, height)
  if (samples.length > 1) {
    const pointList = points.split(' ')
    const firstX = pointList[0].split(',')[0]
    const lastX = pointList.at(-1).split(',')[0]
    const area = document.createElementNS('http://www.w3.org/2000/svg', 'polygon')
    area.setAttribute('class', 'gpu-chart-area')
    area.setAttribute('points', `${firstX},${height} ${points} ${lastX},${height}`)
    svg.append(area)
  }
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline')
  line.setAttribute('class', 'gpu-chart-line')
  line.setAttribute('points', points)
  svg.append(line)
  if (samples.length) {
    const latestPoint = points.split(' ').at(-1).split(',')
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
    marker.setAttribute('class', 'gpu-chart-marker')
    marker.setAttribute('cx', latestPoint[0])
    marker.setAttribute('cy', latestPoint[1])
    marker.setAttribute('r', '2.5')
    svg.append(marker)
  }
  const axis = element('div', 'gpu-chart-axis')
  axis.append(
    element('span', '', state.gpuWindowMs === 60000 ? t('gpu.oneMinute') : t('gpu.tenMinutes')),
    element('span', '', t('gpu.averagePeak', {
      average: formatGpuMetric(metric, average),
      peak: formatGpuMetric(metric, peak),
    })),
  )
  const plot = element('div', 'gpu-chart-plot')
  plot.append(svg)
  attachGpuChartHover(plot, samples, metric, now)
  chart.append(scale, plot, axis)
  return chart
}

function renderGpuMonitor(gpus) {
  const monitor = element('div', 'gpu-monitor')
  const heading = element('div', 'gpu-monitor-heading')
  const windows = element('div', 'gpu-window-control')
  windows.setAttribute('role', 'group')
  windows.setAttribute('aria-label', t('gpu.historyWindow'))
  ;[[60000, t('gpu.oneMinute')], [600000, t('gpu.tenMinutes')]].forEach(([windowMs, label]) => {
    const button = element('button', windowMs === state.gpuWindowMs ? 'active' : '', label)
    button.type = 'button'
    button.setAttribute('aria-pressed', String(windowMs === state.gpuWindowMs))
    button.addEventListener('click', () => {
      state.gpuWindowMs = windowMs
      persistUiSession()
      renderGpuMonitor(state.gpuStats)
    })
    windows.append(button)
  })
  heading.append(element('div', 'gpu-monitor-title', t('gpu.monitor')), windows)
  monitor.append(heading)
  if (!gpus.length) {
    monitor.append(element('div', 'gpu-monitor-muted', t('gpu.unavailable')))
    $('#gpu-output').replaceChildren(monitor)
    return
  }
  const grid = element('div', 'gpu-card-grid')
  gpus.forEach((gpu) => {
    const now = Date.now()
    const history = (state.gpuHistory.get(gpu.index) || []).filter((sample) => sample.timestamp >= now - state.gpuWindowMs)
    const card = element('div', 'gpu-card')
    const head = element('div', 'gpu-card-head')
    head.append(element('strong', '', `GPU ${gpu.index}`), element('span', '', gpu.name))
    const metrics = element('div', 'gpu-metrics-grid')
    GPU_METRICS.forEach((metric) => {
      const chart = createGpuChart(metric, gpu, history, now)
      if (chart) metrics.append(chart)
    })
    const details = element('div', 'gpu-live-details')
    if (gpu.performance_state) details.append(element('span', '', t('gpu.state', { state: gpu.performance_state })))
    if (Number.isFinite(gpu.pcie_generation) && Number.isFinite(gpu.pcie_width)) {
      details.append(element('span', '', t('gpu.pcie', { generation: gpu.pcie_generation, width: gpu.pcie_width })))
    }
    if (Number.isFinite(gpu.power_limit)) {
      details.append(element('span', '', t('gpu.powerLimit', { power: Math.round(gpu.power_limit) })))
    }
    card.append(head, metrics, details)
    grid.append(card)
  })
  monitor.append(grid)
  $('#gpu-output').replaceChildren(monitor)
}

async function refreshGpuMonitor() {
  if (state.gpuRefreshActive) return
  state.gpuRefreshActive = true
  try {
    const payload = await fetchJson('/system/gpu')
    state.gpuStats = Array.isArray(payload.gpus) ? payload.gpus : []
    mergeGpuHistory(payload.history)
    if (!state.gpuHovering) renderGpuMonitor(state.gpuStats)
  } catch {
    if (!state.gpuHovering) renderGpuMonitor(state.gpuStats)
  } finally {
    state.gpuRefreshActive = false
  }
}

function startGpuMonitor() {
  if (state.gpuTimer || document.hidden) return
  if (state.gpuStats.length) renderGpuMonitor(state.gpuStats)
  refreshGpuMonitor()
  state.gpuTimer = setInterval(refreshGpuMonitor, GPU_POLL_INTERVAL_MS)
}

function stopGpuMonitor() {
  clearInterval(state.gpuTimer)
  state.gpuTimer = null
}

function updateRuntime(status) {
  state.status = status
  const badge = $('#runtime-badge')
  badge.dataset.state = 'ready'
  badge.querySelector('strong').textContent = 'Inference ready'
  $('#runtime-model').textContent = `${(status.loaded_languages || []).length}/${(status.configured_languages || []).length} models / ${status.runtime}`
}

async function loadWorkspace(setInitialText = true) {
  const [defaults, status, voicesPayload, formats] = await Promise.all([
    fetchJson('/tts/defaults'),
    fetchJson('/tts/status'),
    fetchJson('/tts/voices'),
    fetchJson('/tts/formats'),
  ])
  state.defaults = defaults
  state.voices = Array.isArray(voicesPayload) ? voicesPayload : voicesPayload.voices || []
  const loaded = state.voices.filter((item) => item.status === 'loaded' && item.speakers?.length)
  const previousLanguage = $('#language').value
  setSelectOptions($('#language'), loaded.map((item) => ({ value: item.language, label: item.language })), previousLanguage || loaded[0]?.language)
  refreshVoiceOptions($('#voice').value)
  setSelectOptions($('#preset'), Object.keys(defaults.presets || {}).map((name) => ({ value: name, label: name })), 'Balanced')
  setSelectOptions(
    $('#output-format'),
    Object.entries(formats.formats || {}).map(([value, config]) => ({ value, label: config.label })),
    formats.formats?.mp3 ? 'mp3' : formats.default,
  )
  if (setInitialText) $('#text-input').value = defaults.texts?.[$('#language').value] || ''
  applyPreset(selectedPreset() ? $('#preset').value : Object.keys(defaults.presets || {})[0])
  applyAudioControlDefaults()
  updateTextMetrics()
  updateRuntime(status)
  setStatus('Ready', 'success')
}

async function pollReadiness() {
  try { updateRuntime(await fetchJson('/tts/status')) } catch {
    $('#runtime-badge').dataset.state = 'starting'
    $('#runtime-badge strong').textContent = 'Inference starting'
    $('#runtime-model').textContent = 'Waiting for inference service'
  }
  setTimeout(pollReadiness, 15000)
}

document.addEventListener('audio-error', (event) => showToast(errorMessage(event.detail)))
document.addEventListener('visibilitychange', () => {
  if (document.hidden) stopGpuMonitor()
  else if (state.activeTab === 'system') startGpuMonitor()
})
window.addEventListener('beforeunload', () => {
  state.streamAbort?.abort()
  state.streamPlayback?.stop()
  stopGpuMonitor()
})

restoreSessionState()
setHeroCollapsed(state.headerCollapsed, false, false)
loadWorkspace().then(() => activateTab(state.activeTab)).catch((error) => {
  setStatus('Connection failed', 'error')
  showToast(errorMessage(error))
})
pollReadiness()
