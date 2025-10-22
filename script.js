const navToggle = document.querySelector('.nav__toggle');
const navLinks = document.querySelector('.nav__links');
const themeToggle = document.querySelector('.theme-toggle');
const themeIcon = document.querySelector('.theme-toggle__icon');
const root = document.documentElement;
const form = document.getElementById('contact-form');
const statusText = document.querySelector('.form__status');
const year = document.getElementById('year');

if (year) {
  year.textContent = new Date().getFullYear();
}

const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');

function setTheme(theme) {
  if (theme === 'light') {
    root.setAttribute('data-theme', 'light');
    themeIcon.textContent = '☀️';
  } else {
    root.setAttribute('data-theme', 'dark');
    themeIcon.textContent = '🌙';
  }
  localStorage.setItem('preferred-theme', theme);
}

const savedTheme = localStorage.getItem('preferred-theme');
if (savedTheme) {
  setTheme(savedTheme);
} else {
  setTheme(prefersDark.matches ? 'dark' : 'light');
}

prefersDark.addEventListener('change', (event) => {
  if (!localStorage.getItem('preferred-theme')) {
    setTheme(event.matches ? 'dark' : 'light');
  }
});

themeToggle?.addEventListener('click', () => {
  const isLight = root.getAttribute('data-theme') === 'light';
  setTheme(isLight ? 'dark' : 'light');
});

navToggle?.addEventListener('click', () => {
  navLinks?.classList.toggle('is-open');
});

navLinks?.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', () => navLinks.classList.remove('is-open'));
});

form?.addEventListener('submit', (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const nombre = formData.get('nombre');

  statusText.textContent = 'Enviando...';
  setTimeout(() => {
    statusText.textContent = `¡Gracias ${nombre}! Tu mensaje ha sido registrado. Responderé en breve.`;
    form.reset();
  }, 900);
});

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  },
  {
    threshold: 0.2,
  }
);

document.querySelectorAll('.section, .timeline__item, .card, .skills__group').forEach((element) => {
  element.classList.add('will-animate');
  observer.observe(element);
});
