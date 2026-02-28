/**
 * ANNA Financial Platform - Theme Manager
 *
 * Handles professional light/dark/auto theme switching.
 * - Integrates with Bootstrap 5.3+ via data-bs-theme.
 * - Persists user choice in localStorage.
 * - Updates toggle icons dynamically.
 */

(function() {
    'use strict';

    const THEME_STORAGE_KEY = 'anna_theme';
    const THEME_ATTR = 'data-bs-theme'; // Use Bootstrap's native attribute

    const getSystemTheme = () =>
        window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';

    const getStoredTheme = () => localStorage.getItem(THEME_STORAGE_KEY) || 'auto';

    const setStoredTheme = (theme) => localStorage.setItem(THEME_STORAGE_KEY, theme);

    /**
     * Updates the theme toggle icon to reflect the current setting.
     * @param {string} theme - The user's selected theme setting (light, dark, auto)
     */
    const updateIcon = (theme) => {
        const toggleBtn = document.querySelector('.theme-toggle i');
        if (!toggleBtn) return;
        
        // Remove existing bi-* classes
        toggleBtn.className = Array.from(toggleBtn.classList)
            .filter(c => !c.startsWith('bi-'))
            .join(' ') + ' bi';
            
        if (theme === 'light') {
            toggleBtn.classList.add('bi-sun-fill');
        } else if (theme === 'dark') {
            toggleBtn.classList.add('bi-moon-stars-fill');
        } else {
            toggleBtn.classList.add('bi-circle-half');
        }
    };

    /**
     * Applies the given theme to the document root and updates the stored theme.
     * @param {string} theme - The theme to apply ('light', 'dark', or 'auto').
     */
    const applyTheme = (theme) => {
        let effectiveTheme = theme;
        if (theme === 'auto') {
            effectiveTheme = getSystemTheme();
        }
        document.documentElement.setAttribute(THEME_ATTR, effectiveTheme);
        // Also set data-theme for legacy compatibility during transition
        document.documentElement.setAttribute('data-theme', effectiveTheme);
        updateIcon(theme);
    };

    /**
     * Toggles through the available themes: auto -> light -> dark -> auto.
     */
    const cycleTheme = () => {
        const currentTheme = getStoredTheme();
        let nextTheme;

        if (currentTheme === 'auto') {
            nextTheme = 'light';
        } else if (currentTheme === 'light') {
            nextTheme = 'dark';
        } else {
            nextTheme = 'auto';
        }
        
        setStoredTheme(nextTheme);
        applyTheme(nextTheme);
    };

    // --- Initialization ---

    // Apply theme immediately to prevent FOUC
    applyTheme(getStoredTheme());

    // Listen for DOMContentLoaded to attach event listeners
    window.addEventListener('DOMContentLoaded', () => {
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', cycleTheme);
            // Ensure correct initial icon is set
            updateIcon(getStoredTheme());
        }
    });

    // Listen for changes in the system's color scheme
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (getStoredTheme() === 'auto') {
            applyTheme('auto');
        }
    });

})();
