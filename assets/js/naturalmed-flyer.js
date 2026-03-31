/* naturalmed-flyer.js — PDF flyer generator using jsPDF */
/* Depends on: flyer-images.js (must be loaded first) */

function generateFlyer() {
    const btn = document.getElementById('flyerBtn');
    btn.textContent = 'Generating…';
    btn.disabled = true;

    setTimeout(() => {
        try {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

            const PW = 210, PH = 297;
            const ML = 14, MR = 14, MT = 12;
            const CW = PW - ML - MR;  // 182mm content width

            // ── COLOURS ────────────────────────────────────────────────
            const JADE_DARK  = [4,   52,  44];
            const JADE       = [15, 110,  86];
            const JADE_MIST  = [225, 245, 238];
            const GOLD       = [186, 117,  23];
            const CREAM      = [248, 245, 240];
            const WHITE      = [255, 255, 255];
            const TEXT_MID   = [45,  74,  62];

            const rgb = (arr) => ({ r: arr[0], g: arr[1], b: arr[2] });

            // ── HEADER ─────────────────────────────────────────────────
            // Background strip
            doc.setFillColor(...JADE_DARK);
            doc.rect(0, 0, PW, 32, 'F');

            // Logo
            doc.addImage(LOGO_B64, 'JPEG', ML, 6, 16, 16);

            // Clinic name
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(18);
            doc.setTextColor(...WHITE);
            doc.text('NaturalMed', ML + 20, 14);

            doc.setFont('helvetica', 'normal');
            doc.setFontSize(8.5);
            doc.setTextColor(...JADE_MIST);
            doc.text('Wellness', ML + 20, 19);

            // Right-side tagline in header
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(7.5);
            doc.setTextColor(...JADE_MIST);
            doc.text('www.naturalmed-wellness.com', PW - MR, 14, { align: 'right' });
            doc.setFontSize(7);
            doc.text('Mid-Wales, United Kingdom', PW - MR, 19, { align: 'right' });

            // Gold separator line
            doc.setDrawColor(...GOLD);
            doc.setLineWidth(0.8);
            doc.line(0, 32, PW, 32);

            // ── PHOTO GRID ─────────────────────────────────────────────
            const gridY = 36;
            const nunoW = 62, nunoH = 78;
            const rightW = CW - nunoW - 4;
            const stackH = (nunoH - 3) / 2;

            // Nuno photo (left)
            doc.addImage(NUNO_B64, 'JPEG', ML, gridY, nunoW, nunoH, 'nuno', 'FAST');

            // Needles photo (right top)
            const rx = ML + nunoW + 4;
            doc.addImage(NEEDLES_B64, 'JPEG', rx, gridY, rightW, stackH, 'needles', 'FAST');

            // Office photo (right bottom)
            doc.addImage(OFFICE_B64, 'JPEG', rx, gridY + stackH + 3, rightW, stackH, 'office', 'FAST');

            // ── TITLE SECTION ──────────────────────────────────────────
            const titleY = gridY + nunoH + 9;

            doc.setFillColor(...JADE_DARK);
            doc.rect(0, titleY - 5, PW, 18, 'F');

            doc.setFont('helvetica', 'bold');
            doc.setFontSize(12);
            doc.setTextColor(...WHITE);
            doc.text('TRADITIONAL CHINESE MEDICINE · MID-WALES, UK', PW / 2, titleY + 4, { align: 'center' });

            // ── BODY TEXT ──────────────────────────────────────────────
            const bodyY = titleY + 18;

            doc.setDrawColor(...JADE);
            doc.setLineWidth(0.5);
            doc.line(ML, bodyY, PW - MR, bodyY);

            doc.setFont('helvetica', 'normal');
            doc.setFontSize(9.5);
            doc.setTextColor(...TEXT_MID);
            const bodyText = 'Acupuncture, herbal medicine and holistic care in Newtown, Powys — rooted in authentic Chinese\nmedical tradition from Chengdu University. Nuno Pestana (BSc TCM, Member ATCM UK) has over\n10 years of clinical experience treating pain, fertility, digestive and sleep conditions.';
            doc.text(bodyText, PW / 2, bodyY + 7, { align: 'center', lineHeightFactor: 1.6 });

            // Services pills row
            const servicesY = bodyY + 24;
            const services  = ['Acupuncture', 'Herbal Medicine', 'Tuina Massage', 'Chinese Dietetics', 'Online Consultations'];
            const pillW     = 34, pillH = 7, pillGap = 2;
            const totalPillW = services.length * pillW + (services.length - 1) * pillGap;
            let px = (PW - totalPillW) / 2;

            services.forEach(s => {
                doc.setFillColor(...JADE_MIST);
                doc.setDrawColor(...JADE);
                doc.setLineWidth(0.3);
                doc.roundedRect(px, servicesY, pillW, pillH, 2, 2, 'FD');
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(6.5);
                doc.setTextColor(...JADE_DARK);
                doc.text(s, px + pillW / 2, servicesY + 4.5, { align: 'center' });
                px += pillW + pillGap;
            });

            // ── FOOTER ─────────────────────────────────────────────────
            const footerY = PH - 52;

            // Jade background
            doc.setFillColor(...JADE_DARK);
            doc.rect(0, footerY, PW, PH - footerY, 'F');

            // Gold accent line
            doc.setDrawColor(...GOLD);
            doc.setLineWidth(0.8);
            doc.line(0, footerY, PW, footerY);

            // CONTACTS heading
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(9);
            doc.setTextColor(...GOLD);
            doc.text('CONTACTS', ML, footerY + 9);

            // Gold underline
            doc.setDrawColor(...GOLD);
            doc.setLineWidth(0.4);
            doc.line(ML, footerY + 10.5, ML + 28, footerY + 10.5);

            // Contact lines
            const contacts = [
                'Email:    naturalmed.wellness@gmail.com',
                'Phone:   +44 7756 339 382',
                'Clinic:    30 Shortbridge Street, Newtown, Powys, SY16 2LN — Mid-Wales, UK',
            ];
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(8);
            doc.setTextColor(...JADE_MIST);
            contacts.forEach((line, i) => {
                doc.text(line, ML, footerY + 17 + i * 7);
            });

            // ATCM line
            doc.setFontSize(7);
            doc.setTextColor(93, 202, 165);
            doc.text('Member — Association of Traditional Chinese Medicine UK (ATCM)', ML, footerY + 38);

            // QR code (right side of footer)
            const qrSize = 35;
            const qrX = PW - MR - qrSize;
            const qrY = footerY + 6;
            doc.setFillColor(...WHITE);
            doc.roundedRect(qrX - 2, qrY - 2, qrSize + 4, qrSize + 4, 2, 2, 'F');
            doc.addImage(QR_B64, 'JPEG', qrX, qrY, qrSize, qrSize, 'qrcode', 'FAST');
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(6);
            doc.setTextColor(93, 202, 165);
            doc.text('Scan to visit website', qrX + qrSize / 2, qrY + qrSize + 5, { align: 'center' });

            // Copyright
            doc.setFontSize(6.5);
            doc.setTextColor(93, 202, 165);
            doc.text('© 2026 NaturalMed · www.naturalmed-wellness.com', PW / 2, PH - 4, { align: 'center' });

            // ── SAVE ───────────────────────────────────────────────────
            doc.save('NaturalMed-Flyer.pdf');

        } catch (err) {
            console.error('Flyer error:', err);
            alert('Could not generate flyer. Please try again.');
        }

        btn.textContent = 'Take a Flyer With You';
        btn.disabled = false;
    }, 80);
}
