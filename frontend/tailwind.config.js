export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        clinical: {
          bg: "#070b12",
          panel: "rgba(13, 22, 35, 0.78)",
          line: "rgba(126, 170, 210, 0.18)",
          cyan: "#38d8ff",
          green: "#33d69f",
          amber: "#f8c14a",
          red: "#ff5468",
        },
      },
      boxShadow: {
        monitor: "0 18px 60px rgba(0, 0, 0, 0.42)",
        glow: "0 0 28px rgba(56, 216, 255, 0.16)",
      },
    },
  },
  plugins: [],
}
