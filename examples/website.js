// SPDX-License-Identifier: Apache-2.0. Keep documentation and speech choices independent.
const requestedGallery = new URLSearchParams(location.search);
document.addEventListener('DOMContentLoaded', () => {
  const gallery = document.querySelector('.gallery-content');
  const selector = document.querySelector('#site-language');
  if (!gallery || !selector) return;
  const reflectLanguage = () => {
    gallery.lang = currentPageLanguage;
    document.documentElement.lang = selector.value;
    document.querySelector('#translation-notice').hidden = !['nb', 'pl'].includes(selector.value) || currentPageLanguage !== 'en';
    const url = new URL(location.href);
    url.searchParams.set('lang', selector.value);
    url.searchParams.set('filter', gallery.querySelector('[data-language-value][aria-pressed="true"]').dataset.languageValue);
    history.replaceState({}, '', url);
  };
  const selectLanguage = () => {
    setLanguageFilter(PAGE_LANGUAGES.has(selector.value) ? selector.value : 'en');
    reflectLanguage();
  };
  const filter = requestedGallery.get('filter');
  const requested = requestedGallery.get('lang');
  if (filter === 'all' || PAGE_LANGUAGES.has(filter)) {setLanguageFilter(filter); reflectLanguage();}
  else if (PAGE_LANGUAGES.has(requested) && ![...selector.options].some(option => option.value === requested)) {setLanguageFilter(requested); reflectLanguage();}
  else selectLanguage();
  selector.addEventListener('change', selectLanguage);
  for (const button of gallery.querySelectorAll('[data-language-value]')) button.addEventListener('click', reflectLanguage);
});
