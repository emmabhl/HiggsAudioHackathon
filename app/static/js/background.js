// ===== Gradient Animation =====
const body = document.body;
const colors = [
  "#0a0f0a", "#0f150a", "#11210f", "#153a1a",
  "#184d1e", "#1b5f21", "#1d7125"
];

let currentA = colors[0];
let currentB = colors[1];
let targetA = colors[2];
let targetB = colors[3];
let t = 0;

function randomColor() {
  return colors[Math.floor(Math.random() * colors.length)];
}

function lerpColor(a, b, t) {
  const ah = +("0x" + a.slice(1));
  const bh = +("0x" + b.slice(1));
  const r = (ah >> 16) + t * ((bh >> 16) - (ah >> 16));
  const g = ((ah >> 8) & 0xff) + t * (((bh >> 8) & 0xff) - ((ah >> 8) & 0xff));
  const bl = (ah & 0xff) + t * ((bh & 0xff) - (ah & 0xff));
  return `rgb(${r | 0},${g | 0},${bl | 0})`;
}

function animateGradient() {
  t += 0.002;
  if (t >= 1) {
    t = 0;
    currentA = targetA;
    currentB = targetB;
    targetA = randomColor();
    targetB = randomColor();
  }
  const bgA = lerpColor(currentA, targetA, t);
  const bgB = lerpColor(currentB, targetB, t);
  body.style.background = `linear-gradient(135deg, ${bgA}, ${bgB})`;
  requestAnimationFrame(animateGradient);
}

animateGradient();


