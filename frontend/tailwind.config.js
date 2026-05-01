export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        paper:        '#F5F0E6',
        'paper-deep': '#EDE5D3',
        ink:          '#1A1614',
        'ink-soft':   '#4A413A',
        'ink-mute':   '#8A7E72',
        rule:         '#D9CFB8',
        'rule-soft':  '#E5DCC6',
        tomato:       '#B8341B',
        'tomato-deep':'#8A2412',
        'tomato-soft':'#F2E0DA',
        leaf:         '#3D5A2A',
        amber:        '#A86A1F',
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        body:    ['Inter Tight', 'Inter', 'sans-serif'],
        mono:    ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '2px',
        sm:      '2px',
        md:      '2px',
        lg:      '2px',
        xl:      '4px',
        '2xl':   '4px',
        full:    '9999px',
      },
    },
  },
  plugins: [],
}
