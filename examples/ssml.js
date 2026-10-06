const audioPlayers = Array.from(document.querySelectorAll('.audio-player'))
const toast = document.querySelector('.toast')
const volumeButton = document.querySelector('.volume-button')
const volumeSlider = document.querySelector('.volume-slider')
const volumeIconOn = document.querySelector('.volume-icon-on')
const volumeIconMuted = document.querySelector('.volume-icon-muted')
let currentVolume = Number.parseFloat(volumeSlider?.value || '0.85')
let lastVolume = currentVolume > 0 ? currentVolume : 0.85
let toastTimer

function formatTime(value) {
  if (!Number.isFinite(value)) return '0:00'
  const minutes = Math.floor(value / 60)
  const seconds = Math.floor(value % 60).toString().padStart(2, '0')
  return `${minutes}:${seconds}`
}

function showToast(message) {
  window.clearTimeout(toastTimer)
  toast.textContent = message
  toast.hidden = false
  toastTimer = window.setTimeout(() => { toast.hidden = true }, 1800)
}

function pauseOtherPlayers(currentAudio) {
  audioPlayers.forEach((player) => {
    const audio = player.querySelector('audio')
    if (audio !== currentAudio) audio.pause()
  })
}

function updateVolumeControl() {
  const muted = currentVolume <= 0.001
  audioPlayers.forEach((player) => {
    const audio = player.querySelector('audio')
    audio.volume = currentVolume
    audio.muted = muted
  })
  if (volumeSlider) volumeSlider.value = currentVolume.toString()
  if (volumeButton) {
    volumeButton.dataset.muted = muted.toString()
    volumeButton.setAttribute('aria-label', muted ? 'Unmute audio' : 'Mute audio')
  }
  if (volumeIconOn && volumeIconMuted) {
    volumeIconOn.hidden = muted
    volumeIconMuted.hidden = !muted
  }
}

volumeSlider?.addEventListener('input', () => {
  currentVolume = Number.parseFloat(volumeSlider.value)
  if (currentVolume > 0) lastVolume = currentVolume
  updateVolumeControl()
})

volumeButton?.addEventListener('click', () => {
  if (currentVolume > 0) {
    lastVolume = currentVolume
    currentVolume = 0
  } else {
    currentVolume = lastVolume || 0.85
  }
  updateVolumeControl()
})

audioPlayers.forEach((player) => {
  const audio = player.querySelector('audio')
  const toggle = player.querySelector('.play-toggle')
  const progress = player.querySelector('.progress-button')
  const fill = player.querySelector('.progress-fill')
  const knob = player.querySelector('.progress-knob')
  const time = player.querySelector('.time')
  const title = player.dataset.title || 'dialogue'
  let suppressClickSeek = false

  function setProgress(value) {
    const bounded = Math.max(0, Math.min(100, value))
    fill.style.width = `${bounded}%`
    knob.style.left = `${bounded}%`
  }

  function updateTime() {
    const duration = Number.isFinite(audio.duration) ? audio.duration : 0
    time.textContent = `${formatTime(audio.currentTime)} / ${formatTime(duration)}`
    setProgress(duration > 0 ? (audio.currentTime / duration) * 100 : 0)
  }

  function seek(event) {
    if (!Number.isFinite(audio.duration)) return
    const rect = progress.getBoundingClientRect()
    const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width))
    audio.currentTime = ratio * audio.duration
    updateTime()
  }

  toggle.addEventListener('click', () => {
    if (audio.paused) {
      pauseOtherPlayers(audio)
      audio.play()
    } else {
      audio.pause()
    }
  })

  progress.addEventListener('click', (event) => {
    if (suppressClickSeek) {
      suppressClickSeek = false
      return
    }
    seek(event)
  })
  progress.addEventListener('pointerdown', (event) => {
    event.preventDefault()
    suppressClickSeek = true
    progress.setPointerCapture(event.pointerId)
    seek(event)
  })
  progress.addEventListener('pointermove', (event) => {
    if (progress.hasPointerCapture(event.pointerId)) seek(event)
  })
  progress.addEventListener('pointerup', (event) => {
    if (progress.hasPointerCapture(event.pointerId)) progress.releasePointerCapture(event.pointerId)
  })
  progress.addEventListener('pointercancel', (event) => {
    if (progress.hasPointerCapture(event.pointerId)) progress.releasePointerCapture(event.pointerId)
  })

  audio.addEventListener('loadedmetadata', updateTime)
  audio.addEventListener('timeupdate', updateTime)
  audio.addEventListener('play', () => {
    player.classList.add('is-playing')
    toggle.setAttribute('aria-label', `Pause ${title}`)
  })
  audio.addEventListener('pause', () => {
    player.classList.remove('is-playing')
    toggle.setAttribute('aria-label', `Play ${title}`)
  })
  audio.addEventListener('ended', () => {
    audio.currentTime = 0
    updateTime()
  })
})

document.querySelectorAll('[data-copy-target]').forEach((button) => {
  button.addEventListener('click', async () => {
    const source = document.getElementById(button.dataset.copyTarget)
    try {
      await navigator.clipboard.writeText(source.textContent)
      showToast('Copied to clipboard')
    } catch {
      showToast('Clipboard access was unavailable')
    }
  })
})

updateVolumeControl()
