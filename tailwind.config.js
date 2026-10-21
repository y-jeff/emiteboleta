/** Configuración de Tailwind. Compila con: tailwindcss -i static/src/app.css -o static/css/app.css --minify */
module.exports = {
  content: ["./templates/**/*.html", "./boletas/**/*.py", "./cuentas/**/*.py"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"] },
      colors: { brand: { DEFAULT: "#1e40af", dark: "#1e3a8a", light: "#eff6ff" } },
    },
  },
  plugins: [],
};
