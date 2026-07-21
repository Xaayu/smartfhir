import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../config";
import MedTechLogo from "../components/MedTechLogo";

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  /* Custom scrollbar styling */
  ::-webkit-scrollbar {
    width: 10px;
    height: 10px;
  }
  ::-webkit-scrollbar-track {
    background: var(--bg);
  }
  ::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 5px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: var(--accent);
  }

  :root {
    --bg:      #0A0E1A;
    --surface: #1A2035;
    --border:  #242B42;
    --accent:  #4F8EF7;
    --teal:    #00D4AA;
    --error:   #F87171;
    --warning: #FBBF24;
    --text:    #E2E8F0;
    --muted:   #64748B;
    --dim:     #94A3B8;
  }

  html { scroll-behavior: smooth; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    font-size: 16px;
    line-height: 1.6;
    overflow-x: hidden;
  }

  /* NAV */
  .navbar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 100;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 48px; height: 64px;
    background: rgba(10,14,26,0.85);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
  }
  .nav-logo {
    display: flex; align-items: center; gap: 10px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700; font-size: 18px; cursor: pointer;
  }
  .nav-logo-icon {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, var(--accent), var(--teal));
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 800; color: #fff; flex-shrink: 0;
  }
  .nav-links {
    display: flex; align-items: center; gap: 32px;
    list-style: none; margin: 0; padding: 0;
  }
  .nav-links a { color: var(--dim); text-decoration: none; font-size: 14px; transition: color 0.2s; }
  .nav-links a:hover { color: var(--text); }
  .nav-cta {
    background: var(--accent); color: #fff; border: none; border-radius: 8px;
    padding: 8px 20px; font-size: 14px; font-weight: 600;
    cursor: pointer; transition: opacity 0.2s; font-family: 'Inter', sans-serif;
  }
  .nav-cta:hover { opacity: 0.85; }

  /* HERO */
  .hero {
    min-height: 100vh; display: flex; align-items: center;
    padding: 120px 48px 80px; gap: 64px;
    max-width: 1280px; margin: 0 auto;
  }
  .hero-left { flex: 1; min-width: 0; }
  .hero-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(79,142,247,0.1); border: 1px solid rgba(79,142,247,0.3);
    border-radius: 100px; padding: 6px 14px;
    font-size: 12px; font-weight: 600; color: var(--accent);
    letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 24px;
  }
  .hero-badge-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--teal); animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
  .hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(36px, 4vw, 56px); font-weight: 700;
    line-height: 1.1; letter-spacing: -0.03em; margin-bottom: 20px;
  }
  .hero-title-accent {
    background: linear-gradient(135deg, var(--accent), var(--teal));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .hero-sub { font-size: 18px; color: var(--dim); max-width: 480px; margin-bottom: 40px; line-height: 1.7; }
  .hero-actions { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
  .btn-primary {
    background: var(--accent); color: #fff; border: none; border-radius: 10px;
    padding: 14px 28px; font-size: 15px; font-weight: 600; cursor: pointer;
    transition: all 0.2s; font-family: 'Inter', sans-serif;
    display: inline-flex; align-items: center; gap: 8px;
  }
  .btn-primary:hover { background: #6B9EF8; transform: translateY(-1px); box-shadow: 0 8px 24px rgba(79,142,247,0.3); }
  .btn-secondary {
    background: transparent; color: var(--text); border: 1px solid var(--border);
    border-radius: 10px; padding: 14px 28px; font-size: 15px; font-weight: 500;
    cursor: pointer; transition: all 0.2s; font-family: 'Inter', sans-serif;
  }
  .btn-secondary:hover { border-color: var(--accent); color: var(--accent); }
  .hero-note { margin-top: 16px; font-size: 13px; color: var(--muted); }
  .hero-highlights { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 24px; }
  .hero-highlight {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 10px 14px; border-radius: 999px;
    background: rgba(255,255,255,0.03); border: 1px solid var(--border);
    color: var(--dim); font-size: 13px;
  }
  .hero-highlight strong { color: var(--text); font-weight: 600; }
  .hero-right { flex: 1.1; min-width: 0; }

  /* DEMO CARD */
  .demo-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 16px; overflow: hidden; box-shadow: 0 32px 80px rgba(0,0,0,0.4);
  }
  .demo-topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 16px; border-bottom: 1px solid var(--border); background: rgba(0,0,0,0.2);
  }
  .demo-dots { display: flex; gap: 6px; }
  .demo-dot { width: 10px; height: 10px; border-radius: 50%; }
  .demo-label { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--muted); }
  .demo-body { display: grid; grid-template-columns: 1fr 1fr; }
  .demo-panel { padding: 20px; }
  .demo-panel:first-child { border-right: 1px solid var(--border); }
  .demo-panel-label {
    font-size: 10px; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--muted); margin-bottom: 12px;
  }
  .demo-code { font-family: 'JetBrains Mono', monospace; font-size: 11.5px; line-height: 1.8; white-space: pre; }
  .code-key   { color: #7DD3FC; }
  .code-str   { color: #86EFAC; }
  .code-err   { color: var(--error); text-decoration: underline wavy var(--error); }
  .code-fix   { color: var(--teal); }
  .code-punct { color: var(--dim); }
  .demo-errors { padding: 16px 20px; border-top: 1px solid var(--border); background: rgba(0,0,0,0.15); }
  .demo-error-item {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 12px; border-radius: 8px; margin-bottom: 8px;
    background: rgba(248,113,113,0.08); border: 1px solid rgba(248,113,113,0.2);
    font-size: 12px; transition: all 0.4s;
  }
  .demo-error-item.fixed { background: rgba(0,212,170,0.08); border-color: rgba(0,212,170,0.2); }
  .demo-error-field { font-family: 'JetBrains Mono', monospace; color: var(--accent); font-size: 11px; min-width: 80px; }
  .demo-error-msg { color: var(--dim); flex: 1; }
  .demo-badge {
    font-size: 10px; font-weight: 700; letter-spacing: 0.05em;
    padding: 2px 8px; border-radius: 4px; text-transform: uppercase; white-space: nowrap;
  }
  .badge-error { background: rgba(248,113,113,0.15); color: var(--error); border: 1px solid rgba(248,113,113,0.3); }
  .badge-fixed { background: rgba(0,212,170,0.15); color: var(--teal); border: 1px solid rgba(0,212,170,0.3); }
  .demo-fix-btn {
    width: 100%; margin-top: 4px;
    background: linear-gradient(135deg, var(--accent), var(--teal));
    color: #fff; border: none; border-radius: 8px; padding: 10px;
    font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s;
    font-family: 'Inter', sans-serif; display: flex; align-items: center; justify-content: center; gap: 8px;
  }
  .demo-fix-btn:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); }
  .demo-fix-btn:disabled { opacity: 0.5; cursor: default; transform: none; }
  .demo-quality { display: flex; align-items: center; gap: 12px; padding: 12px 20px; border-top: 1px solid var(--border); }
  .quality-ring {
    width: 40px; height: 40px; border-radius: 50%; border: 2px solid var(--teal);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 14px;
    color: var(--teal); transition: all 0.5s; flex-shrink: 0;
  }
  .quality-ring.grade-b { border-color: var(--accent); color: var(--accent); }
  .quality-stats { display: flex; gap: 16px; flex: 1; }
  .quality-stat { text-align: center; }
  .quality-stat-val { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 18px; }
  .quality-stat-label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }

  /* STATS BAR */
  .stats-bar {
    border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
    padding: 32px 48px; display: flex; justify-content: center; gap: 80px; flex-wrap: wrap;
  }
  .stat-item { text-align: center; }
  .stat-val {
    font-family: 'Space Grotesk', sans-serif; font-size: 36px; font-weight: 700;
    background: linear-gradient(135deg, var(--accent), var(--teal));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .stat-label { font-size: 13px; color: var(--muted); margin-top: 4px; }

  /* SECTIONS */
  .section { max-width: 1280px; margin: 0 auto; padding: 96px 48px; }
  .section-eyebrow { font-size: 12px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); margin-bottom: 16px; }
  .section-title { font-family: 'Space Grotesk', sans-serif; font-size: clamp(28px,3vw,40px); font-weight: 700; letter-spacing: -0.02em; margin-bottom: 16px; line-height: 1.2; }
  .section-sub { font-size: 17px; color: var(--dim); max-width: 520px; line-height: 1.7; }
  .full-divider { height: 1px; background: var(--border); }
  .benefit-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 32px; }
  .benefit-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
    padding: 24px; transition: border-color 0.2s, transform 0.2s;
  }
  .benefit-card:hover { border-color: rgba(79,142,247,0.4); transform: translateY(-2px); }
  .benefit-icon { font-size: 22px; margin-bottom: 12px; }
  .benefit-title { font-family: 'Space Grotesk', sans-serif; font-size: 16px; font-weight: 600; margin-bottom: 8px; }
  .benefit-desc { font-size: 14px; color: var(--dim); line-height: 1.7; }

  /* HOW IT WORKS */
  .how-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2px; margin-top: 64px; background: var(--border); border-radius: 16px; overflow: hidden;
  }
  .how-step { background: var(--surface); padding: 40px 32px; }
  .how-step-num { font-family: 'Space Grotesk', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 0.1em; color: var(--accent); text-transform: uppercase; margin-bottom: 20px; }
  .how-step-icon { font-size: 32px; margin-bottom: 16px; }
  .how-step-title { font-family: 'Space Grotesk', sans-serif; font-size: 18px; font-weight: 600; margin-bottom: 10px; }
  .how-step-desc { font-size: 14px; color: var(--dim); line-height: 1.7; }
  .how-code {
    margin-top: 16px; background: rgba(0,0,0,0.3); border-radius: 8px; padding: 12px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--dim);
    border: 1px solid var(--border); line-height: 1.8;
  }
  .how-code .hl { color: var(--teal); }

  /* API CODE BLOCK */
  .code-block {
    background: #060A14; border: 1px solid var(--border); border-radius: 12px; padding: 24px;
    font-family: 'JetBrains Mono', monospace; font-size: 13px; line-height: 1.8;
    overflow-x: auto; margin-top: 32px; white-space: pre;
  }
  .cb-comment { color: #4A5568; }
  .cb-key     { color: #7DD3FC; }
  .cb-str     { color: #86EFAC; }
  .cb-num     { color: #FCA5A5; }
  .cb-kw      { color: #C084FC; }
  .cb-punct   { color: #64748B; }

  /* FEATURES */
  .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px,1fr)); gap: 16px; margin-top: 64px; }
  .feature-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 28px; transition: border-color 0.2s, transform 0.2s;
    opacity: 0; transform: translateY(20px);
  }
  .feature-card.visible { opacity: 1 !important; transform: translateY(0) !important; transition: opacity 0.5s ease, transform 0.5s ease, border-color 0.2s !important; }
  .feature-card:hover { border-color: rgba(79,142,247,0.4); transform: translateY(-2px); }
  .feature-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; margin-bottom: 16px; }
  .feature-title { font-family: 'Space Grotesk', sans-serif; font-size: 16px; font-weight: 600; margin-bottom: 8px; }
  .feature-desc { font-size: 14px; color: var(--dim); line-height: 1.7; }
  .feature-tag { display: inline-block; margin-top: 12px; font-size: 11px; font-weight: 600; color: var(--accent); letter-spacing: 0.05em; }

  /* RESOURCES */
  .resources-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 64px; }
  .resource-chip {
    background: var(--surface); border: 1px solid var(--border); border-radius: 100px;
    padding: 8px 20px; font-family: 'JetBrains Mono', monospace; font-size: 13px;
    color: var(--dim); transition: all 0.2s; cursor: default;
  }
  .resource-chip:hover { border-color: var(--accent); color: var(--accent); }
  .resource-chip.active { background: rgba(79,142,247,0.1); border-color: rgba(79,142,247,0.4); color: var(--accent); }

  /* PRICING */
  .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px,1fr)); gap: 16px; margin-top: 64px; align-items: start; }
  .pricing-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 16px; padding: 32px; transition: all 0.2s;
    opacity: 0; transform: translateY(20px);
  }
  .pricing-card.visible { opacity: 1 !important; transform: translateY(0) !important; transition: opacity 0.5s ease, transform 0.5s ease !important; }
  .pricing-card.featured {
    border-color: var(--accent);
    background: linear-gradient(135deg, rgba(79,142,247,0.08), rgba(0,212,170,0.04));
    position: relative;
  }
  .pricing-popular {
    position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
    background: linear-gradient(135deg, var(--accent), var(--teal));
    color: #fff; font-size: 11px; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase;
    padding: 4px 16px; border-radius: 100px; white-space: nowrap;
  }
  .pricing-tier { font-size: 12px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin-bottom: 12px; }
  .pricing-price { font-family: 'Space Grotesk', sans-serif; font-size: 40px; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 4px; }
  .pricing-price span { font-size: 16px; font-weight: 500; color: var(--muted); }
  .pricing-calls { font-size: 13px; color: var(--dim); margin-bottom: 24px; }
  .pricing-divider { height: 1px; background: var(--border); margin-bottom: 24px; }
  .pricing-features { list-style: none; }
  .pricing-features li { display: flex; align-items: flex-start; gap: 10px; font-size: 14px; color: var(--dim); margin-bottom: 12px; }
  .pricing-features li::before { content: '✓'; color: var(--teal); font-weight: 700; flex-shrink: 0; }
  .pricing-features li.off { opacity: 0.4; }
  .pricing-features li.off::before { content: '×'; color: var(--muted); }
  .pricing-btn { width: 100%; margin-top: 24px; padding: 12px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; font-family: 'Inter', sans-serif; transition: all 0.2s; }
  .pricing-btn-outline { background: transparent; color: var(--text); border: 1px solid var(--border); }
  .pricing-btn-outline:hover { border-color: var(--accent); color: var(--accent); }
  .pricing-btn-filled { background: var(--accent); color: #fff; border: none; }
  .pricing-btn-filled:hover { background: #6B9EF8; }
  .pricing-btn-disabled { background: rgba(100,116,139,0.12); color: var(--muted); border: 1px solid var(--border); cursor: not-allowed; }
  .pricing-btn-disabled:hover { border-color: var(--border); color: var(--muted); }

  /* CTA */
  .cta-section {
    margin: 0 48px 96px;
    background: linear-gradient(135deg, rgba(79,142,247,0.12), rgba(0,212,170,0.06));
    border: 1px solid rgba(79,142,247,0.2); border-radius: 24px;
    padding: 80px 64px; text-align: center;
  }
  .cta-title { font-family: 'Space Grotesk', sans-serif; font-size: clamp(28px,3vw,44px); font-weight: 700; letter-spacing: -0.02em; margin-bottom: 16px; }
  .cta-sub { font-size: 17px; color: var(--dim); margin-bottom: 40px; }
  .cta-input-row { display: flex; gap: 12px; max-width: 480px; margin: 0 auto; }
  .cta-input {
    flex: 1; background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 12px 16px; color: var(--text);
    font-size: 14px; font-family: 'Inter', sans-serif; outline: none; transition: border-color 0.2s;
  }
  .cta-input:focus { border-color: var(--accent); }
  .cta-input::placeholder { color: var(--muted); }

  /* FOOTER */
  .footer-new {
    border-top: 1px solid var(--border);
    background: #060913;
    padding: 80px 48px 40px;
    margin-top: 80px;
    position: relative;
    z-index: 10;
  }
  .footer-grid {
    max-width: 1280px;
    margin: 0 auto 60px;
    display: grid;
    grid-template-columns: 1.4fr 0.9fr 0.9fr 1.4fr;
    gap: 48px;
  }
  .footer-brand-col {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .footer-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .footer-logo-icon {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    background: linear-gradient(135deg, var(--accent), var(--teal));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 800;
    color: #fff;
    flex-shrink: 0;
  }
  .footer-brand-desc {
    font-size: 14px;
    color: var(--dim);
    line-height: 1.6;
  }
  .footer-contact-info {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .footer-contact-item {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13.5px;
    color: var(--dim);
  }
  .footer-contact-item a {
    color: var(--dim);
    text-decoration: none;
    transition: color 0.2s;
  }
  .footer-contact-item a:hover {
    color: var(--accent);
  }
  .footer-contact-icon {
    font-size: 16px;
    opacity: 0.85;
  }
  .footer-socials {
    display: flex;
    gap: 12px;
    margin-top: 8px;
  }
  .footer-social-link {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border);
    color: var(--dim);
    transition: all 0.2s;
  }
  .footer-social-link:hover {
    color: var(--text);
    border-color: var(--accent);
    background: rgba(79,142,247,0.1);
    transform: translateY(-2px);
  }
  
  .footer-links-col {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .footer-col-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text);
  }
  .footer-col-links {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .footer-col-links li {
    font-size: 14px;
  }
  .footer-col-links a, .footer-btn-link {
    color: var(--dim);
    text-decoration: none;
    transition: color 0.2s;
    background: transparent;
    border: none;
    padding: 0;
    text-align: left;
    font-family: inherit;
    font-size: inherit;
    cursor: pointer;
  }
  .footer-col-links a:hover, .footer-btn-link:hover {
    color: var(--accent);
  }
  .footer-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 12.5px;
    color: var(--teal);
    background: rgba(0, 212, 170, 0.08);
    border: 1px solid rgba(0, 212, 170, 0.2);
    padding: 4px 12px;
    border-radius: 99px;
    margin-top: 4px;
    width: fit-content;
  }
  .footer-status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--teal);
    animation: pulse 2s infinite;
  }

  .footer-contact-col {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .footer-contact-form {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .footer-form-group {
    display: flex;
    flex-direction: column;
  }
  .footer-form-input {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
    color: var(--text);
    font-size: 13.5px;
    font-family: inherit;
    outline: none;
    transition: border-color 0.2s;
  }
  .footer-form-input:focus {
    border-color: var(--accent);
  }
  .footer-form-textarea {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
    color: var(--text);
    font-size: 13.5px;
    font-family: inherit;
    min-height: 70px;
    resize: none;
    outline: none;
    transition: border-color 0.2s;
  }
  .footer-form-textarea:focus {
    border-color: var(--accent);
  }
  .footer-form-btn {
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 10px;
    font-size: 13.5px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s, transform 0.2s;
    font-family: inherit;
  }
  .footer-form-btn:hover:not(:disabled) {
    background: #6B9EF8;
    transform: translateY(-1px);
  }
  .footer-form-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .footer-form-success {
    font-size: 12.5px;
    color: var(--teal);
    background: rgba(0, 212, 170, 0.08);
    border: 1px solid rgba(0, 212, 170, 0.2);
    border-radius: 8px;
    padding: 8px 12px;
    text-align: center;
  }

  .footer-bottom {
    max-width: 1280px;
    margin: 0 auto;
    border-top: 1px solid var(--border);
    padding-top: 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 20px;
  }
  .footer-bottom-links {
    display: flex;
    gap: 24px;
  }
  .footer-bottom-links a {
    color: var(--muted);
    font-size: 13px;
    text-decoration: none;
    transition: color 0.2s;
  }
  .footer-bottom-links a:hover {
    color: var(--text);
  }

  /* FEEDBACK WIDGET */
  .fb-trigger {
    position: fixed;
    right: 28px;
    bottom: 28px;
    z-index: 9999;
    display: flex;
    align-items: center;
    gap: 10px;
    background: linear-gradient(135deg, var(--accent), var(--teal));
    color: #fff;
    border: none;
    border-radius: 999px;
    padding: 12px 20px;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 8px 32px rgba(79,142,247,0.35);
    transition: transform 0.25s, box-shadow 0.25s;
    white-space: nowrap;
  }
  .fb-trigger:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(79,142,247,0.45);
  }
  .fb-trigger-icon {
    width: 18px;
    height: 18px;
    border: 2px solid currentColor;
    border-radius: 6px;
    position: relative;
    flex-shrink: 0;
  }
  .fb-trigger-icon::after {
    content: '';
    position: absolute;
    left: 3px;
    bottom: -5px;
    width: 7px;
    height: 7px;
    background: var(--teal);
    border-left: 2px solid currentColor;
    border-bottom: 2px solid currentColor;
    transform: rotate(-18deg);
  }
  .fb-panel {
    position: fixed;
    right: 28px;
    bottom: 88px;
    z-index: 9998;
    width: min(360px, calc(100vw - 32px));
    background: var(--surface);
    border: 1px solid #2A3550;
    border-radius: 16px;
    box-shadow: 0 24px 64px rgba(0,0,0,0.5);
    overflow: hidden;
    opacity: 0;
    pointer-events: none;
    transform: translateY(16px) scale(0.97);
    transition: opacity 0.25s ease, transform 0.25s ease;
  }
  .fb-panel.open {
    opacity: 1;
    pointer-events: all;
    transform: translateY(0) scale(1);
  }
  .fb-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 20px 20px 0;
  }
  .fb-title {
    color: var(--text);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 17px;
    font-weight: 700;
    line-height: 1.3;
  }
  .fb-close {
    background: none;
    border: none;
    color: var(--muted);
    cursor: pointer;
    flex-shrink: 0;
    font-size: 18px;
    line-height: 1;
    margin-left: 12px;
    padding: 2px;
    transition: color 0.15s;
  }
  .fb-close:hover { color: var(--text); }
  .fb-body { padding: 16px 20px 20px; }
  .fb-q-label {
    color: var(--dim);
    font-size: 13px;
    font-weight: 500;
    line-height: 1.5;
    margin-bottom: 8px;
  }
  .fb-textarea {
    width: 100%;
    min-height: 90px;
    background: #0F1422;
    border: 1px solid #2A3550;
    border-radius: 10px;
    color: var(--text);
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    line-height: 1.6;
    outline: none;
    padding: 11px 13px;
    resize: none;
    transition: border-color 0.2s;
  }
  .fb-textarea:focus { border-color: var(--accent); }
  .fb-textarea.invalid { border-color: var(--error); }
  .fb-textarea::placeholder, .fb-email::placeholder { color: #3D4F6B; }
  .fb-char {
    color: #3D4F6B;
    font-size: 11px;
    margin-top: 4px;
    text-align: right;
    transition: color 0.2s;
  }
  .fb-char.warn { color: var(--warning); }
  .fb-roadmap-label {
    color: var(--muted);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.06em;
    margin: 16px 0 10px;
    text-transform: uppercase;
  }
  .fb-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    margin-bottom: 4px;
  }
  .fb-chip {
    background: #0F1422;
    border: 1px solid #2A3550;
    border-radius: 999px;
    color: var(--dim);
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    padding: 5px 13px;
    transition: border-color 0.15s, color 0.15s, background 0.15s;
  }
  .fb-chip:hover {
    border-color: rgba(79,142,247,0.5);
    color: var(--text);
  }
  .fb-chip.selected {
    background: rgba(79,142,247,0.12);
    border-color: rgba(79,142,247,0.5);
    color: var(--accent);
  }
  .fb-email-row {
    display: flex;
    gap: 8px;
    margin-top: 14px;
  }
  .fb-email {
    flex: 1;
    min-width: 0;
    background: #0F1422;
    border: 1px solid #2A3550;
    border-radius: 10px;
    color: var(--text);
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    outline: none;
    padding: 10px 12px;
    transition: border-color 0.2s;
  }
  .fb-email:focus { border-color: var(--accent); }
  .fb-submit {
    background: var(--accent);
    border: none;
    border-radius: 10px;
    color: #fff;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 18px;
    transition: background 0.2s, opacity 0.2s;
    white-space: nowrap;
  }
  .fb-submit:hover { background: #6B9EF8; }
  .fb-submit:disabled { cursor: default; opacity: 0.5; }
  .fb-success {
    display: none;
    padding: 32px 20px;
    text-align: center;
  }
  .fb-success.visible { display: block; }
  .fb-success-icon {
    align-items: center;
    background: rgba(0,212,170,0.12);
    border: 1px solid rgba(0,212,170,0.25);
    border-radius: 50%;
    color: var(--teal);
    display: inline-flex;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 22px;
    font-weight: 700;
    height: 44px;
    justify-content: center;
    margin-bottom: 12px;
    width: 44px;
  }
  .fb-success-title {
    color: var(--text);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 6px;
  }
  .fb-success-sub {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.6;
  }
  .fb-note {
    color: #3D4F6B;
    font-size: 11px;
    margin-top: 12px;
    text-align: center;
  }

  /* ANIMATIONS */
  @keyframes fadeUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
  .fade-up   { animation: fadeUp 0.6s ease both; }
  .fade-up-2 { animation-delay: 0.1s; }
  .fade-up-3 { animation-delay: 0.2s; }
  .fade-up-4 { animation-delay: 0.3s; }

  /* RESPONSIVE */
  @media (max-width: 768px) {
    .navbar { padding: 0 20px; }
    .nav-links { display: none; }
    .hero { flex-direction: column; padding: 100px 20px 60px; gap: 40px; }
    .section { padding: 60px 20px; }
    .stats-bar { padding: 32px 20px; gap: 40px; }
    .cta-section { margin: 0 20px 60px; padding: 48px 24px; }
    .cta-input-row { flex-direction: column; }
    .footer-grid { grid-template-columns: 1fr; gap: 36px; margin-bottom: 40px; }
    .footer-new { padding: 60px 20px 30px; }
    .footer-bottom { flex-direction: column; text-align: center; gap: 16px; }
    .footer-bottom-links { justify-content: center; }
    .footer-col-links a, .footer-btn-link { text-align: center; width: 100%; }
    .footer-status-pill { align-self: center; }
    .footer-brand-col { align-items: center; text-align: center; }
    .demo-body { grid-template-columns: 1fr; }
    .demo-panel:first-child { border-right: none; border-bottom: 1px solid var(--border); }
    .fb-trigger { right: 16px; bottom: 16px; padding: 11px 16px; }
    .fb-panel { right: 16px; bottom: 76px; }
    .fb-email-row { flex-direction: column; }
    .fb-submit { width: 100%; }
  }
`;

function DemoCard() {
  const [state, setState] = useState({ fixing: false, fixed: false, step: 0 });
  const { fixing, fixed, step } = state;
  const genderFixed = step >= 1;
  const dateFixed   = step >= 2;

  function runFix() {
    if (fixed || fixing) return;
    setState(s => ({ ...s, fixing: true }));
    setTimeout(() => {
      setState(s => ({ ...s, step: 1 }));
      setTimeout(() => setState({ fixing: false, fixed: true, step: 2 }), 300);
    }, 800);
  }

  return (
    <div className="demo-card">
      <div className="demo-topbar">
        <div className="demo-dots">
          <div className="demo-dot" style={{ background: '#F87171' }} />
          <div className="demo-dot" style={{ background: '#FBBF24' }} />
          <div className="demo-dot" style={{ background: '#34D399' }} />
        </div>
        <div className="demo-label">POST /validate — live demo</div>
        <div style={{ width: 52 }} />
      </div>

      <div className="demo-body">
        <div className="demo-panel">
          <div className="demo-panel-label">Input</div>
          <div className="demo-code">
            <span className="code-punct">{'{'}</span>{'\n'}
            {'  '}<span className="code-key">"resourceType"</span><span className="code-punct">: </span><span className="code-str">"Patient"</span><span className="code-punct">,</span>{'\n'}
            {'  '}<span className="code-key">"id"</span><span className="code-punct">: </span><span className="code-str">"P101"</span><span className="code-punct">,</span>{'\n'}
            {'  '}<span className="code-key">"gender"</span><span className="code-punct">: </span><span className="code-err">"M"</span><span className="code-punct">,</span>{'\n'}
            {'  '}<span className="code-key">"birthDate"</span><span className="code-punct">: </span><span className="code-err">"15/04/1990"</span>{'\n'}
            <span className="code-punct">{'}'}</span>
          </div>
        </div>
        <div className="demo-panel">
          <div className="demo-panel-label">Fixed output</div>
          <div className="demo-code">
            <span className="code-punct">{'{'}</span>{'\n'}
            {'  '}<span className="code-key">"resourceType"</span><span className="code-punct">: </span><span className="code-str">"Patient"</span><span className="code-punct">,</span>{'\n'}
            {'  '}<span className="code-key">"id"</span><span className="code-punct">: </span><span className="code-str">"P101"</span><span className="code-punct">,</span>{'\n'}
            {'  '}<span className="code-key">"gender"</span><span className="code-punct">: </span>
            <span className={genderFixed ? 'code-fix' : 'code-str'}>{genderFixed ? '"male"' : '"M"'}</span><span className="code-punct">,</span>{'\n'}
            {'  '}<span className="code-key">"birthDate"</span><span className="code-punct">: </span>
            <span className={dateFixed ? 'code-fix' : 'code-str'}>{dateFixed ? '"1990-04-15"' : '"15/04/1990"'}</span>{'\n'}
            <span className="code-punct">{'}'}</span>
          </div>
        </div>
      </div>

      <div className="demo-errors">
        <div className={`demo-error-item${genderFixed ? ' fixed' : ''}`}>
          <div className="demo-error-field">gender</div>
          <div className="demo-error-msg">FHIR accepts male, female, other, unknown</div>
          <div className={`demo-badge ${genderFixed ? 'badge-fixed' : 'badge-error'}`}>{genderFixed ? 'Fixed' : 'Error'}</div>
        </div>
        <div className={`demo-error-item${dateFixed ? ' fixed' : ''}`}>
          <div className="demo-error-field">birthDate</div>
          <div className="demo-error-msg">Requires YYYY-MM-DD format</div>
          <div className={`demo-badge ${dateFixed ? 'badge-fixed' : 'badge-error'}`}>{dateFixed ? 'Fixed' : 'Error'}</div>
        </div>
        <button
          className="demo-fix-btn"
          onClick={runFix}
          disabled={fixing || fixed}
          style={fixed ? { background: 'linear-gradient(135deg,#00D4AA,#00B894)' } : undefined}
        >
          {fixing ? 'Fixing...' : fixed ? '✓ All errors fixed' : '⚡ Auto-fix errors'}
        </button>
      </div>

      <div className="demo-quality">
        <div className={`quality-ring${fixed ? '' : ' grade-b'}`}>{fixed ? 'A' : 'B'}</div>
        <div className="quality-stats">
          <div className="quality-stat">
            <div className="quality-stat-val" style={{ color: 'var(--error)' }}>{fixed ? '0' : '2'}</div>
            <div className="quality-stat-label">Errors</div>
          </div>
          <div className="quality-stat">
            <div className="quality-stat-val" style={{ color: 'var(--teal)' }}>{fixed ? '2' : '0'}</div>
            <div className="quality-stat-label">Fixed</div>
          </div>
          <div className="quality-stat">
            <div className="quality-stat-val" style={{ color: 'var(--accent)' }}>{fixed ? '85%' : '75%'}</div>
            <div className="quality-stat-label">Score</div>
          </div>
        </div>
      </div>
    </div>
  );
}

const roadmapOptions = [
  'More FHIR resources',
  'HL7 v2 support',
  'CSV / Excel import',
  'Bulk validation',
  'Webhook support',
  'FHIR server push',
  'SDK / library',
  'More code lookups',
  'Team accounts',
  'Audit logs',
  'Custom rules',
  'On-premise deploy',
];

function FeedbackWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [email, setEmail] = useState('');
  const [selectedChips, setSelectedChips] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [showInvalid, setShowInvalid] = useState(false);
  const panelRef = useRef(null);
  const triggerRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return undefined;

    function handlePointerDown(event) {
      if (
        panelRef.current?.contains(event.target) ||
        triggerRef.current?.contains(event.target)
      ) {
        return;
      }
      setIsOpen(false);
    }

    function handleKeyDown(event) {
      if (event.key === 'Escape') setIsOpen(false);
    }

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  function toggleChip(option) {
    setSelectedChips(current =>
      current.includes(option)
        ? current.filter(item => item !== option)
        : [...current, option]
    );
  }

  function resetForm() {
    setFeedback('');
    setEmail('');
    setSelectedChips([]);
    setIsSubmitting(false);
    setIsSubmitted(false);
    setShowInvalid(false);
  }

  async function submitFeedback() {
    if (!feedback.trim() && selectedChips.length === 0) {
      setShowInvalid(true);
      setTimeout(() => setShowInvalid(false), 1200);
      return;
    }

    setIsSubmitting(true);

    const payload = {
      feedback: feedback.trim(),
      next_features: selectedChips,
      email: email.trim() || null,
      submitted_at: new Date().toISOString(),
      page: window.location.href,
    };

    try {
      await fetch(`${API_BASE}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      console.warn('Feedback send failed silently:', error);
    }

    setIsSubmitted(true);
    setTimeout(() => {
      setIsOpen(false);
      setTimeout(resetForm, 400);
    }, 3000);
  }

  return (
    <>
      <button
        className="fb-trigger"
        type="button"
        ref={triggerRef}
        onClick={() => setIsOpen(open => !open)}
        aria-expanded={isOpen}
        aria-controls="feedback-panel"
      >
        <span className="fb-trigger-icon" aria-hidden="true" />
        Share feedback
      </button>

      <div
        className={`fb-panel${isOpen ? ' open' : ''}`}
        id="feedback-panel"
        ref={panelRef}
        aria-hidden={!isOpen}
      >
        {!isSubmitted ? (
          <>
            <div className="fb-header">
              <div className="fb-title">Help shape MedTechTools</div>
              <button
                className="fb-close"
                type="button"
                onClick={() => setIsOpen(false)}
                aria-label="Close feedback panel"
              >
                x
              </button>
            </div>

            <div className="fb-body">
              <label className="fb-q-label" htmlFor="fbText">
                What would make MedTechTools useful<br />for your workflow?
              </label>
              <textarea
                className={`fb-textarea${showInvalid ? ' invalid' : ''}`}
                id="fbText"
                placeholder="e.g. I work with HL7 messages and need conversion support..."
                maxLength={500}
                value={feedback}
                onChange={event => setFeedback(event.target.value)}
              />
              <div className={`fb-char${feedback.length > 400 ? ' warn' : ''}`}>
                {feedback.length} / 500
              </div>

              <div className="fb-roadmap-label">What should we build next?</div>
              <div className="fb-chips">
                {roadmapOptions.map(option => (
                  <button
                    className={`fb-chip${selectedChips.includes(option) ? ' selected' : ''}`}
                    type="button"
                    key={option}
                    onClick={() => toggleChip(option)}
                  >
                    {option}
                  </button>
                ))}
              </div>

              <div className="fb-email-row">
                <input
                  className="fb-email"
                  type="email"
                  placeholder="Email (optional)"
                  value={email}
                  onChange={event => setEmail(event.target.value)}
                />
                <button
                  className="fb-submit"
                  type="button"
                  onClick={submitFeedback}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Sending...' : 'Send'}
                </button>
              </div>

              <div className="fb-note">Takes 30 seconds. Anonymous ok</div>
            </div>
          </>
        ) : (
          <div className="fb-success visible">
            <div className="fb-success-icon">OK</div>
            <div className="fb-success-title">Thank you!</div>
            <div className="fb-success-sub">
              Your feedback directly shapes what we build next.<br />
              We read every single response.
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default function LandingPage() {
  const navigate = useNavigate();
  const animRefs = useRef([]);

  const [contactEmail, setContactEmail] = useState('');
  const [contactMessage, setContactMessage] = useState('');
  const [sendingContact, setSendingContact] = useState(false);
  const [contactSuccess, setContactSuccess] = useState(false);

  const handleQuickContact = async (e) => {
    e.preventDefault();
    if (!contactEmail || !contactMessage) return;
    setSendingContact(true);
    try {
      await fetch(`${API_BASE}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feedback: `[Contact Form] ${contactMessage}`,
          email: contactEmail,
          submitted_at: new Date().toISOString(),
          page: window.location.href,
        }),
      });
      setContactSuccess(true);
      setContactEmail('');
      setContactMessage('');
      setTimeout(() => setContactSuccess(false), 4000);
    } catch (err) {
      console.warn('Contact send failed silently:', err);
      // Fallback success for nice UX if server endpoint is offline
      setContactSuccess(true);
      setContactEmail('');
      setContactMessage('');
      setTimeout(() => setContactSuccess(false), 4000);
    } finally {
      setSendingContact(false);
    }
  };

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
      { threshold: 0.1 }
    );
    animRefs.current.forEach(el => { if (el) observer.observe(el); });
    return () => observer.disconnect();
  }, []);

  const addRef = i => el => { animRefs.current[i] = el; };

  const goToApiKey = () => navigate('/api-key');

  const goToDocs = () => navigate('/docs');
  const goToTools = () => navigate('/tools');

  // Tool-specific dashboards. Selecting an available tool should collect an
  // API key first (if the visitor doesn't have one yet), then land on that
  // tool's own dashboard - never the old shared multi-suite dashboard.
  const TOOL_DASHBOARDS = {
    fhir: '/tools/fhir',
    hl7: '/tools/hl7-suite',
    terminology: '/tools/terminology',
    phi: '/tools/phi',
  };

  const selectTool = (toolId) => {
    const hasApiKey = Boolean(localStorage.getItem('smartfhirApiKey'));
    const destination = TOOL_DASHBOARDS[toolId];
    if (!destination) return;
    navigate(hasApiKey ? destination : `/api-key?tool=${toolId}`);
  };

  return (
    <>
      <style>{styles}</style>

      {/* NAV */}
      <nav className="navbar">
        <div className="nav-logo" onClick={() => navigate('/')}>
          <MedTechLogo size={32} />
          MedTechTools
        </div>
        <ul className="nav-links">
          <li><a href="#how">How it works</a></li>
          <li><a href="#features">Features</a></li>
          <li><a href="#pricing">Pricing</a></li>
          <li><a href="/docs" onClick={(e) => { e.preventDefault(); goToDocs(); }}>Docs</a></li>
          <li><a href="/tools" onClick={(e) => { e.preventDefault(); goToTools(); }}>Tools</a></li>
        </ul>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button 
            className="nav-cta" 
            onClick={() => navigate('/tools/api')}
            style={{ 
              background: 'transparent', 
              border: '1px solid var(--border)', 
              color: 'var(--text)' 
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent)';
              e.currentTarget.style.color = 'var(--accent)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border)';
              e.currentTarget.style.color = 'var(--text)';
            }}
          >
            API Docs
          </button>
          <button className="nav-cta" onClick={goToApiKey}>Get API Key →</button>
        </div>
      </nav>

      {/* HERO */}
      <div className="hero">
        <div className="hero-left">
          <div className="hero-badge fade-up">
            <div className="hero-badge-dot" />
            Now in public beta
          </div>
          <h1 className="hero-title fade-up fade-up-2">
            Developers Platform for<br />
            <span className="hero-title-accent">Healthcare Interoperability.</span>
          </h1>
          <p className="hero-sub fade-up fade-up-3">
            MedTechTools provides powerful tools for healthcare developers to validate, transform, and integrate healthcare data across FHIR, HL7, clinical documents, radiology, laboratory, pharmacy, and more.
          </p>
          <div className="hero-actions fade-up fade-up-4">
            <button className="btn-primary" onClick={goToApiKey}>
              Get free API key <span>→</span>
            </button>
            <button className="btn-secondary" onClick={goToDocs}>View docs</button>
          </div>
          
          <div className="hero-highlights fade-up fade-up-4">
            <div className="hero-highlight"><span>⚡</span><span><strong>Fast setup</strong> in under 2 minutes</span></div>
            <div className="hero-highlight"><span>🩺</span><span><strong>Built for</strong> FHIR, HL7, DICOM, CDA workflows</span></div>
            <div className="hero-highlight"><span>✅</span><span><strong>Free tier</strong> with 500 calls/month</span></div>
          </div>
          
          <p className="hero-note fade-up fade-up-4">Start with your email and get an API key immediately. No credit card required.</p>
        </div>
        <div className="hero-right fade-up fade-up-3">
          <DemoCard />
        </div>
      </div>

      {/* STATS */}
      <div className="stats-bar">
        {[['4','Active Tools'],['6','Coming Soon'],['4','Data Standards'],['<200ms','Avg response time']].map(([val,label]) => (
          <div className="stat-item" key={label}>
            <div className="stat-val">{val}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      {/* TOOLS GALLERY */}
      <div className="section">
        <div className="section-eyebrow">Tools Gallery</div>
        <h2 className="section-title">One platform. Every healthcare standard.</h2>
        <p className="section-sub">Access specialized tools for different healthcare data standards from a single unified dashboard.</p>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 16,
          marginTop: 32
        }}>
          {[
            { icon: '🏥', name: 'FHIR Tools', standard: 'FHIR R4', desc: 'Validate, explain, and auto-fix FHIR resources with intelligent field mapping and quality scoring.', status: 'Available', statusColor: 'var(--teal)', toolId: 'fhir' },
            { icon: '📨', name: 'HL7 Suite', standard: 'HL7 v2', desc: 'Parse, validate, and convert HL7 v2 messages with detailed segment and field analysis.', status: 'Available', statusColor: 'var(--teal)', toolId: 'hl7' },
            { icon: '🔬', name: 'Terminology Suite', standard: 'LOINC/SNOMED/RxNorm', desc: 'Lookup medical codes across multiple standard code systems with live API fallback.', status: 'Available', statusColor: 'var(--teal)', toolId: 'terminology' },
            { icon: '🛡️', name: 'PHI De-identifier', standard: 'HIPAA Safe Harbor / Purpose-Based', desc: 'Purpose-driven PHI de-identification (Pseudonymize, Mask, Redact) with automated compliance & audit reports.', status: 'Available', statusColor: 'var(--teal)', toolId: 'phi' },
            { icon: '📄', name: 'Clinical Documents', standard: 'CCD/CDA', desc: 'Generate, validate, and transform clinical documents including CCD, CDA, and care summaries.', status: 'Coming Soon', statusColor: 'var(--dim)' },
            { icon: '🔍', name: 'Radiology Tools', standard: 'DICOM', desc: 'Work with DICOM imaging data, radiology reports, and imaging study metadata.', status: 'Coming Soon', statusColor: 'var(--dim)' },
            { icon: '🧪', name: 'Laboratory Suite', standard: 'LOINC/LAB', desc: 'Process lab orders, results, and reference ranges with comprehensive laboratory data management.', status: 'Coming Soon', statusColor: 'var(--dim)' },
            { icon: '💊', name: 'Pharmacy Tools', standard: 'RxNorm/NDC', desc: 'Manage prescriptions, medication interactions, and pharmacy dispensing workflows.', status: 'Coming Soon', statusColor: 'var(--dim)' },
          ].map((tool, i) => (
            <div key={tool.name} style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 16,
              padding: 24,
              cursor: tool.status === 'Available' ? 'pointer' : 'default',
              transition: 'all 0.2s',
              opacity: tool.status === 'Coming Soon' ? 0.6 : 1,
            }} onClick={tool.status === 'Available' && tool.toolId ? () => selectTool(tool.toolId) : undefined}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div style={{ fontSize: 32 }}>{tool.icon}</div>
                <div style={{
                  fontSize: 11,
                  fontWeight: 600,
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  color: tool.statusColor,
                  padding: '4px 10px',
                  borderRadius: '100px',
                  background: tool.status === 'Available' ? 'rgba(0,212,170,0.1)' : 'rgba(148,163,184,0.1)'
                }}>{tool.status}</div>
              </div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{tool.name}</div>
              <div style={{ fontSize: 12, color: 'var(--accent)', marginBottom: 12 }}>{tool.standard}</div>
              <div style={{ fontSize: 14, color: 'var(--dim)', lineHeight: 1.6 }}>{tool.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="full-divider" />

      {/* BENEFITS */}
      <div className="section">
        <div className="section-eyebrow">Why teams use it</div>
        <h2 className="section-title">Less manual cleanup. More reliable healthcare data.</h2>
        <p className="section-sub">Designed for developers who want trustworthy healthcare data without spending hours debugging schema issues across multiple standards.</p>
        <div className="benefit-grid">
          <div className="benefit-card">
            <div className="benefit-icon">🧠</div>
            <div className="benefit-title">Understand every issue</div>
            <div className="benefit-desc">Get plain-English explanations for invalid values, bad formats, and missing terminology across FHIR, HL7, and clinical documents.</div>
          </div>
          <div className="benefit-card">
            <div className="benefit-icon">⚙️</div>
            <div className="benefit-title">Cut the repetitive fixes</div>
            <div className="benefit-desc">Handle common mapping and formatting problems automatically so your team can focus on integration work.</div>
          </div>
          <div className="benefit-card">
            <div className="benefit-icon">📦</div>
            <div className="benefit-title">Multi-standard support</div>
            <div className="benefit-desc">Work with FHIR, HL7 v2, clinical documents, radiology, laboratory, pharmacy and more from one unified platform.</div>
          </div>
        </div>
      </div>

      <div className="full-divider" />

      {/* CROSS-STANDARD MAPPING */}
      <div className="section">
        <div className="section-eyebrow">Cross-Standard Mapping</div>
        <h2 className="section-title">Translate between healthcare standards.</h2>
        <p className="section-sub">Seamlessly convert data between different healthcare interoperability standards with intelligent mapping and validation.</p>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: 16,
          marginTop: 32
        }}>
          {[
            { 
              from: 'HL7 v2', 
              to: 'FHIR R4', 
              icon: '📨➡️🏥',
              desc: 'Convert HL7 v2 pipe-delimited messages (ADT^A01, ORM^O01) to structured FHIR resources (Patient, Encounter, ServiceRequest).'
            },
            { 
              from: 'CDA', 
              to: 'FHIR Bundles', 
              icon: '📄➡️📦',
              desc: 'Extract clinical data from CCD/CDA documents and transform into FHIR Bundles with Composition, Patient, and Observation resources.'
            },
            { 
              from: 'DICOM', 
              to: 'FHIR ImagingStudy', 
              icon: '🔍➡️🏥',
              desc: 'Parse DICOM metadata and create FHIR ImagingStudy resources with referenced Series and Instance components.'
            },
          ].map((mapping, i) => (
            <div key={i} style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 16,
              padding: 24,
            }}>
              <div style={{ fontSize: 28, marginBottom: 16, textAlign: 'center' }}>{mapping.icon}</div>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                gap: 12,
                marginBottom: 12 
              }}>
                <span style={{ 
                  fontSize: 14, 
                  fontWeight: 600, 
                  color: 'var(--accent)',
                  background: 'rgba(79,142,247,0.1)',
                  padding: '6px 12px',
                  borderRadius: '8px'
                }}>{mapping.from}</span>
                <span style={{ fontSize: 18, color: 'var(--dim)' }}>➡️</span>
                <span style={{ 
                  fontSize: 14, 
                  fontWeight: 600, 
                  color: 'var(--teal)',
                  background: 'rgba(0,212,170,0.1)',
                  padding: '6px 12px',
                  borderRadius: '8px'
                }}>{mapping.to}</span>
              </div>
              <div style={{ fontSize: 14, color: 'var(--dim)', lineHeight: 1.6, textAlign: 'center' }}>
                {mapping.desc}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="full-divider" />

      {/* HOW IT WORKS */}
      <div className="section" id="how">
        <div className="section-eyebrow">How it works</div>
        <h2 className="section-title">One platform. Multiple healthcare standards.</h2>
        <p className="section-sub">Send your raw healthcare data and get back validated, explained, and corrected resources across FHIR, HL7, and more without manual cleanup.</p>
        <div className="how-grid">
          <div className="how-step" ref={addRef(0)}>
            <div className="how-step-num">Step 01</div>
            <div className="how-step-icon">🗺️</div>
            <div className="how-step-title">Map your fields</div>
            <div className="how-step-desc">
              Send any field names. MedTechTools maps{' '}
              <code style={{color:'var(--accent)',fontFamily:'monospace'}}>PtID</code>,{' '}
              <code style={{color:'var(--accent)',fontFamily:'monospace'}}>DOB</code>,{' '}
              <code style={{color:'var(--accent)',fontFamily:'monospace'}}>Sex</code>{' '}
              to correct FHIR fields automatically. Custom mappings saved for future calls.
            </div>
            <div className="how-code">
              <span className="hl">PtID</span> → Patient.id{'\n'}
              <span className="hl">DOB</span>{'  '}→ Patient.birthDate{'\n'}
              <span className="hl">Sex</span>{'  '}→ Patient.gender
            </div>
          </div>
          <div className="how-step" ref={addRef(1)}>
            <div className="how-step-num">Step 02</div>
            <div className="how-step-icon">🔍</div>
            <div className="how-step-title">Validate & explain</div>
            <div className="how-step-desc">Every error explained in plain English — not cryptic schema messages. Includes LOINC, SNOMED, and RxNorm code lookups built in.</div>
            <div className="how-code">
              <span className="hl">gender: "M"</span>{'\n'}
              → FHIR accepts male, female,{'\n'}
              {'  '}other, unknown
            </div>
          </div>
          <div className="how-step" ref={addRef(2)}>
            <div className="how-step-num">Step 03</div>
            <div className="how-step-icon">⚡</div>
            <div className="how-step-title">Auto-fix & score</div>
            <div className="how-step-desc">Known errors fixed automatically. Complex issues explained with suggested fixes. Quality grade from A+ to D tells you exactly where you stand.</div>
            <div className="how-code">
              <span className="hl">"M"</span> → <span style={{color:'var(--teal)'}}>"male"</span>{'\n'}
              <span className="hl">"15/04/1990"</span> → <span style={{color:'var(--teal)'}}>"1990-04-15"</span>{'\n'}
              Grade: <span style={{color:'var(--teal)'}}>A</span> | Score: <span style={{color:'var(--teal)'}}>85%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="full-divider" />

      {/* API EXAMPLE */}
      <div className="section" id="docs">
        <div className="section-eyebrow">API</div>
        <h2 className="section-title">Dead simple to integrate.</h2>
        <p className="section-sub">Request a key first from `/register`, then call `/bundle` with `X-API-Key` and a patient-centered bundle payload. Works with curl, Python, or any HTTP client.</p>
        <div className="code-block">
          <span className="cb-comment"># 1. Request your API key</span>{'\n'}
          <span className="cb-kw">curl</span>{' -X POST http://localhost:8000/register \\\n'}
          {'  -H '}<span className="cb-str">"Content-Type: application/json"</span>{' \\\n'}
          {'  -d '}<span className="cb-str">{'\'{\n    "email": "you@company.com"\n  }\''}</span>{'\n\n'}
          <span className="cb-comment"># 2. Send bundle request</span>{'\n'}
          <span className="cb-kw">curl</span>{' -X POST http://localhost:8000/bundle \\\n'}
          {'  -H '}<span className="cb-str">"X-API-Key: sk_live_xxxxxxxxxxxx"</span>{' \\\n'}
          {'  -H '}<span className="cb-str">"Content-Type: application/json"</span>{' \\\n'}
          {'  -d '}<span className="cb-str">{'\'{\n    "patient": {\n      "id": "P101",\n      "gender": "M",\n      "birthDate": "15/04/1990"\n    },\n    "observations": [\n      {"code": "Glucose", "value": 90}\n    ],\n    "conditions": [\n      {"code": "Hypertension", "clinicalStatus": "active"}\n    ],\n    "encounters": [\n      {"subject": "P101", "status": "finished", "class": "ambulatory"}\n    ],\n    "medications": [\n      {"subject": "P101", "medication": "Lisinopril", "status": "active", "intent": "order"}\n    ]\n  }\''}</span>{'\n\n'}
          <span className="cb-comment"># Python example</span>{'\n'}
          <span className="cb-kw">python</span>{' -c '}
          <span className="cb-str">{'"import requests\n'}
          {'payload = {\n    "patient": {\n      "id": "P101",\n      "gender": "M",\n      "birthDate": "15/04/1990"\n    },\n    "observations": [\n      {"code": "Glucose", "value": 90}\n    ],\n    "conditions": [\n      {"code": "Hypertension", "clinicalStatus": "active"}\n    ],\n    "encounters": [\n      {"subject": "P101", "status": "finished", "class": "ambulatory"}\n    ],\n    "medications": [\n      {"subject": "P101", "medication": "Lisinopril", "status": "active", "intent": "order"}\n    ]\n  }\n'}
          {'headers = {"X-API-Key": "sk_live_xxxxxxxxxxxx", "Content-Type": "application/json"}\n'}
          {'response = requests.post("http://localhost:8000/bundle", json=payload, headers=headers)\n'}
          {'print(response.json())"'}</span>{'\n\n'}
          <span className="cb-comment"># Response</span>{'\n'}
          <span className="cb-punct">{'{'}</span>{'\n'}
          {'  '}<span className="cb-key">"quality"</span><span className="cb-punct">:</span>{'  { '}<span className="cb-key">"grade"</span><span className="cb-punct">:</span> <span className="cb-str">"A"</span><span className="cb-punct">,</span> <span className="cb-key">"score"</span><span className="cb-punct">:</span> <span className="cb-num">85</span>{' },\n'}
          {'  '}<span className="cb-key">"errors"</span><span className="cb-punct">:</span>{'  [ '}<span className="cb-str">"gender: M → male"</span><span className="cb-punct">,</span> <span className="cb-str">"birthDate: reformatted"</span>{' ],\n'}
          {'  '}<span className="cb-key">"fixed"</span><span className="cb-punct">:</span>{'   { '}<span className="cb-key">"gender"</span><span className="cb-punct">:</span> <span className="cb-str">"male"</span><span className="cb-punct">,</span> <span className="cb-key">"birthDate"</span><span className="cb-punct">:</span> <span className="cb-str">"1990-04-15"</span>{' }\n'}
          <span className="cb-punct">{'}'}</span>
        </div>
      </div>

      <div className="full-divider" />

      {/* FEATURES */}
      <div className="section" id="features">
        <div className="section-eyebrow">Features</div>
        <h2 className="section-title">Everything you need.<br />Nothing you don't.</h2>
        <div className="features-grid">
          {[
            { icon:'🛡️', bg:'rgba(52,211,153,0.1)',  title:'Purpose-Based PHI De-Identification', desc:'Context-aware anonymization for AI, Research, Analytics, & Vendor Sharing. Configurable rules (pseudonymize, mask, redact) with automated audit compliance reports.', tag:'HIPAA · Safe Harbor · Audit Logs' },
            { icon:'🗺️', bg:'rgba(79,142,247,0.1)',  title:'Smart Field Mapping',     desc:'Built-in rules for 50+ common field aliases across multiple standards. Save your own mappings — they apply on every future call automatically.',                                tag:'FHIR · HL7 · Clinical Docs' },
            { icon:'🔬', bg:'rgba(0,212,170,0.1)',   title:'Medical Code Lookup',      desc:'Automatic LOINC codes for lab tests, SNOMED CT for diagnoses, RxNorm for medications. Built-in common codes plus live API fallback.',            tag:'LOINC · SNOMED CT · RxNorm' },
            { icon:'💡', bg:'rgba(251,191,36,0.1)',  title:'Human-Readable Errors',    desc:'No more cryptic schema messages. Every error explained in plain English with the exact fix required. AI-powered for complex cases.',               tag:'Rule-based + Gemini AI hybrid' },
            { icon:'⚡', bg:'rgba(248,113,113,0.1)', title:'Auto-Fix Engine',          desc:'Gender values, date formats, status codes, enum values — fixed automatically. One API call returns a clean, valid resource.',                 tag:'M→male · 15/04/1990→1990-04-15 · ongoing→active' },
            { icon:'🏥', bg:'rgba(192,132,252,0.1)', title:'Business Rule Validation', desc:'Clinical logic checks beyond schema validation. Impossible dates, unrealistic ages, medication conflicts, date ordering errors.',                   tag:'Age · Dates · Dosage · Clinical conflicts' },
            { icon:'📊', bg:'rgba(79,142,247,0.1)',  title:'Quality Scoring',          desc:'Every resource gets a quality grade from A+ to D. Schema score, terminology score, business rules score — all in one response.',                   tag:'A+ · A · B · C · D grades' },
          ].map((f, i) => (
            <div className="feature-card" key={f.title} ref={addRef(3 + i)}>
              <div className="feature-icon" style={{ background: f.bg }}>{f.icon}</div>
              <div className="feature-title">{f.title}</div>
              <div className="feature-desc">{f.desc}</div>
              <div className="feature-tag">{f.tag}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="full-divider" />

      {/* BUNDLE GENERATION */}
      <div className="section">
        <div className="section-eyebrow">Bundle Generation</div>
        <h2 className="section-title">Complete patient records.<br />One API call.</h2>
        <p className="section-sub">Generate complete FHIR bundles containing patient data and all related resources. Perfect for EHR integration and clinical data exchange.</p>
        
        <div style={{
          background: 'var(--surface)',
          border: `1px solid var(--border)`,
          borderRadius: 16,
          padding: 32,
          marginTop: 32,
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20, marginBottom: 32 }}>
            {[
              { icon: '👤', name: 'Patient', desc: 'Core patient demographics and identifiers' },
              { icon: '🔬', name: 'Observations', desc: 'Lab results, vital signs, measurements' },
              { icon: '🏥', name: 'Conditions', desc: 'Diagnoses, problems, health issues' },
              { icon: '📅', name: 'Encounters', desc: 'Visits, admissions, procedures' },
              { icon: '💊', name: 'Medications', desc: 'Prescriptions, drug orders, treatments' },
            ].map((item, i) => (
              <div key={item.name} style={{
                background: 'var(--bg)',
                border: `1px solid var(--border)`,
                borderRadius: 12,
                padding: 20,
                textAlign: 'center',
              }}>
                <div style={{ fontSize: 32, marginBottom: 12 }}>{item.icon}</div>
                <div style={{ 
                  color: 'var(--text)', 
                  fontSize: 15, 
                  fontWeight: 600, 
                  marginBottom: 8 
                }}>{item.name}</div>
                <div style={{ color: 'var(--muted)', fontSize: 13, lineHeight: 1.5 }}>{item.desc}</div>
              </div>
            ))}
          </div>

          <div style={{
            background: 'rgba(79,142,247,0.08)',
            border: `1px solid rgba(79,142,247,0.2)`,
            borderRadius: 12,
            padding: 24,
          }}>
            <h3 style={{ fontSize: 18, margin: '0 0 16px', color: 'var(--accent)' }}>Why Bundle Generation?</h3>
            <ul style={{ 
              listStyle: 'none', 
              padding: 0, 
              margin: 0,
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: 12,
            }}>
              {[
                '📦 Complete patient context in one response',
                '🔗 Automatic resource linking and references',
                '✅ All resources validated and fixed together',
                '🎯 FHIR R4 compliant output',
                '⚡ Single API call replaces multiple requests',
                '🏥 Ready for EHR system integration',
              ].map((item, i) => (
                <li key={i} style={{ 
                  color: 'var(--text)', 
                  fontSize: 14,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}>{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: 32 }}>
          <button className="btn-primary" onClick={() => selectTool('fhir')}>
            Try bundle generation <span>→</span>
          </button>
        </div>
      </div>


      {/* COMING SOON */}
      <div className="section">
        <div className="section-eyebrow">Coming Soon</div>
        <h2 className="section-title">More tools on the roadmap.</h2>
        <p className="section-sub">We're expanding beyond FHIR and HL7 to cover the full spectrum of healthcare data interoperability.</p>
        <div className="benefit-grid">
          <div className="benefit-card">
            <div className="benefit-icon">📄</div>
            <div className="benefit-title">Clinical Documents</div>
            <div className="benefit-desc">Generate, validate, and transform clinical documents including CCD, CDA, and structured care summaries.</div>
          </div>
          <div className="benefit-card">
            <div className="benefit-icon">🔍</div>
            <div className="benefit-title">Radiology Tools</div>
            <div className="benefit-desc">Work with DICOM imaging data, radiology reports, and imaging study metadata.</div>
          </div>
          <div className="benefit-card">
            <div className="benefit-icon">🧪</div>
            <div className="benefit-title">Laboratory Suite</div>
            <div className="benefit-desc">Process lab orders, results, and reference ranges with comprehensive laboratory data management.</div>
          </div>
          <div className="benefit-card">
            <div className="benefit-icon">💊</div>
            <div className="benefit-title">Pharmacy Tools</div>
            <div className="benefit-desc">Manage prescriptions, medication interactions, and pharmacy dispensing workflows.</div>
          </div>
        </div>
      </div>

      <div className="full-divider" />

      {/* PRICING */}
      <div className="section" id="pricing">
        <div className="section-eyebrow">Pricing</div>
        <h2 className="section-title">Start free while V1 learns.</h2>
        <p className="section-sub">Paid plans are coming later. For launch, the free API key is the recommended way to try MedTechTools.</p>
        <div className="pricing-grid">
          {[
            { tier:'Free',       price:'$0',    period:'/mo', calls:'500 API calls/month',    featured:true, btnClass:'pricing-btn-filled', btnText:'Get free API key', disabled:false,
              features:['Recommended for V1 launch','Validation + explain','Auto-fix engine','Mapping','Quality scoring','No credit card required'],
              off:[] },
            { tier:'Starter',    price:'Coming Soon', period:'', calls:'For higher usage after V1', featured:false, btnClass:'pricing-btn-disabled', btnText:'Coming Soon', disabled:true,
              features:['More monthly calls','Team workflows','Usage insights'],
              off:[] },
            { tier:'Pro',        price:'Coming Soon', period:'', calls:'For production integrations', featured:false, btnClass:'pricing-btn-disabled', btnText:'Coming Soon', disabled:true,
              features:['Advanced API usage','Priority feedback channel','Expanded endpoints'],
              off:[] },
            { tier:'Enterprise', price:'Coming Soon', period:'', calls:'For custom healthcare needs', featured:false, btnClass:'pricing-btn-disabled', btnText:'Coming Soon', disabled:true,
              features:['Custom resource types','SLA options','Dedicated support'],
              off:[] },
          ].map((plan, i) => (
            <div key={plan.tier} className={`pricing-card${plan.featured ? ' featured' : ''}`} ref={addRef(9 + i)}>
              {plan.featured && <div className="pricing-popular">Recommended Start</div>}
              <div className="pricing-tier">{plan.tier}</div>
              <div className="pricing-price" style={plan.tier === 'Enterprise' ? {fontSize:28} : undefined}>
                {plan.price}{plan.period && <span>{plan.period}</span>}
              </div>
              <div className="pricing-calls">{plan.calls}</div>
              <div className="pricing-divider" />
              <ul className="pricing-features">
                {plan.features.map(f => <li key={f}>{f}</li>)}
                {plan.off.map(f => <li key={f} className="off">{f}</li>)}
              </ul>
              <button
                className={`pricing-btn ${plan.btnClass}`}
                onClick={plan.disabled ? undefined : goToApiKey}
                disabled={plan.disabled}
              >
                {plan.btnText}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="cta-section">
        <h2 className="cta-title">Stop debugging healthcare data.<br />Start shipping.</h2>
        <p className="cta-sub">Get your free API key in 30 seconds. 500 calls/month, no credit card required.</p>
        <div style={{ display: 'flex', gap: '12px', maxWidth: '480px', margin: '32px auto 0', justifyContent: 'center' }}>
          <button className="btn-primary" onClick={goToApiKey}>Get free API key</button>
        </div>
      </div>

      {/* FOOTER */}
      <footer className="footer-new">
        <div className="footer-grid">
          {/* Brand & Contact Info Column */}
          <div className="footer-brand-col">
            <div className="footer-logo">
              <MedTechLogo size={32} />
              MedTechTools
            </div>
            <p className="footer-brand-desc">
              Developer Platform for Healthcare Interoperability. Validate, transform, and integrate clinical data across FHIR, HL7, and medical terms.
            </p>
    
            <div className="footer-socials">
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="footer-social-link" title="GitHub">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              </a>
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="footer-social-link" title="Twitter">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/></svg>
              </a>
              <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="footer-social-link" title="LinkedIn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
              </a>
            </div>
          </div>

          {/* Column 2: Helpful Links */}
          <div className="footer-links-col">
            <h4 className="footer-col-title">Helpful Links</h4>
            <ul className="footer-col-links">
              <li><button onClick={() => selectTool('fhir')} className="footer-btn-link">FHIR Validation</button></li>
              <li><button onClick={() => selectTool('hl7')} className="footer-btn-link">HL7 Suite Page</button></li>
              <li><button onClick={() => selectTool('terminology')} className="footer-btn-link">Terminology Lookup</button></li>
              <li><button onClick={() => selectTool('phi')} className="footer-btn-link">PHI De-identifier</button></li>
              <li><button onClick={goToTools} className="footer-btn-link">Explore Tools Suite</button></li>
            </ul>
          </div>

          {/* Column 3: Resources */}
          <div className="footer-links-col">
            <h4 className="footer-col-title">Resources</h4>
            <ul className="footer-col-links">
              <li><a href="/docs" onClick={(e) => { e.preventDefault(); goToDocs(); }}>Documentation</a></li>
              <li><a href="/#pricing">Beta Pricing</a></li>
              <li><a href="https://github.com" target="_blank" rel="noopener noreferrer">GitHub Repo</a></li>
              <li><a href="/#docs">API References</a></li>
              <li>
                <span className="footer-status-pill">
                  <span className="footer-status-dot"></span> All Systems Operational
                </span>
              </li>
            </ul>
          </div>

          {/* Column 4: Contact Us Quick Form */}
          <div className="footer-contact-col">
            <h4 className="footer-col-title">Contact Us</h4>
            <form onSubmit={handleQuickContact} className="footer-contact-form">
              <div className="footer-form-group">
                <input 
                  type="email" 
                  placeholder="Your work email" 
                  className="footer-form-input" 
                  value={contactEmail} 
                  onChange={(e) => setContactEmail(e.target.value)}
                  required 
                />
              </div>
              <div className="footer-form-group">
                <textarea 
                  placeholder="How can we help?" 
                  className="footer-form-textarea" 
                  value={contactMessage}
                  onChange={(e) => setContactMessage(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="footer-form-btn" disabled={sendingContact}>
                {sendingContact ? 'Sending...' : 'Send Message'}
              </button>
              {contactSuccess && (
                <div className="footer-form-success">
                  ✓ Message sent. We will reply soon!
                </div>
              )}
            </form>
          </div>
        </div>

        <div className="footer-bottom">
          <div className="footer-copy">© 2026 MedTechTools. Built for healthcare developers.</div>
          <div className="footer-bottom-links">
            <a href="#privacy">Privacy Policy</a>
            <a href="#terms">Terms of Service</a>
            <a href="#security">Security (HIPAA)</a>
          </div>
        </div>
      </footer>

      <FeedbackWidget />
    </>
  );
}