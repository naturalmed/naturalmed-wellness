/**
 * NaturalMed — GDPR Cookie Consent Manager
 * Compliant with EU GDPR / UK GDPR (post-Brexit)
 *
 * Third-party services that set cookies on this site:
 *   - Google Calendar embed (contact.html) — always shown, no personal data stored by NaturalMed
 *   - Google Analytics — only loaded after explicit consent
 *
 * LOAD ORDER: this file must be the FIRST script on every page,
 * before any analytics or other third-party scripts.
 */

class CookieConsentManager {
    constructor(config = {}) {
        this.config = {
            cookieName: 'nm_cookie_consent',
            cookieExpiry: 365,       // days
            version: '1.0',          // bump to force re-consent after policy changes
            onConsentChange: config.onConsentChange || null,
            categories: {
                essential: {
                    name: 'Essential',
                    description: 'Required for the website to function. Includes your cookie-consent preference. Cannot be disabled.',
                    required: true,
                    enabled: true
                },
                analytics: {
                    name: 'Analytics',
                    description: 'Help us understand how visitors use the site so we can improve it. All data is anonymised.',
                    required: false,
                    enabled: false,
                    scripts: config.analyticsScripts || []
                }
            }
        };

        this.consent = this.loadConsent();
        this.init();
    }

    init() {
        if (!this.consent || this.consent.version !== this.config.version) {
            this.showBanner();
        } else {
            this.applyConsent();
        }
        this.attachSettingsTriggers();
    }

    loadConsent() {
        try {
            const cookie = document.cookie
                .split('; ')
                .find(row => row.startsWith(this.config.cookieName + '='));
            if (cookie) return JSON.parse(decodeURIComponent(cookie.split('=')[1]));
        } catch (e) { /* ignore */ }
        return null;
    }

    saveConsent(preferences) {
        const consent = {
            version: this.config.version,
            timestamp: new Date().toISOString(),
            preferences: preferences
        };
        const expires = new Date();
        expires.setDate(expires.getDate() + this.config.cookieExpiry);
        document.cookie = `${this.config.cookieName}=${encodeURIComponent(JSON.stringify(consent))}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`;
        this.consent = consent;
        return consent;
    }

    applyConsent() {
        const prefs = this.consent.preferences;
        if (prefs.analytics && this.config.categories.analytics.scripts.length > 0) {
            this.loadAnalyticsScripts();
        }
        if (this.config.onConsentChange) this.config.onConsentChange(prefs);
    }

    loadAnalyticsScripts() {
        this.config.categories.analytics.scripts.forEach(s => {
            if (s.type === 'gtag') this.loadGoogleAnalytics(s.id);
            else if (s.type === 'custom') this.loadCustomScript(s.src);
        });
    }

    loadGoogleAnalytics(measurementId) {
        const script = document.createElement('script');
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`;
        document.head.appendChild(script);
        window.dataLayer = window.dataLayer || [];
        function gtag(){ dataLayer.push(arguments); }
        window.gtag = gtag;
        gtag('js', new Date());
        gtag('config', measurementId, { anonymize_ip: true, cookie_flags: 'SameSite=None;Secure' });
    }

    loadCustomScript(src) {
        const script = document.createElement('script');
        script.src = src; script.async = true;
        document.head.appendChild(script);
    }

    acceptAll() {
        this.saveConsent({ essential: true, analytics: true });
        this.applyConsent();
        this.hideBanner();
    }

    acceptSelected(preferences) {
        preferences.essential = true;
        this.saveConsent(preferences);
        this.applyConsent();
        this.hideSettings();
        this.hideBanner();
    }

    rejectNonEssential() {
        this.saveConsent({ essential: true, analytics: false });
        this.hideBanner();
    }

    showBanner() {
        this.hideBanner();
        const banner = document.createElement('div');
        banner.id = 'cookie-consent-banner';
        banner.className = 'cookie-consent-banner';
        banner.innerHTML = `
            <div class="cookie-consent-content">
                <div class="cookie-consent-text">
                    <h3>🍪 Cookie Preferences</h3>
                    <p>We use essential cookies to make this site work. With your permission we may also use analytics cookies to help us improve it.
                    Read our <a href="privacy.html">Privacy Policy</a> for full details.</p>
                </div>
                <div class="cookie-consent-buttons">
                    <button class="cookie-btn cookie-btn-settings" onclick="cookieConsent.showSettings()">⚙️ Customise</button>
                    <button class="cookie-btn cookie-btn-reject"   onclick="cookieConsent.rejectNonEssential()">Essential Only</button>
                    <button class="cookie-btn cookie-btn-accept"   onclick="cookieConsent.acceptAll()">Accept All</button>
                </div>
            </div>`;
        document.body.appendChild(banner);
        setTimeout(() => banner.classList.add('show'), 10);
    }

    hideBanner() {
        const el = document.getElementById('cookie-consent-banner');
        if (el) { el.classList.remove('show'); setTimeout(() => el.remove(), 350); }
    }

    showSettings() {
        this.hideSettings();
        const prefs = this.consent?.preferences || { essential: true, analytics: false };
        const panel = document.createElement('div');
        panel.id = 'cookie-settings-panel';
        panel.className = 'cookie-settings-panel';
        panel.innerHTML = `
            <div class="cookie-settings-overlay" onclick="cookieConsent.hideSettings()"></div>
            <div class="cookie-settings-content">
                <div class="cookie-settings-header">
                    <h2>Cookie Preferences</h2>
                    <button class="cookie-settings-close" onclick="cookieConsent.hideSettings()">✕</button>
                </div>
                <div class="cookie-settings-body">
                    <p class="cookie-settings-intro">
                        Manage which cookies NaturalMed may store on your device.
                        Essential cookies cannot be disabled as the site needs them to function.
                    </p>
                    <div class="cookie-category">
                        <div class="cookie-category-header">
                            <div>
                                <h3>${this.config.categories.essential.name}</h3>
                                <p>${this.config.categories.essential.description}</p>
                            </div>
                            <label class="cookie-toggle">
                                <input type="checkbox" checked disabled>
                                <span class="cookie-toggle-slider"></span>
                            </label>
                        </div>
                        <div class="cookie-category-info">
                            <span class="cookie-badge cookie-badge-required">Always Active</span>
                        </div>
                    </div>
                    <div class="cookie-category">
                        <div class="cookie-category-header">
                            <div>
                                <h3>${this.config.categories.analytics.name}</h3>
                                <p>${this.config.categories.analytics.description}</p>
                            </div>
                            <label class="cookie-toggle">
                                <input type="checkbox" id="nm-analytics-toggle" ${prefs.analytics ? 'checked' : ''}>
                                <span class="cookie-toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
                <div class="cookie-settings-footer">
                    <a href="privacy.html">📄 Privacy Policy</a>
                    <button class="cookie-btn cookie-btn-secondary" onclick="cookieConsent.hideSettings()">Cancel</button>
                    <button class="cookie-btn cookie-btn-primary"   onclick="cookieConsent.saveFromSettings()">Save Preferences</button>
                </div>
            </div>`;
        document.body.appendChild(panel);
        setTimeout(() => panel.classList.add('show'), 10);
    }

    hideSettings() {
        const el = document.getElementById('cookie-settings-panel');
        if (el) { el.classList.remove('show'); setTimeout(() => el.remove(), 350); }
    }

    saveFromSettings() {
        const toggle = document.getElementById('nm-analytics-toggle');
        this.acceptSelected({ essential: true, analytics: toggle ? toggle.checked : false });
    }

    attachSettingsTriggers() {
        document.addEventListener('click', e => {
            if (e.target.matches('[data-cookie-settings]') || e.target.closest('[data-cookie-settings]')) {
                e.preventDefault();
                this.showSettings();
            }
        });
    }

    hasConsent(category) {
        return this.consent ? this.consent.preferences[category] === true : false;
    }

    revokeConsent() {
        document.cookie = `${this.config.cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        ['_ga','_gid','_gat'].forEach(name => {
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
            const domain = window.location.hostname.split('.').slice(-2).join('.');
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.${domain}`;
        });
        this.consent = null;
        this.showBanner();
    }
}

window.CookieConsentManager = CookieConsentManager;
