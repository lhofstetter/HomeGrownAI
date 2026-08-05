/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/app/*.tsx", "./src/components/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {},
  },
  plugins: [],
}

