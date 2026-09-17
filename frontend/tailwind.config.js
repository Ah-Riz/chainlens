/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#E6EBEF",
        surface: "#F4F7F9",
        ink: "#0B1220",
        muted: "#5A6A7A",
        line: "#C5D0DA",
        accent: "#0F766E",
        amber: "#B45309",
        pale: {
          red: "#FDEBEC",
          blue: "#E0F2FE",
          green: "#CCFBF1",
          yellow: "#FEF3C7",
          teal: "#CCFBF1",
        },
      },
      fontFamily: {
        display: ['"Sora"', "system-ui", "sans-serif"],
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        lift: "0 4px 16px rgba(11, 18, 32, 0.06)",
      },
      keyframes: {
        "scan-sweep": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        "fade-up": {
          from: { opacity: "0", transform: "translateY(12px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "scan-sweep": "scan-sweep 2.2s ease-in-out infinite",
        "fade-up": "fade-up 600ms cubic-bezier(0.16, 1, 0.3, 1) both",
      },
    },
  },
  plugins: [],
};
