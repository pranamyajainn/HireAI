// AI Interview Animation System
document.addEventListener('DOMContentLoaded', function () {
    const overlayHTML = document.getElementById('aiInterviewOverlay') || createOverlay();
    const widgetContainer = document.getElementById('widgetContainer');
    const closeWidgetBtn = document.getElementById('closeWidgetBtn');
    const toggleWidgetBtn = document.getElementById('toggleWidgetBtn');
    const mainContainer = document.getElementById('mainContainer');

    let isWidgetActive = false;
    let overlayActive = false;
    let audioChime = null;

    function createAudioElement() {
        audioChime = document.createElement('audio');
        audioChime.src = 'https://assets.mixkit.co/active_storage/sfx/2568/2568-preview.mp3';
        audioChime.preload = 'auto';
        audioChime.volume = 0.3;
        document.body.appendChild(audioChime);
    }

    function createOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'aiInterviewOverlay';
        overlay.className = 'ai-interview-overlay';
        overlay.innerHTML = `
            <div class="overlay-backdrop"></div>
            <div class="overlay-content">
                <div class="particles-container">${'<div class="particle"></div>'.repeat(12)}</div>
                <div class="neural-network">
                    <div class="neural-line"></div>
                    <div class="neural-line"></div>
                    <div class="neural-line"></div>
                </div>
                <div class="ai-orb-container">
                    <div class="ai-orb">
                        <div class="orb-core"></div>
                        <div class="orb-ring"></div>
                        <div class="orb-ring-outer"></div>
                        <div class="orb-particles"></div>
                    </div>
                </div>
                <div class="voice-visualization">
                    ${'<div class="wave-bar"></div>'.repeat(7)}
                </div>
                <div class="welcome-message">
                    <h2 class="typing-text">Welcome to your AI interview</h2>
                    <p class="fade-in-text">I'm here to guide our conversation</p>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        return overlay;
    }

    function personalizeWelcome() {
        const candidateName = document.getElementById('candidateName')?.value?.trim() || '';
        const welcomeText = document.querySelector('.typing-text');
        if (candidateName) {
            welcomeText.textContent = `Hello ${candidateName}, welcome to your AI interview`;
        }
    }

    function showOverlay() {
        const overlay = document.getElementById('aiInterviewOverlay');
        personalizeWelcome();
        overlay.style.display = 'flex';
        setTimeout(() => {
            overlay.style.opacity = '1';
            startWaveAnimation();
            if (audioChime) audioChime.play().catch(e => console.log('Audio play prevented:', e));
            overlayActive = true;
        }, 100);

        setTimeout(() => {
            hideOverlay();
            // Auto-click "Start Call" button after overlay
            const tryStartCall = () => {
                const callBtn = document.querySelector('elevenlabs-convai')?.shadowRoot?.querySelector('button') ||
                                document.querySelector('button[aria-label="Start a call"]') ||
                                document.querySelector('.elevenlabs-call-button') ||
                                document.querySelector('.widget-fullpage-container button');

                if (callBtn) {
                    callBtn.click();
                    console.log('✅ Call started via auto-click.');
                } else {
                    console.warn('⚠️ Start Call button not found. Trying again in 1s...');
                    setTimeout(tryStartCall, 1000);
                }
            };

            tryStartCall();
        }, 9000);
    }

    function hideOverlay() {
        if (!overlayActive) return;
        const overlay = document.getElementById('aiInterviewOverlay');
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.style.display = 'none';
            stopWaveAnimation();
            overlayActive = false;
        }, 1500);
    }

    function startWaveAnimation() {
        const waveBars = document.querySelectorAll('.wave-bar');
        waveBars.forEach((bar, i) => {
            bar.style.animation = `wave ${1 + Math.random() * 0.5}s ease-in-out ${i * 0.1}s infinite`;
        });
    }

    function stopWaveAnimation() {
        const waveBars = document.querySelectorAll('.wave-bar');
        waveBars.forEach(bar => bar.style.animation = '');
    }

    function openWidget() {
        if (widgetContainer) {
            showOverlay();
            setTimeout(() => {
                widgetContainer.style.display = 'block';
                if (mainContainer) mainContainer.style.display = 'none';
                document.body.style.overflow = 'hidden';
                isWidgetActive = true;
            }, 500);
        }
    }

    function closeWidget() {
        if (widgetContainer) {
            widgetContainer.style.display = 'none';
            if (mainContainer) mainContainer.style.display = 'block';
            document.body.style.overflow = 'auto';
            isWidgetActive = false;
        }
    }

    if (toggleWidgetBtn) toggleWidgetBtn.addEventListener('click', openWidget);
    if (closeWidgetBtn) closeWidgetBtn.addEventListener('click', closeWidget);

    document.addEventListener('elevenlabs-convai:speaking', () => {
        if (overlayActive) startWaveAnimation();
    });

    document.addEventListener('elevenlabs-convai:silent', () => {
        if (overlayActive) stopWaveAnimation();
    });

    createAudioElement();
});