const PAGE_LANGUAGES = new Set(["en", "es", "fr", "ja", "zh", "ko"]);
const PRODUCT_URLS = {
  en: "https://hangrylabs.app/software/melotts",
  es: "https://hangrylabs.app/es/software/melotts",
  fr: "https://hangrylabs.app/software/melotts",
  ja: "https://hangrylabs.app/ja/software/melotts",
  zh: "https://hangrylabs.app/zh/software/melotts",
  ko: "https://hangrylabs.app/software/melotts",
};
const TRANSLATIONS = {
  en: {
    title: "Hangry Labs Melo TTS Voice Examples",
    brandSubtitle: "Useful AI tools, easy to run",
    volumeControl: "Volume control",
    muteAudio: "Mute audio",
    unmuteAudio: "Unmute audio",
    volume: "Volume",
    ssmlDialogues: "SSML dialogues",
    headline: "Voice examples",
    intro: "Easy-run text-to-speech Docker images with a browser UI and HTTP API. These samples show the voices people will hear before they decide to run the container or connect it to an application.",
    all: "All",
    filterLabel: "Filter voice examples by language",
    examplesLabel: "Voice examples",
    playPrefix: "Play",
    pausePrefix: "Pause",
    seekSample: "Seek sample",
    samples: { enBritish: "English British", enNewest: "English newest", enV2: "English v2", en: "English", enIndian: "English Indian", enAustralian: "English Australian", enAmerican: "English American", enDefault: "English default", spanish: "Spanish", french: "French", chinese: "Chinese", japanese: "Japanese", korean: "Korean" },
  },
  es: {
    title: "Ejemplos de voz de Hangry Labs Melo TTS",
    brandSubtitle: "Herramientas de IA útiles y fáciles de ejecutar",
    volumeControl: "Control de volumen",
    muteAudio: "Silenciar audio",
    unmuteAudio: "Activar audio",
    volume: "Volumen",
    ssmlDialogues: "Diálogos SSML",
    headline: "Ejemplos de voz",
    intro: "Imágenes Docker de texto a voz fáciles de ejecutar, con interfaz web y API HTTP. Estas muestras permiten escuchar las voces antes de iniciar el contenedor o conectarlo a una aplicación.",
    all: "Todo",
    filterLabel: "Filtrar ejemplos de voz por idioma",
    examplesLabel: "Ejemplos de voz",
    playPrefix: "Reproducir",
    pausePrefix: "Pausar",
    seekSample: "Buscar en la muestra",
    samples: { enBritish: "Inglés británico", enNewest: "Inglés más reciente", enV2: "Inglés v2", en: "Inglés", enIndian: "Inglés de India", enAustralian: "Inglés australiano", enAmerican: "Inglés estadounidense", enDefault: "Inglés predeterminado", spanish: "Español", french: "Francés", chinese: "Chino", japanese: "Japonés", korean: "Coreano" },
  },
  fr: {
    title: "Exemples de voix Hangry Labs Melo TTS",
    brandSubtitle: "Des outils d'IA utiles et faciles à lancer",
    volumeControl: "Contrôle du volume",
    muteAudio: "Couper le son",
    unmuteAudio: "Rétablir le son",
    volume: "Volume",
    ssmlDialogues: "Dialogues SSML",
    headline: "Exemples de voix",
    intro: "Des images Docker de synthèse vocale faciles à lancer, avec interface web et API HTTP. Écoutez ces voix avant de démarrer le conteneur ou de le connecter à une application.",
    all: "Tout",
    filterLabel: "Filtrer les exemples de voix par langue",
    examplesLabel: "Exemples de voix",
    playPrefix: "Lire",
    pausePrefix: "Mettre en pause",
    seekSample: "Parcourir l'extrait",
    samples: { enBritish: "Anglais britannique", enNewest: "Anglais le plus récent", enV2: "Anglais v2", en: "Anglais", enIndian: "Anglais indien", enAustralian: "Anglais australien", enAmerican: "Anglais américain", enDefault: "Anglais par défaut", spanish: "Espagnol", french: "Français", chinese: "Chinois", japanese: "Japonais", korean: "Coréen" },
  },
  ja: {
    title: "Hangry Labs Melo TTS 音声サンプル",
    brandSubtitle: "便利な AI ツールを簡単に",
    volumeControl: "音量調整",
    muteAudio: "ミュート",
    unmuteAudio: "ミュート解除",
    volume: "音量",
    ssmlDialogues: "SSML ダイアログ",
    headline: "音声サンプル",
    intro: "ブラウザー UI と HTTP API を備えた、簡単に実行できるテキスト読み上げ Docker イメージです。コンテナを起動したりアプリケーションから接続したりする前に、各音声を試聴できます。",
    all: "すべて",
    filterLabel: "言語で音声サンプルを絞り込む",
    examplesLabel: "音声サンプル",
    playPrefix: "再生",
    pausePrefix: "一時停止",
    seekSample: "サンプルをシーク",
    samples: { enBritish: "イギリス英語", enNewest: "最新英語", enV2: "英語 v2", en: "英語", enIndian: "インド英語", enAustralian: "オーストラリア英語", enAmerican: "アメリカ英語", enDefault: "既定の英語", spanish: "スペイン語", french: "フランス語", chinese: "中国語", japanese: "日本語", korean: "韓国語" },
  },
  zh: {
    title: "Hangry Labs Melo TTS 声音示例",
    brandSubtitle: "实用的 AI 工具，轻松运行",
    volumeControl: "音量控制",
    muteAudio: "静音",
    unmuteAudio: "取消静音",
    volume: "音量",
    ssmlDialogues: "SSML 对话",
    headline: "声音示例",
    intro: "易于运行的文本转语音 Docker 镜像，内置浏览器界面和 HTTP API。启动容器或接入应用程序之前，可以先试听这些声音。",
    all: "全部",
    filterLabel: "按语言筛选声音示例",
    examplesLabel: "声音示例",
    playPrefix: "播放",
    pausePrefix: "暂停",
    seekSample: "跳转示例音频",
    samples: { enBritish: "英式英语", enNewest: "最新英语", enV2: "英语 v2", en: "英语", enIndian: "印度英语", enAustralian: "澳大利亚英语", enAmerican: "美式英语", enDefault: "默认英语", spanish: "西班牙语", french: "法语", chinese: "中文", japanese: "日语", korean: "韩语" },
  },
  ko: {
    title: "Hangry Labs Melo TTS 음성 예제",
    brandSubtitle: "유용한 AI 도구를 간편하게",
    volumeControl: "볼륨 제어",
    muteAudio: "음소거",
    unmuteAudio: "음소거 해제",
    volume: "볼륨",
    ssmlDialogues: "SSML 대화",
    headline: "음성 예제",
    intro: "브라우저 UI와 HTTP API가 포함된 간편한 텍스트 음성 변환 Docker 이미지입니다. 컨테이너를 실행하거나 애플리케이션에 연결하기 전에 음성을 미리 들어 볼 수 있습니다.",
    all: "전체",
    filterLabel: "언어별 음성 예제 필터",
    examplesLabel: "음성 예제",
    playPrefix: "재생",
    pausePrefix: "일시 정지",
    seekSample: "샘플 탐색",
    samples: { enBritish: "영국 영어", enNewest: "최신 영어", enV2: "영어 v2", en: "영어", enIndian: "인도 영어", enAustralian: "호주 영어", enAmerican: "미국 영어", enDefault: "기본 영어", spanish: "스페인어", french: "프랑스어", chinese: "중국어", japanese: "일본어", korean: "한국어" },
  },
};

let currentPageLanguage = "en";
const players = Array.from(document.querySelectorAll(".brand-card audio"));
const cards = Array.from(document.querySelectorAll(".brand-card"));
const languageButtons = Array.from(document.querySelectorAll("[data-language-value]"));
const volumeButton = document.querySelector(".volume-button");
const volumeSlider = document.querySelector(".volume-slider");
const volumeIconOn = document.querySelector(".volume-icon-on");
const volumeIconMuted = document.querySelector(".volume-icon-muted");
let currentVolume = Number.parseFloat(volumeSlider?.value || "0.85");
let lastVolume = currentVolume > 0 ? currentVolume : 0.85;

function translatePage(language) {
  currentPageLanguage = PAGE_LANGUAGES.has(language) ? language : "en";
  const translation = TRANSLATIONS[currentPageLanguage];
  document.documentElement.lang = currentPageLanguage;
  document.title = translation.title;
  document.querySelectorAll("[data-product-link]").forEach((link) => {
    link.href = PRODUCT_URLS[currentPageLanguage];
  });

  document.querySelectorAll("[data-page-i18n]").forEach((element) => {
    const value = translation[element.dataset.pageI18n];
    if (value) element.textContent = value;
  });
  document.querySelectorAll("[data-page-i18n-aria]").forEach((element) => {
    const value = translation[element.dataset.pageI18nAria];
    if (value) element.setAttribute("aria-label", value);
  });
  cards.forEach((card) => {
    const heading = card.querySelector("[data-sample-name]");
    const sampleName = translation.samples[card.dataset.sampleKey];
    if (heading && sampleName) heading.textContent = sampleName;
    const audio = card.querySelector("audio");
    card.setAttribute("aria-label", `${audio?.paused === false ? translation.pausePrefix : translation.playPrefix} ${sampleName || "voice sample"}`);
  });
  document.querySelectorAll(".progress-button").forEach((button) => {
    button.setAttribute("aria-label", translation.seekSample);
  });
  updateVolumeControl();
}

function setLanguageFilter(language) {
  players.forEach((audio) => audio.pause());
  if (language !== "all") translatePage(language);
  languageButtons.forEach((button) => {
    const active = button.dataset.languageValue === language;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", active.toString());
  });
  cards.forEach((card) => {
    card.hidden = language !== "all" && card.dataset.language !== language;
  });
}

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

function updateVolumeControl() {
  const isMuted = currentVolume <= 0.001;

  players.forEach((audio) => {
    audio.volume = currentVolume;
    audio.muted = isMuted;
  });

  if (volumeSlider) {
    volumeSlider.value = currentVolume.toString();
  }

  if (volumeButton) {
    const translation = TRANSLATIONS[currentPageLanguage];
    volumeButton.dataset.muted = isMuted.toString();
    volumeButton.setAttribute("aria-label", isMuted ? translation.unmuteAudio : translation.muteAudio);
  }

  if (volumeIconOn && volumeIconMuted) {
    volumeIconOn.hidden = isMuted;
    volumeIconMuted.hidden = !isMuted;
    volumeIconOn.style.display = isMuted ? "none" : "block";
    volumeIconMuted.style.display = isMuted ? "block" : "none";
  }
}

languageButtons.forEach((button) => {
  button.addEventListener("click", () => setLanguageFilter(button.dataset.languageValue || "all"));
});

if (volumeSlider) {
  volumeSlider.addEventListener("input", () => {
    currentVolume = Number.parseFloat(volumeSlider.value);

    if (currentVolume > 0) {
      lastVolume = currentVolume;
    }

    updateVolumeControl();
  });
}

if (volumeButton) {
  volumeButton.addEventListener("click", () => {
    if (currentVolume > 0) {
      lastVolume = currentVolume;
      currentVolume = 0;
    } else {
      currentVolume = lastVolume || 0.85;
    }

    updateVolumeControl();
  });
}

players.forEach((audio) => {
  const card = audio.closest(".brand-card");

  audio.volume = currentVolume;
  audio.removeAttribute("controls");
  if (audio.nextElementSibling && audio.nextElementSibling.classList.contains("player")) {
    return;
  }

  const controls = document.createElement("div");
  controls.className = "player";
  controls.innerHTML = `
    <button class="progress-button" type="button" aria-label="${TRANSLATIONS[currentPageLanguage].seekSample}">
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
  let suppressClickSeek = false;

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
    card.setAttribute("aria-label", `${TRANSLATIONS[currentPageLanguage].playPrefix} ${card.querySelector("h2")?.textContent || "voice sample"}`);

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
    if (suppressClickSeek) {
      suppressClickSeek = false;
      return;
    }
    seekToPosition(event);
  });

  progressButton.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    suppressClickSeek = true;
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
      card.setAttribute("aria-label", `${TRANSLATIONS[currentPageLanguage].pausePrefix} ${card.querySelector("h2")?.textContent || "voice sample"}`);
    }
  });

  audio.addEventListener("pause", () => {
    if (card) {
      card.classList.remove("is-playing");
      card.setAttribute("aria-label", `${TRANSLATIONS[currentPageLanguage].playPrefix} ${card.querySelector("h2")?.textContent || "voice sample"}`);
    }
  });

  audio.addEventListener("ended", () => {
    setProgress(0);
    if (card) {
      card.classList.remove("is-playing");
      card.setAttribute("aria-label", `${TRANSLATIONS[currentPageLanguage].playPrefix} ${card.querySelector("h2")?.textContent || "voice sample"}`);
    }
  });
});

const requestedLanguage = new URLSearchParams(window.location.search).get("lang")?.toLowerCase();
setLanguageFilter(PAGE_LANGUAGES.has(requestedLanguage) ? requestedLanguage : "en");
