function rgb(hex: string): number[] { return [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)); }
export function luminance(hex: string): number { return rgb(hex).map(n => { const v = n / 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }).reduce((sum, v, i) => sum + v * [0.2126, 0.7152, 0.0722][i], 0); }
export function contrast(a: string, b: string): number { const x = luminance(a), y = luminance(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
export function accentForeground(hex: string): string { return contrast(hex, '#000000') >= contrast(hex, '#ffffff') ? '#000000' : '#ffffff'; }
export function readableAccent(hex: string, background: string): string {
  const values = rgb(hex), target = luminance(background) < 0.5 ? 255 : 0;
  for (let step = 0; step <= 100; step++) {
    const candidate = '#' + values.map(n => Math.round(n + (target - n) * step / 100).toString(16).padStart(2, '0')).join('');
    if (contrast(candidate, background) >= 4.5) return candidate;
  }
  return target ? '#ffffff' : '#000000';
}
