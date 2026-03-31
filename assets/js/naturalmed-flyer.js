/* naturalmed-flyer.js — PDF flyer generator
   Requires: jsPDF CDN + flyer-images.js loaded before this file
   Version 3 — robust jsPDF detection + unique image aliases          */

function generateFlyer() {
    var btn = document.getElementById('flyerBtn');
    if (!btn) return;
    var origText = btn.textContent;
    btn.textContent = 'Generating…';
    btn.disabled = true;

    setTimeout(function () {
        try {

            /* ── 1. Resolve jsPDF constructor ─────────────────────── */
            var JsPDF = null;
            if (window.jspdf && typeof window.jspdf.jsPDF === 'function') {
                JsPDF = window.jspdf.jsPDF;                  // v2.x UMD
            } else if (typeof window.jsPDF === 'function') {
                JsPDF = window.jsPDF;                        // v1.x
            }
            if (!JsPDF) {
                throw new Error('PDF library (jsPDF) not loaded. Please refresh the page and try again.');
            }

            /* ── 2. Verify all image variables exist ──────────────── */
            var logo    = (typeof LOGO_B64    !== 'undefined') ? LOGO_B64    : null;
            var nuno    = (typeof NUNO_B64    !== 'undefined') ? NUNO_B64    : null;
            var needles = (typeof NEEDLES_B64 !== 'undefined') ? NEEDLES_B64 : null;
            var office  = (typeof OFFICE_B64  !== 'undefined') ? OFFICE_B64  : null;
            var qrImg   = (typeof QR_B64      !== 'undefined') ? QR_B64      : null;

            var missing = [];
            if (!logo)    missing.push('LOGO_B64');
            if (!nuno)    missing.push('NUNO_B64');
            if (!needles) missing.push('NEEDLES_B64');
            if (!office)  missing.push('OFFICE_B64');
            if (missing.length) {
                throw new Error('Flyer images not loaded (' + missing.join(', ') + '). Please refresh the page.');
            }

            /* ── 3. Create document ───────────────────────────────── */
            var doc = new JsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

            var PW = 210, PH = 297;
            var ML = 14,  MR = 14;
            var CW = PW - ML - MR;   // 182 mm content width

            // Colours (RGB arrays)
            var JADE_DARK  = [4,   52,  44];
            var JADE       = [15, 110,  86];
            var JADE_MIST  = [225, 245, 238];
            var JADE_LIGHT = [93,  202, 165];
            var GOLD       = [186, 117,  23];
            var WHITE      = [255, 255, 255];
            var TEXT_MID   = [45,  74,  62];

            /* ── HEADER ──────────────────────────────────────────────*/
            doc.setFillColor(JADE_DARK[0], JADE_DARK[1], JADE_DARK[2]);
            doc.rect(0, 0, PW, 32, 'F');

            // Logo  — unique alias 'img_logo'
            doc.addImage(logo, 'JPEG', ML, 6, 16, 16, 'img_logo', 'FAST');

            // Clinic name
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(18);
            doc.setTextColor(WHITE[0], WHITE[1], WHITE[2]);
            doc.text('NaturalMed', ML + 20, 14);

            doc.setFont('helvetica', 'normal');
            doc.setFontSize(8.5);
            doc.setTextColor(JADE_MIST[0], JADE_MIST[1], JADE_MIST[2]);
            doc.text('Wellness', ML + 20, 19);

            // Right-side tagline
            doc.setFontSize(7.5);
            doc.text('www.naturalmed-wellness.com', PW - MR, 14, { align: 'right' });
            doc.setFontSize(7);
            doc.text('Mid-Wales, United Kingdom', PW - MR, 19, { align: 'right' });

            // Gold separator line
            doc.setDrawColor(GOLD[0], GOLD[1], GOLD[2]);
            doc.setLineWidth(0.8);
            doc.line(0, 32, PW, 32);

            /* ── PHOTO GRID ──────────────────────────────────────────*/
            var gridY  = 36;
            var nunoW  = 62, nunoH = 78;
            var rightW = CW - nunoW - 4;
            var stackH = (nunoH - 3) / 2;
            var rx     = ML + nunoW + 4;

            // Each image gets a UNIQUE alias to prevent jsPDF cache collision
            doc.addImage(nuno,    'JPEG', ML, gridY,               nunoW,  nunoH,  'img_nuno',    'FAST');
            doc.addImage(needles, 'JPEG', rx, gridY,               rightW, stackH, 'img_needles', 'FAST');
            doc.addImage(office,  'JPEG', rx, gridY + stackH + 3,  rightW, stackH, 'img_office',  'FAST');

            /* ── TITLE BAND ──────────────────────────────────────────*/
            var titleY = gridY + nunoH + 9;
            doc.setFillColor(JADE_DARK[0], JADE_DARK[1], JADE_DARK[2]);
            doc.rect(0, titleY - 5, PW, 18, 'F');
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(12);
            doc.setTextColor(WHITE[0], WHITE[1], WHITE[2]);
            doc.text('TRADITIONAL CHINESE MEDICINE · MID-WALES, UK', PW / 2, titleY + 4, { align: 'center' });

            /* ── BODY TEXT ───────────────────────────────────────────*/
            var bodyY = titleY + 18;
            doc.setDrawColor(JADE[0], JADE[1], JADE[2]);
            doc.setLineWidth(0.5);
            doc.line(ML, bodyY, PW - MR, bodyY);

            doc.setFont('helvetica', 'normal');
            doc.setFontSize(9.5);
            doc.setTextColor(TEXT_MID[0], TEXT_MID[1], TEXT_MID[2]);
            var bodyText =
                'Acupuncture, herbal medicine and holistic care in Newtown, Powys — rooted in authentic Chinese\n' +
                'medical tradition from Chengdu University. Nuno Pestana (BSc TCM, Member ATCM UK) has over\n' +
                '10 years of clinical experience treating pain, fertility, digestive and sleep conditions.';
            doc.text(bodyText, PW / 2, bodyY + 7, { align: 'center', lineHeightFactor: 1.6 });

            // Services pills row
            var servicesY = bodyY + 24;
            var services  = ['Acupuncture', 'Herbal Medicine', 'Tuina Massage', 'Chinese Dietetics', 'Online Consultations'];
            var pillW = 34, pillH = 7, pillGap = 2;
            var totalPillW = services.length * pillW + (services.length - 1) * pillGap;
            var px = (PW - totalPillW) / 2;

            services.forEach(function (s) {
                doc.setFillColor(JADE_MIST[0], JADE_MIST[1], JADE_MIST[2]);
                doc.setDrawColor(JADE[0], JADE[1], JADE[2]);
                doc.setLineWidth(0.3);
                doc.roundedRect(px, servicesY, pillW, pillH, 2, 2, 'FD');
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(6.5);
                doc.setTextColor(JADE_DARK[0], JADE_DARK[1], JADE_DARK[2]);
                doc.text(s, px + pillW / 2, servicesY + 4.5, { align: 'center' });
                px += pillW + pillGap;
            });

            /* ── FOOTER ──────────────────────────────────────────────*/
            var footerY = PH - 52;
            doc.setFillColor(JADE_DARK[0], JADE_DARK[1], JADE_DARK[2]);
            doc.rect(0, footerY, PW, PH - footerY, 'F');

            doc.setDrawColor(GOLD[0], GOLD[1], GOLD[2]);
            doc.setLineWidth(0.8);
            doc.line(0, footerY, PW, footerY);

            // CONTACTS heading
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(9);
            doc.setTextColor(GOLD[0], GOLD[1], GOLD[2]);
            doc.text('CONTACTS', ML, footerY + 9);

            doc.setDrawColor(GOLD[0], GOLD[1], GOLD[2]);
            doc.setLineWidth(0.4);
            doc.line(ML, footerY + 10.5, ML + 28, footerY + 10.5);

            // Contact lines
            var contacts = [
                'Email:    naturalmed.wellness@gmail.com',
                'Phone:   +44 7756 339 382',
                'Clinic:    30 Shortbridge Street, Newtown, Powys, SY16 2LN \u2014 Mid-Wales, UK',
            ];
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(8);
            doc.setTextColor(JADE_MIST[0], JADE_MIST[1], JADE_MIST[2]);
            contacts.forEach(function (line, i) {
                doc.text(line, ML, footerY + 17 + i * 7);
            });

            // ATCM line
            doc.setFontSize(7);
            doc.setTextColor(JADE_LIGHT[0], JADE_LIGHT[1], JADE_LIGHT[2]);
            doc.text('Member \u2014 Association of Traditional Chinese Medicine UK (ATCM)', ML, footerY + 38);

            // QR code  — unique alias 'img_qr'
            var qrSize = 35;
            var qrX    = PW - MR - qrSize;
            var qrFY   = footerY + 6;
            doc.setFillColor(WHITE[0], WHITE[1], WHITE[2]);
            doc.roundedRect(qrX - 2, qrFY - 2, qrSize + 4, qrSize + 4, 2, 2, 'F');
            if (qrImg) {
                doc.addImage(qrImg, 'JPEG', qrX, qrFY, qrSize, qrSize, 'img_qr', 'FAST');
            }
            doc.setFontSize(6);
            doc.setTextColor(JADE_LIGHT[0], JADE_LIGHT[1], JADE_LIGHT[2]);
            doc.text('Scan to visit website', qrX + qrSize / 2, qrFY + qrSize + 5, { align: 'center' });

            // Copyright
            doc.setFontSize(6.5);
            doc.text('\u00a9 2026 NaturalMed \u00b7 www.naturalmed-wellness.com', PW / 2, PH - 4, { align: 'center' });

            /* ── SAVE ────────────────────────────────────────────────*/
            doc.save('NaturalMed-Flyer.pdf');

        } catch (err) {
            console.error('Flyer generation error:', err);
            alert('Could not generate flyer.\n\n' + (err.message || String(err)) + '\n\nPlease refresh the page and try again.');
        }

        btn.textContent = origText;
        btn.disabled = false;

    }, 100);
}
