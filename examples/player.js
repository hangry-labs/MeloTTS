const players = Array.from(document.querySelectorAll(".brand-card audio"));

function formatTime(value) {
  if (!Number.isFinite(value)) {
    return "0:00";
  }

  const minutes = Math.floor(value / 60);
  const seconds = Math.floor(value % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function pauseOthers(currentAudio) {
  players.forEach((audio) => {
    if (audio !== currentAudio) {
      audio.pause();
    }
  });
}

players.forEach((audio) => {
  const card = audio.closest(".brand-card");

  audio.removeAttribute("controls");
  if (audio.nextElementSibling && audio.nextElementSibling.classList.contains("player")) {
    return;
  }

  const controls = document.createElement("div");
  controls.className = "player";
  controls.innerHTML = `
    <button class="progress-button" type="button" aria-label="Seek sample">
      <span class="progress-track" aria-hidden="true">
        <span class="progress-fill"></span>
        <span class="progress-knob"></span>
      </span>
    </button>
    <span class="duration">0:00</span>
  `;

  audio.insertAdjacentElement("afterend", controls);

  const progressButton = controls.querySelector(".progress-button");
  const progressFill = controls.querySelector(".progress-fill");
  const progressKnob = controls.querySelector(".progress-knob");
  const duration = controls.querySelector(".duration");

  function setProgress(value) {
    const progress = Math.max(0, Math.min(100, value));
    progressFill.style.width = `${progress}%`;
    progressKnob.style.left = `${progress}%`;
  }

  function seekToPosition(event) {
    if (Number.isFinite(audio.duration)) {
      const rect = progressButton.getBoundingClientRect();
      const position = (event.clientX - rect.left) / rect.width;
      const progress = Math.max(0, Math.min(1, position));
      audio.currentTime = progress * audio.duration;
      setProgress(progress * 100);
    }
  }

  function togglePlayback() {
    if (audio.paused) {
      pauseOthers(audio);
      audio.play();
    } else {
      audio.pause();
    }
  }

  if (card) {
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");
    card.setAttribute("aria-label", `Play ${card.querySelector("h2")?.textContent || "voice sample"}`);

    card.addEventListener("click", togglePlayback);
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        togglePlayback();
      }
    });
  }

  progressButton.addEventListener("click", (event) => {
    event.stopPropagation();
    seekToPosition(event);
  });

  progressButton.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    progressButton.setPointerCapture(event.pointerId);
    seekToPosition(event);
  });

  progressButton.addEventListener("pointermove", (event) => {
    if (progressButton.hasPointerCapture(event.pointerId)) {
      event.preventDefault();
      event.stopPropagation();
      seekToPosition(event);
    }
  });

  progressButton.addEventListener("pointerup", (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (progressButton.hasPointerCapture(event.pointerId)) {
      progressButton.releasePointerCapture(event.pointerId);
    }
  });

  progressButton.addEventListener("pointercancel", (event) => {
    if (progressButton.hasPointerCapture(event.pointerId)) {
      progressButton.releasePointerCapture(event.pointerId);
    }
  });

  audio.addEventListener("loadedmetadata", () => {
    duration.textContent = `0:00 / ${formatTime(audio.duration)}`;
  });

  audio.addEventListener("timeupdate", () => {
    if (Number.isFinite(audio.duration) && audio.duration > 0) {
      setProgress((audio.currentTime / audio.duration) * 100);
      duration.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration)}`;
    }
  });

  audio.addEventListener("play", () => {
    if (card) {
      card.classList.add("is-playing");
      card.setAttribute("aria-label", `Pause ${card.querySelector("h2")?.textContent || "voice sample"}`);
    }
  });

  audio.addEventListener("pause", () => {
    if (card) {
      card.classList.remove("is-playing");
      card.setAttribute("aria-label", `Play ${card.querySelector("h2")?.textContent || "voice sample"}`);
    }
  });

  audio.addEventListener("ended", () => {
    setProgress(0);
    if (card) {
      card.classList.remove("is-playing");
      card.setAttribute("aria-label", `Play ${card.querySelector("h2")?.textContent || "voice sample"}`);
    }
  });
});
