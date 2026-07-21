import React from "react";

export default function MedTechLogo({ size = 32, showText = false, tagline = false, onClick, style = {} }) {
  // Generate unique IDs for gradients to prevent conflicts when multiple logos are rendered
  const uniqueId = React.useId();
  const blueGradId = `m-blue-grad-${uniqueId}`;
  const tealGradId = `m-teal-grad-${uniqueId}`;

  return (
    <div 
      onClick={onClick}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: size * 0.3,
        cursor: onClick ? "pointer" : "default",
        userSelect: "none",
        ...style
      }}
    >
      {/* MedTech Icon Mark */}
      <svg
        width={size}
        height={size}
        viewBox="0 0 512 512"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ flexShrink: 0, borderRadius: size > 40 ? 12 : 8 }}
      >
        <defs>
          {/* Left Stem Gradient (Blue) */}
          <linearGradient id={blueGradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#2563EB" />
            <stop offset="100%" stopColor="#3B82F6" />
          </linearGradient>
          
          {/* Right Stem Gradient (Teal/Cyan) */}
          <linearGradient id={tealGradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3B82F6" />
            <stop offset="50%" stopColor="#06B6D4" />
            <stop offset="100%" stopColor="#00D4AA" />
          </linearGradient>
        </defs>

        <g transform="translate(46, 30)">
          {/* Main M Body Left & Center */}
          <path d="M 65 80
                   C 45 80, 30 95, 30 120
                   L 30 290
                   C 30 310, 45 325, 65 325
                   L 85 325
                   C 105 325, 120 310, 120 290
                   L 120 200
                   L 195 295
                   C 205 308, 215 308, 225 295
                   L 300 200
                   L 300 290
                   C 300 310, 315 325, 335 325
                   L 355 325
                   C 375 325, 390 310, 390 290
                   L 390 120
                   C 390 95, 375 80, 355 80
                   L 335 80
                   C 315 80, 300 95, 290 110
                   L 210 215
                   L 130 110
                   C 120 95, 105 80, 85 80
                   Z"
                fill={`url(#${blueGradId})`} />

          {/* Right Stem Teal Gradient Overlay */}
          <path d="M 210 215
                   L 290 110
                   C 300 95, 315 80, 335 80
                   L 355 80
                   C 375 80, 390 95, 390 120
                   L 390 290
                   C 390 310, 375 325, 355 325
                   L 335 325
                   C 315 325, 300 310, 300 290
                   L 300 200
                   Z"
                fill={`url(#${tealGradId})`} />

          {/* Pixel Data Blocks on Bottom Left */}
          <rect x="0" y="270" width="18" height="18" rx="4" fill="#2563EB" opacity="0.9" />
          <rect x="22" y="270" width="18" height="18" rx="4" fill="#3B82F6" opacity="0.95" />
          <rect x="0" y="292" width="18" height="18" rx="4" fill="#1D4ED8" opacity="0.85" />
          <rect x="22" y="292" width="22" height="22" rx="5" fill="#3B82F6" opacity="0.95" />
          <rect x="48" y="292" width="16" height="16" rx="3" fill="#60A5FA" opacity="0.9" />
          <rect x="22" y="246" width="16" height="16" rx="3" fill="#2563EB" opacity="0.8" />
          <rect x="48" y="268" width="16" height="16" rx="3" fill="#3B82F6" opacity="0.85" />
          <rect x="68" y="292" width="14" height="14" rx="3" fill="#93C5FD" opacity="0.9" />

          {/* Medical Cross '+' Cutout on Right Stem */}
          <g transform="translate(325, 255)">
            <rect x="18" y="6" width="12" height="36" rx="4" fill="#0A0E1A" />
            <rect x="6" y="18" width="36" height="12" rx="4" fill="#0A0E1A" />
          </g>
        </g>
      </svg>

      {/* Brand Text (Optional) */}
      {showText && (
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{
            fontFamily: "'Space Grotesk', system-ui, sans-serif",
            fontWeight: 700,
            fontSize: size * 0.55,
            lineHeight: 1.1,
            letterSpacing: "-0.02em"
          }}>
            <span style={{
              background: "linear-gradient(135deg, #3B82F6, #60A5FA)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}>
              MedTech
            </span>
            <span style={{ color: "#FFFFFF" }}>Tools</span>
          </div>
          {tagline && (
            <div style={{
              fontSize: size * 0.22,
              fontWeight: 700,
              color: "#94A3B8",
              letterSpacing: "0.15em",
              textTransform: "uppercase",
              marginTop: 2
            }}>
              BUILD • VALIDATE • TRANSFORM • PROTECT
            </div>
          )}
        </div>
      )}
    </div>
  );
}
