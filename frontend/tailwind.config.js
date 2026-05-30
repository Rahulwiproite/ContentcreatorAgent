/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', "ui-monospace", "monospace"],
        display: ['"Orbitron"', '"Space Grotesk"', "system-ui", "sans-serif"],
      },
      colors: {
        bg: "#05060d",
        panel: "rgba(255,255,255,0.04)",
        line: "rgba(255,255,255,0.08)",
        neon: {
          cyan: "#22d3ee",
          violet: "#a78bfa",
          pink: "#f472b6",
          lime: "#a3e635",
        },
      },
      animation: {
        "scan": "scan 6s linear infinite",
        "pulse-slow": "pulse 3s cubic-bezier(0.4,0,0.6,1) infinite",
        "spin-slow": "spin 8s linear infinite",
        "fade-up": "fadeUp 0.5s ease-out",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        fadeUp: {
          "0%": { opacity: 0, transform: "translateY(12px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        glow: {
          "0%": { boxShadow: "0 0 24px rgba(34,211,238,0.25)" },
          "100%": { boxShadow: "0 0 56px rgba(167,139,250,0.55)" },
        },
      },
    },
  },
  plugins: [],
};
