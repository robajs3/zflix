(function () {
  const video = document.getElementById("zjVideo");
  const stage = document.getElementById("playerStage");
  const controls = document.getElementById("zjControls");
  const bigPlay = document.getElementById("zjBigPlay");
  const playPauseBtn = document.getElementById("zjPlayPause");
  const iconPlay = document.getElementById("zjIconPlay");
  const iconPause = document.getElementById("zjIconPause");
  const progressWrap = document.getElementById("zjProgressWrap");
  const played = document.getElementById("zjPlayed");
  const buffered = document.getElementById("zjBuffered");
  const handle = document.getElementById("zjHandle");
  const timeLabel = document.getElementById("zjTime");
  const muteBtn = document.getElementById("zjMute");
  const iconVolume = document.getElementById("zjIconVolume");
  const iconMuted = document.getElementById("zjIconMuted");
  const volumeSlider = document.getElementById("zjVolume");
  const fullscreenBtn = document.getElementById("zjFullscreen");

  if (!video) return;

  let hideControlsTimer = null;

  function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) seconds = 0;
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60)
      .toString()
      .padStart(2, "0");
    return `${m}:${s}`;
  }

  function togglePlay() {
    if (video.paused || video.ended) {
      video.play();
    } else {
      video.pause();
    }
  }

  function updatePlayIcon() {
    const isPaused = video.paused || video.ended;
    iconPlay.style.display = isPaused ? "block" : "none";
    iconPause.style.display = isPaused ? "none" : "block";
    bigPlay.style.display = isPaused ? "flex" : "none";
  }

  function updateProgress() {
    if (!video.duration) return;
    const pct = (video.currentTime / video.duration) * 100;
    played.style.width = pct + "%";
    handle.style.left = pct + "%";
    timeLabel.textContent = `${formatTime(video.currentTime)} / ${formatTime(video.duration)}`;
  }

  function updateBuffered() {
    if (!video.duration || video.buffered.length === 0) return;
    const end = video.buffered.end(video.buffered.length - 1);
    buffered.style.width = (end / video.duration) * 100 + "%";
  }

  function seekFromEvent(e) {
    const rect = progressWrap.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    let ratio = (clientX - rect.left) / rect.width;
    ratio = Math.min(1, Math.max(0, ratio));
    if (video.duration) {
      video.currentTime = ratio * video.duration;
    }
  }

  function updateVolumeIcon() {
    const muted = video.muted || video.volume === 0;
    iconVolume.style.display = muted ? "none" : "block";
    iconMuted.style.display = muted ? "block" : "none";
  }

  function showControls() {
    controls.classList.add("is-visible");
    stage.classList.remove("controls-hidden");
    clearTimeout(hideControlsTimer);
    if (!video.paused) {
      hideControlsTimer = setTimeout(() => {
        stage.classList.add("controls-hidden");
      }, 2500);
    }
  }

  // Play / pause
  playPauseBtn.addEventListener("click", togglePlay);
  bigPlay.addEventListener("click", togglePlay);
  video.addEventListener("click", togglePlay);
  video.addEventListener("play", updatePlayIcon);
  video.addEventListener("pause", updatePlayIcon);
  video.addEventListener("ended", updatePlayIcon);

  // Progress
  video.addEventListener("timeupdate", updateProgress);
  video.addEventListener("progress", updateBuffered);
  video.addEventListener("loadedmetadata", () => {
    updateProgress();
    updateBuffered();
  });

  let isSeeking = false;
  progressWrap.addEventListener("mousedown", (e) => {
    isSeeking = true;
    seekFromEvent(e);
  });
  window.addEventListener("mousemove", (e) => {
    if (isSeeking) seekFromEvent(e);
  });
  window.addEventListener("mouseup", () => {
    isSeeking = false;
  });
  progressWrap.addEventListener(
    "touchstart",
    (e) => {
      isSeeking = true;
      seekFromEvent(e);
    },
    { passive: true }
  );
  progressWrap.addEventListener(
    "touchmove",
    (e) => {
      if (isSeeking) seekFromEvent(e);
    },
    { passive: true }
  );
  progressWrap.addEventListener("touchend", () => {
    isSeeking = false;
  });

  // Volume
  muteBtn.addEventListener("click", () => {
    video.muted = !video.muted;
    updateVolumeIcon();
  });
  volumeSlider.addEventListener("input", () => {
    video.volume = parseFloat(volumeSlider.value);
    video.muted = video.volume === 0;
    updateVolumeIcon();
  });

  // Fullscreen
  fullscreenBtn.addEventListener("click", () => {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      stage.requestFullscreen();
    }
  });

  // Auto-hide controls
  ["mousemove", "click", "touchstart"].forEach((evt) => {
    stage.addEventListener(evt, showControls);
  });
  video.addEventListener("pause", showControls);

  // Keyboard shortcuts
  document.addEventListener("keydown", (e) => {
    if (!document.body.classList.contains("page-player")) return;
    if (e.target.tagName === "INPUT") return;

    if (e.code === "Space") {
      e.preventDefault();
      togglePlay();
    } else if (e.code === "ArrowRight") {
      video.currentTime = Math.min(video.duration, video.currentTime + 10);
    } else if (e.code === "ArrowLeft") {
      video.currentTime = Math.max(0, video.currentTime - 10);
    }
  });

  updatePlayIcon();
  updateVolumeIcon();
  showControls();
})();
