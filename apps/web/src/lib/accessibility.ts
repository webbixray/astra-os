export function trapFocus(element: HTMLElement): () => void {
  const focusableElements = element.querySelectorAll<HTMLElement>(
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  );

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key !== 'Tab') return;

    if (event.shiftKey) {
      if (document.activeElement === firstElement) {
        event.preventDefault();
        lastElement?.focus();
      }
    } else {
      if (document.activeElement === lastElement) {
        event.preventDefault();
        firstElement?.focus();
      }
    }
  }

  element.addEventListener('keydown', handleKeyDown);
  firstElement?.focus();

  return () => {
    element.removeEventListener('keydown', handleKeyDown);
  };
}

export function announceToScreenReader(message: string, priority?: 'polite' | 'assertive'): void {
  const announcer = document.createElement('div');
  announcer.setAttribute('aria-live', priority || 'polite');
  announcer.setAttribute('aria-atomic', 'true');
  announcer.setAttribute('class', 'sr-only');
  announcer.textContent = message;
  document.body.appendChild(announcer);

  setTimeout(() => {
    document.body.removeChild(announcer);
  }, 1000);
}

export function generateId(prefix?: string): string {
  const random = Math.random().toString(36).substring(2, 9);
  return prefix ? `${prefix}-${random}` : random;
}

export function getAriaDescribedBy(id: string): { 'aria-describedby': string } {
  return { 'aria-describedby': id };
}

export function getAriaLabelledBy(id: string): { 'aria-labelledby': string } {
  return { 'aria-labelledby': id };
}

export function isInteractiveElement(element: HTMLElement): boolean {
  const interactiveSelectors = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ];

  return interactiveSelectors.some((selector) => element.matches(selector));
}

export function focusFirstFocusableElement(container: HTMLElement): boolean {
  const focusable = container.querySelector<HTMLElement>(
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  );

  if (focusable) {
    focusable.focus();
    return true;
  }

  return false;
}

export function handleEscapeKey(event: KeyboardEvent, callback: () => void): void {
  if (event.key === 'Escape') {
    callback();
  }
}

export function handleEnterOrSpace(event: KeyboardEvent, callback: () => void): void {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    callback();
  }
}
