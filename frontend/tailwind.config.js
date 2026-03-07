/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Primary Gold/Yellow
        "primary": "#dab80b",
        "primary-hover": "#bfa10a",
        "primary-dark": "#b89b09",
        
        // Background Colors
        "background-light": "#f8f8f5",
        "background-dark": "#221f10",
        
        // Coffee Theme
        "coffee-dark": "#181711",
        "coffee-medium": "#2d2a1e",
        "coffee-light": "#393628",
        
        // Cream Colors
        "cream": "#f1f0ea",
        "cream-muted": "#bab59c",
        "cream-pill": "#fdfcf5",
        
        // Surface Colors
        "surface-dark": "#27251b",
        "surface-border": "#393628",
        
        // Text Colors
        "text-muted": "#bab59c",
      },
      fontFamily: {
        "display": ["Inter", "sans-serif"],
        "body": ["Inter", "sans-serif"],
      },
      borderRadius: {
        "DEFAULT": "0.5rem",
        "lg": "1rem",
        "xl": "1.5rem",
        "2xl": "2rem",
        "full": "9999px",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in-up": "fadeInUp 0.5s ease-out forwards",
        "waveform": "waveform 1s ease-in-out infinite",
      },
      keyframes: {
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        waveform: {
          "0%, 100%": { transform: "scaleY(1)" },
          "50%": { transform: "scaleY(1.5)" },
        },
      },
      boxShadow: {
        "primary": "0 0 15px rgba(218, 184, 11, 0.2)",
        "primary-lg": "0 0 30px rgba(218, 184, 11, 0.3)",
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
