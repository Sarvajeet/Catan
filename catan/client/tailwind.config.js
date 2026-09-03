/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        catan: {
          bg: "#0f1f2e",
          panel: "#13283d",
          panel2: "#1c3553",
          sea: "#2d6aa0",
          lumber: "#27632a",
          brick: "#b34722",
          wool: "#8ac64a",
          grain: "#e6b23a",
          ore: "#6d7784",
          desert: "#d9b26b",
        },
      },
      fontFamily: {
        display: ['"Outfit"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
