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

// Texts of the banner and settings panel, by page language (PT for /pt/..., EN elsewhere).
const NM_COOKIE_TEXTS = {
    en: {
        bannerTitle: '🍪 Cookie Preferences',
        bannerText: 'We use essential cookies to make this site work. With your permission we may also use analytics cookies to help us improve it.',
        bannerPolicy: 'Read our {link} for full details.',
        policy: 'Privacy Policy',
        customise: '⚙️ Customise',
        essentialOnly: 'Essential Only',
        acceptAll: 'Accept All',
        panelTitle: 'Cookie Preferences',
        panelIntro: 'Manage which cookies NaturalMed may store on your device. Essential cookies cannot be disabled as the site needs them to function.',
        essentialName: 'Essential',
        essentialDesc: 'Required for the website to function. Includes your cookie-consent preference. Cannot be disabled.',
        analyticsName: 'Analytics',
        analyticsDesc: 'Help us understand how visitors use the site so we can improve it. All data is anonymised.',
        alwaysActive: 'Always Active',
        cancel: 'Cancel',
        save: 'Save Preferences'
    },
    pt: {
        bannerTitle: '🍪 Preferências de Cookies',
        bannerText: 'Usamos cookies essenciais para que este site funcione. Com a sua autorização, podemos também usar cookies de análise para nos ajudar a melhorá-lo.',
        bannerPolicy: 'Leia a nossa {link} para mais pormenores.',
        policy: 'Política de Privacidade',
        customise: '⚙️ Personalizar',
        essentialOnly: 'Só Essenciais',
        acceptAll: 'Aceitar Todos',
        panelTitle: 'Preferências de Cookies',
        panelIntro: 'Escolha que cookies a NaturalMed pode guardar no seu dispositivo. Os cookies essenciais não podem ser desativados, porque o site precisa deles para funcionar.',
        essentialName: 'Essenciais',
        essentialDesc: 'Necessários para o funcionamento do site. Incluem a sua preferência de cookies. Não podem ser desativados.',
        analyticsName: 'Análise',
        analyticsDesc: 'Ajudam-nos a perceber como os visitantes usam o site, para o podermos melhorar. Todos os dados são anonimizados.',
        alwaysActive: 'Sempre Ativos',
        cancel: 'Cancelar',
        save: 'Guardar Preferências'
    }
};

function nmCookieLang() {
    const path = (window.location && window.location.pathname) || '/';
    return /^\/pt(\/|$)/.test(path) ? 'pt' : 'en';
}

class CookieConsentManager {
    constructor(config = {}) {
        this.t = NM_COOKIE_TEXTS[nmCookieLang()];
        this.config = {
            cookieName: 'nm_cookie_consent',
            cookieExpiry: 365,       // days
            version: '1.0',          // bump to force re-consent after policy changes
            onConsentChange: config.onConsentChange || null,
            categories: {
                essential: {
                    name: this.t.essentialName,
                    description: this.t.essentialDesc,
                    required: true,
                    enabled: true
                },
                analytics: {
                    name: this.t.analyticsName,
                    description: this.t.analyticsDesc,
                    required: false,
                    enabled: false,
                    // Google Analytics only ever loads through this consent gate (never from the
                    // page <head>). Pages may pass their own list; otherwise the site's GA4 tag is used.
                    scripts: (config.analyticsScripts && config.analyticsScripts.length)
                        ? config.analyticsScripts
                        : [{ type: 'gtag', id: 'G-5175TWZGHK' }]
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
        if (this._gaLoaded) return;   // never load the tag twice on the same page
        this._gaLoaded = true;
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

    // The privacy page depends on the page language, not on the folder depth: a relative
    // "privacy.html" broke on /pt/, /en/articles/ and /pt/artigos/ (404 in Search Console).
    privacyUrl() {
        const path = (window.location && window.location.pathname) || '/';
        return nmCookieLang() === 'pt' ? '/pt/privacidade.html' : '/en/privacy.html';
    }

    showBanner() {
        this.hideBanner();
        const banner = document.createElement('div');
        banner.id = 'cookie-consent-banner';
        banner.className = 'cookie-consent-banner';
        banner.innerHTML = `
            <div class="cookie-consent-content">
                <div class="cookie-consent-text">
                    <h3>${this.t.bannerTitle}</h3>
                    <p>${this.t.bannerText}
                    ${this.t.bannerPolicy.replace('{link}', `<a href="${this.privacyUrl()}">${this.t.policy}</a>`)}</p>
                </div>
                <div class="cookie-consent-buttons">
                    <button class="cookie-btn cookie-btn-settings" onclick="cookieConsent.showSettings()">${this.t.customise}</button>
                    <button class="cookie-btn cookie-btn-reject"   onclick="cookieConsent.rejectNonEssential()">${this.t.essentialOnly}</button>
                    <button class="cookie-btn cookie-btn-accept"   onclick="cookieConsent.acceptAll()">${this.t.acceptAll}</button>
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
                    <h2>${this.t.panelTitle}</h2>
                    <button class="cookie-settings-close" onclick="cookieConsent.hideSettings()">✕</button>
                </div>
                <div class="cookie-settings-body">
                    <p class="cookie-settings-intro">
                        ${this.t.panelIntro}
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
                            <span class="cookie-badge cookie-badge-required">${this.t.alwaysActive}</span>
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
                    <a href="${this.privacyUrl()}">📄 ${this.t.policy}</a>
                    <button class="cookie-btn cookie-btn-secondary" onclick="cookieConsent.hideSettings()">${this.t.cancel}</button>
                    <button class="cookie-btn cookie-btn-primary"   onclick="cookieConsent.saveFromSettings()">${this.t.save}</button>
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

// Pages that include this file but do not start the manager themselves get one automatically,
// so the banner - and the consent gate for Analytics - works on every page.
document.addEventListener('DOMContentLoaded', function () {
    if (typeof cookieConsent === 'undefined' && !window.cookieConsent) {
        window.cookieConsent = new CookieConsentManager();
    }
});
