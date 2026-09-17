/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F7F6F3",
        surface: "#FFFFFF",
        ink: "#111111",
        muted: "#787774",
        line: "#EAEAEA",
        pale: {
          red: "#FDEBEC",
          blue: "#E1F3FE",
          green: "#EDF3EC",
          yellow: "#FBF3DB",
        },
      },
      fontFamily: {
        display: ['"Newsreader"', "Georgia", "serif"],
        sans: ['"Geist"', '"Helvetica Neue"', "Helvetica", "sans-serif"],
        mono: ['"Geist Mono"', '"SF Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        lift: "0 2px 8px rgba(0,0,0,0.04)",
      },
    },
  },
  plugins: [],
};
