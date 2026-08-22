/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/*.tsx", "./src/components/**/*.{js,jsx,ts,tsx}", "./src/screens/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {},
  },
  plugins: [],
}
