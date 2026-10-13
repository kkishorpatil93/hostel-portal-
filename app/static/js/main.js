/**
 * StayNest PG - Core Frontend Interaction Script
 */

document.addEventListener('DOMContentLoaded', () => {
  // Theme Toggle (Light / Dark mode persistence)
  const themeToggle = document.getElementById('theme-toggle');
  const themeIcon = themeToggle ? themeToggle.querySelector('.theme-icon') : null;
  const currentTheme = localStorage.getItem('staynest-theme') || (
    window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  );

  document.documentElement.setAttribute('data-theme', currentTheme);
  if (themeIcon) {
    themeIcon.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const activeTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('staynest-theme', newTheme);
      if (themeIcon) {
        themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
      }
    });
  }

  // Mobile Menu Toggle
  const mobileBtn = document.getElementById('mobile-menu-btn');
  const mainNav = document.getElementById('main-nav');
  if (mobileBtn && mainNav) {
    mobileBtn.addEventListener('click', () => {
      const isExpanded = mainNav.style.display === 'flex';
      mainNav.style.display = isExpanded ? 'none' : 'flex';
      mainNav.style.flexDirection = 'column';
      mainNav.style.position = 'absolute';
      mainNav.style.top = '68px';
      mainNav.style.left = '0';
      mainNav.style.width = '100%';
      mainNav.style.background = 'var(--bg-surface)';
      mainNav.style.padding = '1rem';
      mainNav.style.borderBottom = '1px solid var(--border-color)';
    });
  }
});
