const body = document.body;
const themeToggle = document.querySelector('.theme-toggle');
const themeToggleIcon = document.querySelector('.theme-toggle__icon');
const navToggle = document.querySelector('.nav__toggle');
const navLinks = document.querySelector('.nav__links');
const yearEl = document.getElementById('year');

const THEMES = {
  DARK: 'dark',
  LIGHT: 'light'
};

function setTheme(theme) {
  if (theme === THEMES.LIGHT) {
    body.classList.add('light-theme');
    themeToggleIcon.textContent = '☀️';
  } else {
    body.classList.remove('light-theme');
    themeToggleIcon.textContent = '🌙';
  }
  localStorage.setItem('preferred-theme', theme);
}

function toggleTheme() {
  const isLight = body.classList.toggle('light-theme');
  setTheme(isLight ? THEMES.LIGHT : THEMES.DARK);
}

function initTheme() {
  const stored = localStorage.getItem('preferred-theme');
  if (stored === THEMES.LIGHT) {
    body.classList.add('light-theme');
    themeToggleIcon.textContent = '☀️';
  }
}

function closeMenu() {
  navLinks.classList.remove('is-open');
  navToggle.setAttribute('aria-expanded', 'false');
}

function handleNavClick(event) {
  if (event.target.matches('a')) {
    closeMenu();
  }
}

function handleOutsideClick(event) {
  if (!navLinks.contains(event.target) && !navToggle.contains(event.target)) {
    closeMenu();
  }
}

function updateActiveLink() {
  const sections = document.querySelectorAll('section[id]');
  const scrollPos = window.scrollY + 140;

  sections.forEach((section) => {
    const link = document.querySelector(`.nav__links a[href="#${section.id}"]`);
    if (!link) return;

    if (scrollPos >= section.offsetTop && scrollPos < section.offsetTop + section.offsetHeight) {
      link.classList.add('is-active');
    } else {
      link.classList.remove('is-active');
    }
  });
}

function initAnimations() {
  const animated = document.querySelectorAll('[data-animate]');
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
      threshold: 0.2
    }
  );

  animated.forEach((element) => observer.observe(element));
}

function init() {
  initTheme();
  initAnimations();
  updateActiveLink();

  themeToggle.addEventListener('click', toggleTheme);

  navToggle.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('is-open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
    document.addEventListener('click', handleOutsideClick, { once: true });
  });

  navLinks.addEventListener('click', handleNavClick);
  window.addEventListener('scroll', updateActiveLink);

  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }
}

document.addEventListener('DOMContentLoaded', init);
