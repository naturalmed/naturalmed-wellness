/**
 * NaturalMed CMS Auth — Cloudflare Worker
 * OAuth proxy for Sveltia CMS + GitHub
 *
 * Based on: https://github.com/sveltia/sveltia-cms-auth
 *
 * Environment variables (set in Cloudflare dashboard → Worker → Settings → Variables):
 *   GITHUB_CLIENT_ID      — from your GitHub OAuth App
 *   GITHUB_CLIENT_SECRET  — from your GitHub OAuth App
 *   ALLOWED_DOMAINS       — www.naturalmed-wellness.com
 */

const GITHUB_AUTH_URL  = 'https://github.com/login/oauth/authorize';
const GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token';
const ALLOWED_DOMAINS  = ['www.naturalmed-wellness.com', 'localhost:8080'];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ── CORS preflight ──────────────────────────────────────
    if (request.method === 'OPTIONS') {
      return corsResponse('', 204);
    }

    // ── Step 1: Redirect to GitHub OAuth ───────────────────
    if (url.pathname === '/auth') {
      const origin = url.searchParams.get('origin') || '';
      const domain = new URL(origin || 'https://www.naturalmed-wellness.com').hostname;

      if (!ALLOWED_DOMAINS.some(d => domain === d || domain.endsWith('.' + d))) {
        return corsResponse('Unauthorized domain: ' + domain, 403);
      }

      const params = new URLSearchParams({
        client_id:    env.GITHUB_CLIENT_ID,
        scope:        'repo,user',
        state:        btoa(JSON.stringify({ origin })),
        redirect_uri: `${url.origin}/callback`,
      });

      return Response.redirect(`${GITHUB_AUTH_URL}?${params}`, 302);
    }

    // ── Step 2: Handle OAuth callback from GitHub ───────────
    if (url.pathname === '/callback') {
      const code  = url.searchParams.get('code');
      const state = url.searchParams.get('state');

      if (!code) {
        return corsResponse('Missing code parameter', 400);
      }

      let origin = 'https://www.naturalmed-wellness.com';
      try {
        const decoded = JSON.parse(atob(state || ''));
        origin = decoded.origin || origin;
      } catch (_) {}

      // Exchange code for access token
      const tokenResp = await fetch(GITHUB_TOKEN_URL, {
        method:  'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept':       'application/json',
        },
        body: JSON.stringify({
          client_id:     env.GITHUB_CLIENT_ID,
          client_secret: env.GITHUB_CLIENT_SECRET,
          code,
          redirect_uri:  `${url.origin}/callback`,
        }),
      });

      const tokenData = await tokenResp.json();

      if (tokenData.error) {
        return corsResponse('GitHub error: ' + tokenData.error_description, 400);
      }

      // Return token to the CMS via postMessage
      const html = `<!DOCTYPE html>
<html>
<head><title>NaturalMed CMS — Authenticating…</title></head>
<body>
<script>
  (function() {
    var token = ${JSON.stringify(tokenData.access_token)};
    var provider = 'github';
    var origin   = ${JSON.stringify(origin)};
    // Post message back to the CMS window
    if (window.opener) {
      window.opener.postMessage(
        'authorization:' + provider + ':success:' + JSON.stringify({ token: token, provider: provider }),
        origin
      );
    }
    window.close();
  })();
</script>
<p>Authentication successful — you can close this window.</p>
</body>
</html>`;

      return new Response(html, {
        headers: { 'Content-Type': 'text/html;charset=UTF-8' },
      });
    }

    // ── Health check ────────────────────────────────────────
    if (url.pathname === '/') {
      return corsResponse('NaturalMed CMS Auth Worker is running ✓', 200);
    }

    return corsResponse('Not found', 404);
  },
};

function corsResponse(body, status = 200) {
  return new Response(body, {
    status,
    headers: {
      'Access-Control-Allow-Origin':  '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Content-Type': 'text/plain;charset=UTF-8',
    },
  });
}
