import type { Config } from "tailwindcss";
import forms from "@tailwindcss/forms";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./node_modules/@tremor/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    {
      pattern: /^(bg|text|border|ring|fill|stroke)-(amber|zinc|red)-(50|100|200|300|400|500|600|700|800|900|950)$/,
      variants: ["hover", "ui-selected"],
    },
  ],
  darkMode: "class",
  theme: {
    transparent: "transparent",
    current: "currentColor",
    extend: {
      colors: {
        tremor: {
          brand: { faint: "#fffbeb", muted: "#fef3c7", subtle: "#fcd34d", DEFAULT: "#d97706", emphasis: "#92400e", inverted: "#ffffff" },
          background: { muted: "#fafafa", subtle: "#f4f4f5", DEFAULT: "#ffffff", emphasis: "#3f3f46" },
          border: { DEFAULT: "#e4e4e7" },
          ring: { DEFAULT: "#d4d4d8" },
          content: { subtle: "#a1a1aa", DEFAULT: "#71717a", emphasis: "#52525b", strong: "#18181b", inverted: "#ffffff" },
        },
        "dark-tremor": {
          brand: { faint: "#451a03", muted: "#78350f", subtle: "#b45309", DEFAULT: "#f59e0b", emphasis: "#fcd34d", inverted: "#18181b" },
          background: { muted: "#18181b", subtle: "#27272a", DEFAULT: "#3f3f46", emphasis: "#d4d4d8" },
          border: { DEFAULT: "#52525b" },
          ring: { DEFAULT: "#71717a" },
          content: { subtle: "#71717a", DEFAULT: "#a1a1aa", emphasis: "#d4d4d8", strong: "#fafafa", inverted: "#18181b" },
        },
      },
      boxShadow: {
        "tremor-input": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        "tremor-card": "0 1px 3px 0 rgb(0 0 0 / 0.08)",
        "tremor-dropdown": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
      },
      borderRadius: { "tremor-small": "0.5rem", "tremor-default": "0.75rem", "tremor-full": "9999px" },
      fontSize: {
        "tremor-label": ["0.75rem", { lineHeight: "1rem" }],
        "tremor-default": ["0.875rem", { lineHeight: "1.25rem" }],
        "tremor-title": ["1.125rem", { lineHeight: "1.75rem" }],
        "tremor-metric": ["1.875rem", { lineHeight: "2.25rem" }],
      },
    },
  },
  plugins: [forms],
};
export default config;
