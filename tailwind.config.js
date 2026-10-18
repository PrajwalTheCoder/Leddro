/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#111214',
          secondary: '#17191C',
          panel: '#1D2024',
          elevated: '#24272C',
          hover: '#292D33',
        },
        border: {
          DEFAULT: '#30343A',
          subtle: '#22252A',
          strong: '#3F444C',
        },
        text: {
          primary: '#F3F4F6',
          secondary: '#A0A5AD',
          muted: '#727780',
        },
        accent: {
          DEFAULT: '#D8E7A2',
          hover: '#C7D791',
          muted: 'rgba(216, 231, 162, 0.12)',
          border: 'rgba(216, 231, 162, 0.28)',
        },
        semantic: {
          success: '#80B89A',
          warning: '#D8B16C',
          error: '#D78383',
          info: '#91B7D8',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '4px',
        sm: '3px',
        md: '6px',
        lg: '8px',
        xl: '10px',
      },
      boxShadow: {
        'panel': '0 4px 12px rgba(0, 0, 0, 0.35)',
        'dropdown': '0 8px 24px rgba(0, 0, 0, 0.5)',
      }
    },
  },
  plugins: [],
}
