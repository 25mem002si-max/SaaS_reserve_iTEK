import type { Config } from "tailwindcss";

// Design system mobile-first, ultra-léger (cf. cahier des charges)
const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#1E3A8A",
          light: "#3B82F6",
        },
        accent: "#F59E0B",
        success: "#16A34A",
        danger: "#DC2626",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
