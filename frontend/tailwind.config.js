/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Brand-neutral palette — swap when product design lands.
        brand: {
          50: "#f5f7f5",
          100: "#e6ebe6",
          500: "#3b6e3f",
          600: "#2f5c33",
          700: "#26492a",
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "PingFang SC",
          "Microsoft YaHei",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};