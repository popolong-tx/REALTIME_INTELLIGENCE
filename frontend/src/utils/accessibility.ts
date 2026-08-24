// Accessibility utilities for WCAG 2.2 AA compliance

// Color contrast utilities
export const getContrastRatio = (foreground: string, background: string): number => {
  const getLuminance = (hex: string): number => {
    const rgb = hexToRgb(hex);
    if (!rgb) return 0;

    const [r, g, b] = [rgb.r, rgb.g, rgb.b].map((c) => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };

  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);

  return (lighter + 0.05) / (darker + 0.05);
};

export const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
};

export const meetsContrastRequirement = (
  foreground: string,
  background: string,
  level: 'AA' | 'AAA' = 'AA',
  size: 'normal' | 'large' = 'normal'
): boolean => {
  const ratio = getContrastRatio(foreground, background);

  if (level === 'AAA') {
    return size === 'large' ? ratio >= 4.5 : ratio >= 7;
  }

  return size === 'large' ? ratio >= 3 : ratio >= 4.5;
};

// ARIA utilities
export const generateId = (prefix: string = 'id'): string => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

export const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite'): void => {
  const announcer = document.createElement('div');
  announcer.setAttribute('aria-live', priority);
  announcer.setAttribute('aria-atomic', 'true');
  announcer.setAttribute('class', 'sr-only');
  announcer.textContent = message;

  document.body.appendChild(announcer);

  setTimeout(() => {
    document.body.removeChild(announcer);
  }, 1000);
};

// Focus management
export const trapFocus = (element: HTMLElement): (() => void) => {
  const focusableElements = element.querySelectorAll(
    'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select, [tabindex]:not([tabindex="-1"])'
  );

  const firstFocusable = focusableElements[0] as HTMLElement;
  const lastFocusable = focusableElements[focusableElements.length - 1] as HTMLElement;

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      if (document.activeElement === firstFocusable) {
        lastFocusable.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === lastFocusable) {
        firstFocusable.focus();
        e.preventDefault();
      }
    }
  };

  element.addEventListener('keydown', handleKeyDown);
  firstFocusable?.focus();

  return () => {
    element.removeEventListener('keydown', handleKeyDown);
  };
};

// Keyboard navigation
export const handleArrowKeyNavigation = (
  e: KeyboardEvent,
  items: HTMLElement[],
  currentIndex: number,
  onIndexChange: (index: number) => void
): void => {
  let newIndex = currentIndex;

  switch (e.key) {
    case 'ArrowDown':
    case 'ArrowRight':
      e.preventDefault();
      newIndex = (currentIndex + 1) % items.length;
      break;
    case 'ArrowUp':
    case 'ArrowLeft':
      e.preventDefault();
      newIndex = (currentIndex - 1 + items.length) % items.length;
      break;
    case 'Home':
      e.preventDefault();
      newIndex = 0;
      break;
    case 'End':
      e.preventDefault();
      newIndex = items.length - 1;
      break;
    default:
      return;
  }

  onIndexChange(newIndex);
  items[newIndex]?.focus();
};

// Skip link
export const createSkipLink = (targetId: string, label: string): HTMLElement => {
  const skipLink = document.createElement('a');
  skipLink.href = `#${targetId}`;
  skipLink.textContent = label;
  skipLink.className = 'sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded';
  skipLink.setAttribute('tabindex', '0');

  return skipLink;
};

// Reduced motion detection
export const prefersReducedMotion = (): boolean => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

// High contrast detection
export const prefersHighContrast = (): boolean => {
  return window.matchMedia('(prefers-contrast: high)').matches;
};

// Screen reader detection
export const isScreenReaderActive = (): boolean => {
  return window.matchMedia('(screen-reader: active)').matches;
};

// ARIA attributes helpers
export const ariaAttributes = {
  button: (label: string, pressed?: boolean) => ({
    'aria-label': label,
    ...(pressed !== undefined && { 'aria-pressed': pressed }),
  }),
  link: (label: string, current?: boolean) => ({
    'aria-label': label,
    ...(current && { 'aria-current': 'page' }),
  }),
  dialog: (label: string, describedBy?: string) => ({
    'aria-modal': true,
    'aria-label': label,
    ...(describedBy && { 'aria-describedby': describedBy }),
  }),
  tab: (selected: boolean, controls: string) => ({
    role: 'tab',
    'aria-selected': selected,
    'aria-controls': controls,
    tabIndex: selected ? 0 : -1,
  }),
  tabpanel: (labelledBy: string) => ({
    role: 'tabpanel',
    'aria-labelledby': labelledBy,
    tabIndex: 0,
  }),
  alert: (live: 'polite' | 'assertive' = 'assertive') => ({
    role: 'alert',
    'aria-live': live,
    'aria-atomic': true,
  }),
  progressbar: (value: number, max: number = 100, label?: string) => ({
    role: 'progressbar',
    'aria-valuenow': value,
    'aria-valuemin': 0,
    'aria-valuemax': max,
    ...(label && { 'aria-label': label }),
  }),
};

// Form accessibility
export const formAccessibility = {
  input: (id: string, label: string, error?: string, required?: boolean) => ({
    id,
    'aria-label': label,
    'aria-required': required,
    'aria-invalid': !!error,
    ...(error && { 'aria-describedby': `${id}-error` }),
  }),
  errorMessage: (id: string) => ({
    id: `${id}-error`,
    role: 'alert',
    'aria-live': 'polite',
  }),
};

// Table accessibility
export const tableAccessibility = {
  sortableHeader: (label: string, sorted: boolean, direction: 'asc' | 'desc') => ({
    'aria-label': `${label}, ${sorted ? `sorted ${direction}` : 'not sorted'}`,
    'aria-sort': sorted ? (direction === 'asc' ? 'ascending' : 'descending') : 'none',
  }),
};

// Image accessibility
export const imageAccessibility = {
  decorative: () => ({
    alt: '',
    'aria-hidden': true,
    role: 'presentation',
  }),
  informative: (alt: string) => ({
    alt,
  }),
};

export default {
  getContrastRatio,
  meetsContrastRequirement,
  generateId,
  announceToScreenReader,
  trapFocus,
  handleArrowKeyNavigation,
  createSkipLink,
  prefersReducedMotion,
  prefersHighContrast,
  isScreenReaderActive,
  ariaAttributes,
  formAccessibility,
  tableAccessibility,
  imageAccessibility,
};
