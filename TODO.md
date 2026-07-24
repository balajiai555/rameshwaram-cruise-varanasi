# Rameshwaram Cruise Varanasi - Project TODO List

This document tracks completed tasks, bug fixes, configurations, and future roadmap items for the Rameshwaram Cruise Varanasi booking platform.

---

## ✅ Completed Tasks

### 🎨 Branding & UI Redesign
- [x] **Official Logo Integration**: Extracted the official logo from the Elementor asset path (`image-removebg-preview.png`) and integrated it into both the web navbar and the ticket PDF header.
- [x] **Official Color Scheme Alignment**: Configured theme colors matching the official Varanasi cruise website:
  - Crimson Red (`#BE0A13`)
  - Deep Navy Blue (`#001C3F`)
  - Temple Gold/Amber (`#F59E0B`)
  - Soft Warm Ivory Background (`#FCFBF7`)
- [x] **Varanasi Landing Page Content**: Updated home page title and descriptions to focus on Ganga Aarti views, live music, and heritage commentary.
- [x] **Google Fonts Integration**: Added Montserrat (headings) and Plus Jakarta Sans (body) for modern, premium typography.

### 📄 E-Ticket Receipt & PDF Generation
- [x] **PDF Platform Fallback**: Configured `xhtml2pdf` as a pure-Python fallback rendering engine when WeasyPrint native binaries (GObject/Pango) are missing on Windows hosts.
- [x] **Modern Light Yellow Theme**: Redesigned the ticket receipt with a compact, modern gold-yellow theme.
- [x] **Single-Page Constraint**: Tightened margin paddings, line-heights, and font-sizing so the ticket fits strictly on a single A4 page.
- [x] **Bill of Supply**: Included a formal business invoice structure with:
  - Dummy GSTIN (`09AAECR9559B1ZN`)
  - SAC Code (`996411` - passenger transport service)
  - Tax breakout table displaying CGST (2.5% inclusive) and SGST (2.5% inclusive).

### 🔒 Security & Authentication
- [x] **Strict Staff Login**: Disabled all dev bypasses and autologin URLs. Staff members must authenticate using their username and password at `/accounts/login/`.
- [x] **Secure Configuration**: Integrated `python-dotenv` for loading SMTP, database, and base domain environment credentials from a local `.env` file.
- [x] **Dashboard Seat Generator**: Added a helper view and UI warning banner on the staff dashboard that lets admins initialize/generate all 60 seat assignments for active schedules directly in the browser.
- [x] **Seat Hold & Release Optimization**: Reduced seat hold limit to 7 minutes, added a Javascript ticking countdown timer on the checkout page, and implemented a secure `/api/release-booking/` endpoint to instantly free seats in the database if the user cancels or closes the payment modal.
- [x] **Schedules & Pricing Manager Dashboard**: Built a dedicated Schedules page inside the staff panel to batch-generate schedules in bulk and inline-update seat prices (supporting Rs. 5,000 festival surges inclusive of GST) directly from the browser.
- [x] **Simplified Dashboard Sorting & Layouts**: Removed redundant "Vessel / Route" and "Cruise" columns from the dashboard index and bookings list, removed the search ticket option, and sorted all list views chronologically by date/month/year.
- [x] **Personalized Email Branding & Paperless Disclaimers**: Set default sender display name to "RameshwaramCruiseVaranasi", updated subject to "Your Varanasi Ghat Cruise Yatra Ticket", added a spiritual "Om Namo Gangaye Namah" greeting in Hindi, and incorporated an eco-friendly note instructing boarding gate checkers to accept the attached PDF ticket copy or the email directly from mobile devices.
- [x] **SEO Meta Optimization & Favicon Integration**: Read and extracted core keywords from the live website to implement optimized title, description, keywords, and OpenGraph tags. Mapped the official logo as a high-resolution favicon in the header layout, and configured the production host parameters for `book.rameshwaramcruise.com`.
- [x] **GTK Runtime Auto-Detection & PDF Fallback**: Integrated proactive verification check for `libgobject` DLL dependencies on Windows local environments before importing WeasyPrint. Bypasses the import and falls back silently to `xhtml2pdf` if dependencies are missing, completely silencing console logging warning tracebacks.
- [x] **Security Verification & Audit**: Compiled a comprehensive security audit report detailing CSRF tokens, ORM SQL-injection blocks, XSS auto-escaping, staff dashboard Mixin constraints, double-boarding QR limits, and transaction concurrency (select_for_update) locks.
- [x] **Spreadsheet Bookings Export (CSV)**: Built a dashboard CSV exporter view allowing staff to download a structured Excel-compatible spreadsheet of all guest bookings, contacts, slot times in 24-hour format, and actual seat lists.
- [x] **Interactive Dashboard Search, Sorting & Seats**: Built a dynamic search form (by name, phone, email, booking #) and dropdown sorting options (by day, month, or transaction date) on the bookings list dashboard. Displayed actual seat labels as badges instead of simple seat counts in the table columns, and added visual dynamic grouping header rows (by day, month, or transaction date depending on active sort) to group hundreds of bookings elegantly.
- [x] **Head Template Injection Block**: Added a custom `extra_head` template block in the HTML head layout to allow seamless injection of Google Tag / Analytics / marketing pixels.
- [x] **Automated Weekly DB Backup Configuration**: Added automated database backup scripts and cron triggers under `deploy.txt` to dump production PostgreSQL databases weekly and prune old archives automatically.
- [x] **Today Revenue & Toggleable Monthly Filter Modal**: Restructured the main dashboard metrics card to display **Today's Revenue** by default. Integrated an interactive, toggleable monthly filter popup modal allowing admins to choose any transaction period and instantly view filtered monthly earnings without cluttering the main layout.
- [x] **Brute-Force Rate Limiting & OTP Self-Destruct**: Implemented strict IP-based rate limiting (5 POST requests per minute) on customer OTP issue/verification and staff login endpoints. Configured automated OTP invalidation locking after 5 incorrect validation attempts to mathematically eliminate brute-force guessing vectors.
- [x] **Developer Architecture Blueprint (Structure.md)**: Generated a complete developer blueprint mapping the file tree, model relationships, checkout/payment flows, and security measures to allow seamless onboarding of external developers.
- [x] **Visual Product Showcase Guide (PDF)**: Captured high-quality browser screenshots of the local passenger homepage, interactive seat grid, customer OTP sign-in, and staff dashboard login. Compiled them into a print-ready `product_showcase.pdf` document describing the UI and features in detail to show other customers.

### 🐛 Bug Fixes & Bypasses
- [x] **Seat Filter DB Fix**: Corrected relationship lookup from `booking_seats__booking` to `bookingseat__booking` to resolve critical lookup FieldErrors.
- [x] **Email URL Context Fix**: Replaced missing dynamic request host context in mail templates with a static/env-driven `BASE_URL` token.
- [x] **Razorpay Bypass**: Added a `[Test Env] Dummy Success Payment` button in debug environments to allow ticket generation testing without a live Razorpay merchant account.

---

## 🚀 Future Roadmap & Pending Features

### 🔐 2-Factor Authentication (2FA) for Staff
- [ ] **Staff OTP Login**: Implement a two-factor verification step using email OTP (One-Time Password) for all staff members logging into `/accounts/login/` before redirecting to the admin dashboard.

### 💳 Live Payment Gateway Integration
- [ ] **Razorpay Merchant Production Credentials**: Set up live keys in the `.env` configuration once merchant onboarding is completed.
- [ ] **Disable Test Bypass**: Ensure Razorpay test bypass buttons are completely hidden in production (`DEBUG = False`).

### 📦 Deployment & Environment Optimization
- [ ] **Collect Static Assets**: Run `python manage.py collectstatic` for serving production assets via WhiteNoise or CDN.
- [ ] **SSL Configuration**: Force secure HTTPS redirects and configure secure cookies for production sessions.
