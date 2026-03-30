'use strict';
/* ============================================================
   naturalmed-flyer.js
   Generates the NaturalMed clinic PDF flyer when the user
   clicks "Take a Flyer With You".
   Requires: jsPDF 2.5.x, QRCode.js (both loaded via CDN)
   ============================================================ */

// ── Image loading ─────────────────────────────────────────────────────────────
function imgToDataURL(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = function () {
      const cv = document.createElement('canvas');
      cv.width  = img.naturalWidth  || img.width;
      cv.height = img.naturalHeight || img.height;
      cv.getContext('2d').drawImage(img, 0, 0);
      const mime = src.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
      resolve(cv.toDataURL(mime, 0.92));
    };
    img.onerror = () => reject(new Error('Cannot load image: ' + src));
    // Add timestamp to avoid cached opaque responses blocking crossOrigin
    img.src = src + (src.includes('?') ? '&' : '?') + '_t=' + Date.now();
  });
}

// ── QR code generation ────────────────────────────────────────────────────────
function qrToDataURL(url, size) {
  size = size || 300;
  return new Promise(function (resolve) {
    var wrap = document.createElement('div');
    wrap.style.cssText = 'position:fixed;top:-9999px;left:-9999px;visibility:hidden;';
    document.body.appendChild(wrap);
    /* QRCode.js renders a <canvas> when canvas is available */
    new QRCode(wrap, {
      text:         url,
      width:        size,
      height:       size,
      colorDark:    '#000000',
      colorLight:   '#ffffff',
      correctLevel: QRCode.CorrectLevel.H
    });
    /* Allow the library a tick to finish rendering */
    setTimeout(function () {
      var cv = wrap.querySelector('canvas');
      var data = cv ? cv.toDataURL('image/png') : null;
      document.body.removeChild(wrap);
      resolve(data);
    }, 600);
  });
}

// ── Clip an image to a rounded rectangle ─────────────────────────────────────
// Uses PDF path operators (moveTo / lineTo / curveTo) + clip().
// Falls back to an unclipped rectangle if anything fails.
function addClippedImage(doc, dataURL, fmt, x, y, w, h, r) {
  var k = 0.5523; // cubic-Bézier approximation of a quarter-circle
  try {
    doc.saveGraphicsState();
    // Build rounded-rect path
    doc.moveTo(x + r,     y);
    doc.lineTo(x + w - r, y);
    doc.curveTo(x + w - r + r*k, y,              x + w, y + r - r*k,           x + w, y + r);
    doc.lineTo(x + w, y + h - r);
    doc.curveTo(x + w, y + h - r + r*k,          x + w - r + r*k, y + h,       x + w - r, y + h);
    doc.lineTo(x + r, y + h);
    doc.curveTo(x + r - r*k, y + h,              x, y + h - r + r*k,           x, y + h - r);
    doc.lineTo(x, y + r);
    doc.curveTo(x, y + r - r*k,                  x + r - r*k, y,               x + r, y);
    doc.clip('nonzero');
    doc.discardPath();
    doc.addImage(dataURL, fmt, x, y, w, h);
    doc.restoreGraphicsState();
  } catch (e) {
    // Fallback: draw without clipping
    try { doc.restoreGraphicsState(); } catch (_) {}
    doc.addImage(dataURL, fmt, x, y, w, h);
  }
}

// ── Helper: detect format from data URL ──────────────────────────────────────
function fmtOf(dataURL) {
  return (dataURL || '').startsWith('data:image/png') ? 'PNG' : 'JPEG';
}

// ── Main entry point ─────────────────────────────────────────────────────────
async function generateFlyer() {
  var btn = document.getElementById('flyerBtn');
  var origHTML = btn ? btn.innerHTML : '';
  if (btn) { btn.disabled = true; btn.innerHTML = '<span style="opacity:.7">⏳ Generating PDF…</span>'; }

  try {
    // 1. Load all assets in parallel (failures are non-fatal for images)
    var results = await Promise.allSettled([
      imgToDataURL('../assets/img/nuno-photo.png'),
      imgToDataURL('../assets/img/naturalmed-needles.jpg'),
      imgToDataURL('../assets/img/naturalmed-office.jpg'),
      qrToDataURL('https://www.naturalmed-wellness.com', 320),
      imgToDataURL('../assets/img/naturalmed-logo.png'),
    ]);

    var nunoData    = results[0].status === 'fulfilled' ? results[0].value : null;
    var needlesData = results[1].status === 'fulfilled' ? results[1].value : null;
    var officeData  = results[2].status === 'fulfilled' ? results[2].value : null;
    var qrData      = results[3].status === 'fulfilled' ? results[3].value : null;
    var logoData    = results[4].status === 'fulfilled' ? results[4].value : null;

    // 2. Instantiate jsPDF (A4, portrait, points)
    var jsPDF = window.jspdf.jsPDF;
    var doc   = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'a4' });

    var W = 595.28, H = 841.89;

    // ── Shorthand helpers ────────────────────────────────────────────────
    function fg(r, g, b) { doc.setFillColor(r, g, b); }
    function sg(r, g, b) { doc.setDrawColor(r, g, b); }
    function tc(r, g, b) { doc.setTextColor(r, g, b); }
    function lw(n)       { doc.setLineWidth(n); }
    function fnt(style, size) { doc.setFont('helvetica', style); doc.setFontSize(size); }
    function frect(x, y, w, h) { doc.rect(x, y, w, h, 'F'); }

    // ── Palette (RGB 0-255) ──────────────────────────────────────────────
    // Each entry: [R, G, B]
    var darkGreen      = [5,   51,  43 ];
    var lightGreenBg   = [199, 219, 209];
    var mediumGreen    = [181, 199, 191];
    var veryLightGreen = [224, 245, 237];
    var lightGreenTxt  = [93,  202, 165];
    var darkGreenTxt   = [4,   52,  44 ];
    var tealTxt        = [45,  74,  62 ];
    var gold           = [186, 117, 23 ];
    var white          = [255, 255, 255];
    var black          = [0,   0,   0  ];

    // ── OFFSET: extra vertical space added below header ──────────────────
    var OFFSET = 50;
    var CORNER = 10;   // rounded-corner radius for boxes

    // ════════════════════════════════════════════════════════════════════
    // SECTION 1 — HEADER
    // ════════════════════════════════════════════════════════════════════
    fg(...darkGreen); frect(0, 0, W, 90.7);

    // NM logo badge — use real logo if available, else NM text
    var badgeX = 39.7, badgeY = 17.0, badgeW = 45.3, badgeH = 45.4;
    fg(...veryLightGreen); lw(0.5);
    doc.roundedRect(badgeX, badgeY, badgeW, badgeH, 5, 5, 'F');

    if (logoData) {
      addClippedImage(doc, logoData, 'PNG', badgeX, badgeY, badgeW, badgeH, 5);
    } else {
      fnt('bold', 10); tc(...darkGreenTxt);
      doc.text('NM', badgeX + badgeW / 2, badgeY + badgeH / 2 + 3.5, { align: 'center' });
    }

    // "NaturalMed"
    fnt('bold', 18); tc(...white);
    doc.text('NaturalMed', 102, 25.4 + 14);

    // "Wellness"
    fnt('normal', 8.5); tc(...veryLightGreen);
    doc.text('Wellness', 102, 47.1 + 7);

    // Website & location (right-aligned)
    tc(...veryLightGreen);
    fnt('normal', 7.5);
    doc.text('www.naturalmed-wellness.com', W - 28, 33.7 + 6, { align: 'right' });
    fnt('normal', 7.0);
    doc.text('Mid-Wales, United Kingdom',   W - 28, 48.3 + 5, { align: 'right' });

    // ════════════════════════════════════════════════════════════════════
    // SECTION 2 — THREE IMAGE BOXES
    // ════════════════════════════════════════════════════════════════════
    var BT  = 102   + OFFSET;   // boxes top    = 152
    var BB  = 323.1 + OFFSET;   // boxes bottom = 373.1
    var LX  = 134.64, LW = 164.4, LH = BB - BT;
    var RX  = LX + LW + 14.2,  RW = 147.4;
    var RUT = BT,             RUB = 208.3 + OFFSET;  // right-upper box
    var RLT = 216.9 + OFFSET, RLB = BB;              // right-lower box
    var RUH = RUB - RUT, RLH = RLB - RLT;

    // ── drawBox: image + clipped label band + gold border ───────────────
    function drawBox(imgData, x, y, w, h, label) {
      var r = CORNER;
      var k = 0.5523; // Bézier quarter-circle approximation
      var bandH = 22;

      // Build the rounded-rect clip path
      function setClipPath() {
        doc.moveTo(x + r, y);
        doc.lineTo(x + w - r, y);
        doc.curveTo(x + w - r + r*k, y,       x + w, y + r - r*k,           x + w, y + r);
        doc.lineTo(x + w, y + h - r);
        doc.curveTo(x + w, y + h - r + r*k,   x + w - r + r*k, y + h,       x + w - r, y + h);
        doc.lineTo(x + r, y + h);
        doc.curveTo(x + r - r*k, y + h,       x, y + h - r + r*k,           x, y + h - r);
        doc.lineTo(x, y + r);
        doc.curveTo(x, y + r - r*k,           x + r - r*k, y,               x + r, y);
      }

      // Clip everything (image + band) to the rounded rect
      doc.saveGraphicsState();
      setClipPath();
      doc.clip('nonzero');
      doc.discardPath();

      if (imgData) {
        doc.addImage(imgData, fmtOf(imgData), x, y, w, h);
      } else {
        fg(...lightGreenBg); frect(x, y, w, h);
      }

      // Dark band at bottom — corners now clipped cleanly
      fg(...darkGreen);
      frect(x, y + h - bandH, w, bandH);

      doc.restoreGraphicsState();

      // Gold border drawn AFTER restoring state so it sits on top
      sg(...gold); lw(2.27);
      doc.roundedRect(x, y, w, h, r, r, 'S');

      // White label text centred in band
      fnt('bold', 8); tc(...white);
      doc.text(label, x + w / 2, y + h - bandH / 2 + 3, { align: 'center' });
    }

    drawBox(nunoData,    LX, BT,  LW, LH,  'Nuno Pestana');
    drawBox(needlesData, RX, RUT, RW, RUH, 'Acupuncture');
    drawBox(officeData,  RX, RLT, RW, RLH, 'Clinic');

    // ════════════════════════════════════════════════════════════════════
    // SECTION 3 — SERVICES BANNER (dark green strip)
    // ════════════════════════════════════════════════════════════════════
    var banT = 334.5 + OFFSET, banB = 385.5 + OFFSET, banH = banB - banT;
    fg(...darkGreen); frect(0, banT, W, banH);
    fnt('bold', 12); tc(...white);
    doc.text(
      'TRADITIONAL CHINESE MEDICINE · MID-WALES, UK',
      W / 2, banT + banH / 2 + 4.5, { align: 'center' }
    );

    // ════════════════════════════════════════════════════════════════════
    // SECTION 4 — BODY TEXT
    // ════════════════════════════════════════════════════════════════════
    fnt('normal', 9.5); tc(...tealTxt);
    var bodyLines = [
      'Acupuncture, herbal medicine and holistic care in Newtown, Powys — rooted in authentic Chinese',
      'medical tradition from Chengdu University. Nuno Pestana (BSc TCM, Member ATCM UK) has over',
      '10 years of clinical experience treating pain, fertility, digestive and sleep conditions.',
    ];
    var bodyTops = [412 + OFFSET, 427.2 + OFFSET, 442.4 + OFFSET];
    bodyLines.forEach(function (line, i) {
      doc.text(line, W / 2, bodyTops[i] + 7.5, { align: 'center' });
    });

    // ════════════════════════════════════════════════════════════════════
    // SECTION 5 — SERVICE PILLS
    // ════════════════════════════════════════════════════════════════════
    var services = ['Acupuncture', 'Herbal Medicine', 'Tuina Massage', 'Chinese Dietetics', 'Online Consultations'];
    var px0s = [45.4, 147.4, 249.4, 351.5, 453.5];
    var px1s = [141.7, 243.8, 345.8, 447.9, 549.9];
    var pillTop = 467.7 + OFFSET, pillBot = 487.6 + OFFSET;
    var pillH   = pillBot - pillTop;

    services.forEach(function (svc, i) {
      var px = px0s[i], pw = px1s[i] - px0s[i];
      fg(...veryLightGreen); sg(...darkGreenTxt); lw(0.85);
      doc.roundedRect(px, pillTop, pw, pillH, 4, 4, 'FD');
      fnt('normal', 6.5); tc(...darkGreenTxt);
      doc.text(svc, px + pw / 2, pillTop + pillH / 2 + 2.5, { align: 'center' });
    });

    // ════════════════════════════════════════════════════════════════════
    // SECTION 6 — FOOTER
    // ════════════════════════════════════════════════════════════════════
    var footTop = 694.5;
    fg(...darkGreen); frect(0, footTop, W, H - footTop);

    // ── QR code box ──────────────────────────────────────────────────────
    var qrX = 462, qrY = 714.3, qrW = 96.4, qrH = 96.4;
    var margin = 5;

    // Outer black square
    fg(...black); frect(qrX, qrY, qrW, qrH);

    if (qrData) {
      // White inner area + actual QR image
      fg(...white);
      frect(qrX + margin, qrY + margin, qrW - margin * 2, qrH - margin * 2);
      doc.addImage(
        qrData, 'PNG',
        qrX + margin, qrY + margin,
        qrW - margin * 2, qrH - margin * 2
      );
    }

    // White border around the square
    sg(...white); lw(2.5);
    doc.rect(qrX, qrY, qrW, qrH, 'S');

    // "Scan to visit website"
    fnt('normal', 6); tc(...lightGreenTxt);
    doc.text('Scan to visit website', qrX + qrW / 2, 814.5 + 5, { align: 'center' });

    // ── Contact details ───────────────────────────────────────────────────
    var lx = 39.7;

    fnt('bold', 9); tc(...gold);
    doc.text('CONTACTS', lx, 716 + 7.5);

    fnt('normal', 7.5); tc(...white);
    doc.text('Email:   naturalmed.wellness@gmail.com',                              lx, 742 + 6);
    doc.text('Phone:  +44 7756 339 382',                                            lx, 765 + 6);
    doc.text('Clinic:   30 Shortbridge Street, Newtown, Powys, SY16 2LN — Mid-Wales, UK', lx, 788 + 6);

    fnt('normal', 6.5); tc(...lightGreenTxt);
    doc.text('Member — Association of Traditional Chinese Medicine UK (ATCM)', lx, 810 + 5);

    fnt('normal', 6);
    doc.text('© 2026 NaturalMed · naturalmed.wellness', W / 2, 829, { align: 'center' });

    // ── Save ──────────────────────────────────────────────────────────────
    doc.save('NaturalMed-Flyer.pdf');

  } catch (err) {
    console.error('Flyer generation failed:', err);
    alert('Could not generate the flyer.\n' + err.message);
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = origHTML; }
  }
}
