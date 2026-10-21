/** Configuración de Tailwind. Compila con: tailwindcss -i static/src/app.css -o static/css/app.css --minify */
module.exports = {
  content: ["./templates/**/*.html", "./boletas/**/*.py", "./cuentas/**/*.py"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"] },
      colors: {
        // Paleta del logo: azul -> celeste sobre azul noche y violeta
        brand: { DEFAULT: "#2563eb", dark: "#1d4ed8", light: "#eff6ff" },
        noche: "#0b1f52",
        violeta: "#2e1763",
      },
    },
  },
  plugins: [],
};
