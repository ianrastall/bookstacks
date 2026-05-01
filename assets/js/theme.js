// Theme and accent color management
var textUtilsStorage = window.__textUtilsStorage || {
    get(key) {
        try {
            return localStorage.getItem(key);
        } catch (_) {
            return null;
        }
    },
    set(key, value) {
        try {
            localStorage.setItem(key, value);
        } catch (_) {
            // Ignore storage write failures (private mode / quota).
        }
    },
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (_) {
            // Ignore storage removal failures.
        }
    }
};
window.__textUtilsStorage = textUtilsStorage;

if (typeof window.textUtilsClipboardWrite !== 'function') {
    window.textUtilsClipboardWrite = async function textUtilsClipboardWrite(value) {
        const text = String(value ?? '');

        if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
            return navigator.clipboard.writeText(text);
        }

        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.setAttribute('readonly', '');
        textarea.setAttribute('aria-hidden', 'true');
        textarea.style.position = 'fixed';
        textarea.style.top = '0';
        textarea.style.left = '-9999px';
        textarea.style.opacity = '0';

        const previousActive = document.activeElement;

        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        textarea.setSelectionRange(0, textarea.value.length);

        let copied = false;
        try {
            copied = typeof document.execCommand === 'function'
                && document.execCommand('copy');
        } finally {
            textarea.remove();
            if (previousActive && typeof previousActive.focus === 'function') {
                previousActive.focus();
            }
        }

        if (!copied) {
            throw new Error('Clipboard copy unavailable');
        }
    };
}

(function() {
    'use strict';

    if (window.__textUtilsThemeModuleLoaded) {
        return;
    }
    window.__textUtilsThemeModuleLoaded = true;

    const ACCENT_PALETTE = [
        { value: '#0d9488', label: 'Teal' },
        { value: '#3b82f6', label: 'Blue' },
        { value: '#8b5cf6', label: 'Purple' },
        { value: '#10b981', label: 'Emerald' },
        { value: '#f59e0b', label: 'Amber' },
        { value: '#ef4444', label: 'Red' },
        { value: '#ec4899', label: 'Soft Pink' },
        { value: '#fb7185', label: 'Coral' },
        { value: '#5f9ea0', label: 'Cadet Blue' },
        { value: '#6495ed', label: 'Cornflower' },
        { value: '#deb887', label: 'Burlywood' },
        { value: '#60a5fa', label: 'Sky Blue' },
        { value: '#7c3aed', label: 'Violet' }
    ];
    const DEFAULT_ACCENT = '#0d9488';

    let themeToggle = null;
    let accentColor = null;

    function captureControls() {
        themeToggle = document.getElementById('themeToggle');
        accentColor = document.getElementById('accentColor');

        if (themeToggle) {
            themeToggle.type = 'button';
        }

        if (accentColor && !accentColor.getAttribute('aria-label')) {
            accentColor.setAttribute('aria-label', 'Accent color');
        }
    }

    function normalizeHexColor(color) {
        if (typeof color !== 'string') {
            return DEFAULT_ACCENT;
        }

        let candidate = color.trim().toLowerCase();
        if (/^#[0-9a-f]{3}$/.test(candidate)) {
            candidate = `#${candidate[1]}${candidate[1]}${candidate[2]}${candidate[2]}${candidate[3]}${candidate[3]}`;
        }

        if (/^#[0-9a-f]{6}$/.test(candidate)) {
            return candidate;
        }

        return DEFAULT_ACCENT;
    }

    function hexToRgbTuple(hex) {
        const normalized = normalizeHexColor(hex).slice(1);
        const red = parseInt(normalized.slice(0, 2), 16);
        const green = parseInt(normalized.slice(2, 4), 16);
        const blue = parseInt(normalized.slice(4, 6), 16);
        return `${red}, ${green}, ${blue}`;
    }

    function clampUnit(value) {
        return Math.min(Math.max(value, 0), 1);
    }

    function rgbToHsl(red, green, blue) {
        const r = red / 255;
        const g = green / 255;
        const b = blue / 255;
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const delta = max - min;

        let hue = 0;
        let saturation = 0;
        const lightness = (max + min) / 2;

        if (delta !== 0) {
            saturation = delta / (1 - Math.abs((2 * lightness) - 1));

            switch (max) {
                case r:
                    hue = ((g - b) / delta) % 6;
                    break;
                case g:
                    hue = ((b - r) / delta) + 2;
                    break;
                default:
                    hue = ((r - g) / delta) + 4;
                    break;
            }

            hue *= 60;
            if (hue < 0) {
                hue += 360;
            }
        }

        return { hue, saturation, lightness };
    }

    function hslToRgb(hue, saturation, lightness) {
        const chroma = (1 - Math.abs((2 * lightness) - 1)) * saturation;
        const huePrime = (hue % 360) / 60;
        const x = chroma * (1 - Math.abs((huePrime % 2) - 1));
        let r1 = 0;
        let g1 = 0;
        let b1 = 0;

        if (huePrime >= 0 && huePrime < 1) {
            r1 = chroma;
            g1 = x;
        } else if (huePrime < 2) {
            r1 = x;
            g1 = chroma;
        } else if (huePrime < 3) {
            g1 = chroma;
            b1 = x;
        } else if (huePrime < 4) {
            g1 = x;
            b1 = chroma;
        } else if (huePrime < 5) {
            r1 = x;
            b1 = chroma;
        } else {
            r1 = chroma;
            b1 = x;
        }

        const match = lightness - (chroma / 2);
        const red = Math.round((r1 + match) * 255);
        const green = Math.round((g1 + match) * 255);
        const blue = Math.round((b1 + match) * 255);
        return { red, green, blue };
    }

    function adjustColor(color, amount) {
        const normalized = normalizeHexColor(color).slice(1);
        const parsed = parseInt(normalized, 16);

        if (Number.isNaN(parsed)) {
            return DEFAULT_ACCENT;
        }

        const red = (parsed >> 16) & 0xFF;
        const green = (parsed >> 8) & 0xFF;
        const blue = parsed & 0xFF;
        const hsl = rgbToHsl(red, green, blue);
        const adjustedLightness = clampUnit(hsl.lightness + (amount / 255));
        const adjusted = hslToRgb(hsl.hue, hsl.saturation, adjustedLightness);

        return `#${((adjusted.red << 16) | (adjusted.green << 8) | adjusted.blue).toString(16).padStart(6, '0')}`;
    }

    function applyAccent(color) {
        const normalized = normalizeHexColor(color);
        document.documentElement.style.setProperty('--accent', normalized);
        document.documentElement.style.setProperty('--accent-light', adjustColor(normalized, 20));
        document.documentElement.style.setProperty('--accent-rgb', hexToRgbTuple(normalized));
        return normalized;
    }

    function ensureAccentOptionExists(value) {
        if (!accentColor) {
            return;
        }

        const normalized = normalizeHexColor(value);
        if (accentColor.querySelector(`option[value="${normalized}"]`)) {
            return;
        }

        const customOption = document.createElement('option');
        customOption.value = normalized;
        customOption.textContent = `Custom (${normalized})`;
        accentColor.appendChild(customOption);
    }

    function populateAccentDropdown(selectedColor) {
        if (!accentColor) {
            return;
        }

        accentColor.replaceChildren();

        ACCENT_PALETTE.forEach(({ value, label }) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            accentColor.appendChild(option);
        });

        const normalizedSelected = normalizeHexColor(selectedColor);
        const hasSavedColor = ACCENT_PALETTE.some(
            ({ value }) => value.toLowerCase() === normalizedSelected
        );

        if (!hasSavedColor) {
            ensureAccentOptionExists(normalizedSelected);
        }

        accentColor.value = normalizedSelected;
    }

    function updateThemeToggleIcon(theme) {
        if (!themeToggle) {
            return;
        }

        const icon = document.createElement('span');
        icon.className = 'material-icons';
        icon.setAttribute('aria-hidden', 'true');
        icon.textContent = theme === 'dark' ? 'dark_mode' : 'light_mode';

        themeToggle.replaceChildren(icon);

        const isDark = theme === 'dark';
        themeToggle.setAttribute('aria-pressed', isDark ? 'true' : 'false');
        themeToggle.setAttribute('title', isDark ? 'Dark mode' : 'Light mode');
        themeToggle.setAttribute(
            'aria-label',
            isDark ? 'Switch to light theme' : 'Switch to dark theme'
        );
    }

    function getDefaultTheme() {
        const prefersLight = window.matchMedia
            && window.matchMedia('(prefers-color-scheme: light)').matches;
        return prefersLight ? 'light' : 'dark';
    }

    function loadPreferences() {
        const storedTheme = textUtilsStorage.get('theme');
        const savedTheme = storedTheme === 'light' || storedTheme === 'dark'
            ? storedTheme
            : getDefaultTheme();

        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeToggleIcon(savedTheme);

        const storedColor = textUtilsStorage.get('accentColor');
        const savedColor = normalizeHexColor(storedColor || DEFAULT_ACCENT);
        const appliedColor = applyAccent(savedColor);
        populateAccentDropdown(appliedColor);
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        textUtilsStorage.set('theme', newTheme);
        updateThemeToggleIcon(newTheme);
    }

    function changeAccentColor(color) {
        const normalized = applyAccent(color);
        textUtilsStorage.set('accentColor', normalized);
        if (accentColor) {
            ensureAccentOptionExists(normalized);
            accentColor.value = normalized;
        }
    }

    function setupEventListeners() {
        if (themeToggle && themeToggle.dataset.themeBound !== '1') {
            themeToggle.addEventListener('click', toggleTheme);
            themeToggle.dataset.themeBound = '1';
        }

        if (accentColor && accentColor.dataset.accentBound !== '1') {
            accentColor.addEventListener('change', (event) => {
                changeAccentColor(event.target.value);
            });
            accentColor.dataset.accentBound = '1';
        }
    }

    function init() {
        captureControls();
        loadPreferences();
        setupEventListeners();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.themeUtils = {
        adjustColor,
        applyAccent,
        normalizeHexColor,
        toggleTheme() {
            captureControls();
            toggleTheme();
        },
        changeAccentColor(color) {
            captureControls();
            changeAccentColor(color);
        },
        loadPreferences() {
            captureControls();
            loadPreferences();
        }
    };
})();

(function() {
    'use strict';

    if (window.__textUtilsSnowModuleLoaded) {
        return;
    }
    window.__textUtilsSnowModuleLoaded = true;

    const STORAGE_KEY = 'holiday_snow_enabled';
    const BTN_CLASS = 'btn btn-secondary';
    const BTN_ID = 'snowToggle';

    let canvas = null;
    let ctx = null;
    let width = 0;
    let height = 0;
    let particles = [];
    let animationId = null;
    let isSnowing = false;
    let resizeAttached = false;

    function isHolidaySeason() {
        const now = new Date();
        const month = now.getMonth();
        const date = now.getDate();

        if (month === 0 && date === 1) {
            return true;
        }

        if (month === 11) {
            return true;
        }

        if (month === 10) {
            const firstOfNovember = new Date(now.getFullYear(), 10, 1);
            const firstDay = firstOfNovember.getDay();
            const daysToFirstThursday = (4 - firstDay + 7) % 7;
            const thanksgivingDate = 1 + daysToFirstThursday + 21;
            return date >= thanksgivingDate;
        }

        return false;
    }

    if (!isHolidaySeason()) {
        return;
    }

    function resize() {
        if (!canvas || !ctx) {
            return;
        }

        const dpr = window.devicePixelRatio || 1;
        width = window.innerWidth;
        height = window.innerHeight;

        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function buildParticles() {
        const particleCount = Math.min(Math.floor(window.innerWidth / 10), 50);
        particles = [];

        for (let index = 0; index < particleCount; index++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                r: 1 + Math.random() * 2.5,
                v: 0.4 + Math.random() * 1.2,
                drift: (Math.random() * 2 - 1) * 0.5
            });
        }
    }

    function draw() {
        if (!isSnowing || !ctx) {
            return;
        }

        ctx.clearRect(0, 0, width, height);

        const theme = document.documentElement.getAttribute('data-theme');
        ctx.fillStyle = theme === 'light'
            ? 'rgba(0, 0, 0, 0.25)'
            : 'rgba(255, 255, 255, 0.65)';

        for (const particle of particles) {
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.r, 0, Math.PI * 2);
            ctx.fill();

            particle.y += particle.v;
            particle.x += particle.drift;

            if (particle.y > height + 5) {
                particle.y = -5;
                particle.x = Math.random() * width;
            }

            if (particle.x < -5) {
                particle.x = width + 5;
            } else if (particle.x > width + 5) {
                particle.x = -5;
            }
        }

        animationId = requestAnimationFrame(draw);
    }

    function startSnow() {
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            isSnowing = false;
            return;
        }

        isSnowing = true;

        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:100;';
            document.body.appendChild(canvas);
            ctx = canvas.getContext('2d');
        }

        if (!resizeAttached) {
            window.addEventListener('resize', resize, { passive: true });
            resizeAttached = true;
        }

        resize();
        buildParticles();

        if (!animationId) {
            animationId = requestAnimationFrame(draw);
        }
    }

    function stopSnow() {
        isSnowing = false;

        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }

        particles = [];

        if (resizeAttached) {
            window.removeEventListener('resize', resize);
            resizeAttached = false;
        }

        if (canvas) {
            canvas.remove();
            canvas = null;
            ctx = null;
        }
    }

    function handleVisibilityChange() {
        if (!isSnowing) {
            return;
        }

        if (document.hidden) {
            if (animationId) {
                cancelAnimationFrame(animationId);
                animationId = null;
            }
        } else if (!animationId) {
            animationId = requestAnimationFrame(draw);
        }
    }

    function updateSnowButtonState(button, snowEnabled) {
        const icon = document.createElement('span');
        icon.className = 'material-icons';
        icon.setAttribute('aria-hidden', 'true');
        icon.textContent = 'ac_unit';

        button.replaceChildren(
            icon,
            document.createTextNode(snowEnabled ? ' Disable Snow' : ' Enable Snow')
        );

        button.setAttribute('aria-pressed', snowEnabled ? 'true' : 'false');
        button.setAttribute(
            'aria-label',
            snowEnabled ? 'Disable snow effect' : 'Enable snow effect'
        );
    }

    function createSnowButton() {
        const controls = document.querySelector('.controls');
        if (!controls) {
            return null;
        }

        const existingButton = document.getElementById(BTN_ID);
        if (existingButton) {
            return existingButton;
        }

        const button = document.createElement('button');
        button.className = BTN_CLASS;
        button.id = BTN_ID;
        button.type = 'button';
        button.style.marginLeft = '0.5rem';
        controls.appendChild(button);
        return button;
    }

    function init() {
        document.addEventListener('visibilitychange', handleVisibilityChange);

        const persistedState = textUtilsStorage.get(STORAGE_KEY) === 'true';
        if (persistedState) {
            startSnow();
        }

        const button = createSnowButton();
        if (!button) {
            return;
        }

        updateSnowButtonState(button, isSnowing);
        button.addEventListener('click', () => {
            if (isSnowing) {
                stopSnow();
            } else {
                startSnow();
            }

            textUtilsStorage.set(STORAGE_KEY, isSnowing ? 'true' : 'false');
            updateSnowButtonState(button, isSnowing);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
