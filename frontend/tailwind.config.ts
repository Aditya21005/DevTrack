import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "Inter", "system-ui", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: "hsl(var(--card))",
        primary: "hsl(var(--primary))",
        success: "hsl(var(--success))",
        warning: "hsl(var(--warning))",
        accent: "hsl(var(--accent))",
        muted: "hsl(var(--muted))",
        ring: "hsl(var(--ring))",
      },
      boxShadow: {
        panel: "0 18px 60px rgba(23, 32, 42, 0.12)",
      },
    },
  },
  plugins: [],
} satisfies Config;
