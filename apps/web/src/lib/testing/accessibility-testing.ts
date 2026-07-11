export interface AccessibilityIssue {
  element: string;
  rule: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  wcagLevel: 'A' | 'AA' | 'AAA';
  fix?: string;
}

export interface AccessibilityReport {
  issues: AccessibilityIssue[];
  score: number;
  passed: number;
  failed: number;
  timestamp: number;
}

export class AccessibilityTester {
  private issues: AccessibilityIssue[] = [];

  async test(container: HTMLElement): Promise<AccessibilityReport> {
    this.issues = [];

    this.checkImages(container);
    this.checkLinks(container);
    this.checkForms(container);
    this.checkHeadings(container);
    this.checkColorContrast(container);
    this.checkAriaLabels(container);
    this.checkKeyboardNavigation(container);
    this.checkSemanticHTML(container);

    const passed = this.issues.filter((i) => i.severity === 'error').length === 0
      ? 1
      : 0;
    const failed = this.issues.filter((i) => i.severity === 'error').length;

    return {
      issues: [...this.issues],
      score: Math.max(0, 100 - failed * 10),
      passed,
      failed,
      timestamp: Date.now(),
    };
  }

  private checkImages(container: HTMLElement): void {
    const images = container.querySelectorAll('img');
    images.forEach((img) => {
      if (!img.alt && !img.getAttribute('aria-label') && !img.getAttribute('aria-hidden')) {
        this.addIssue({
          element: img.outerHTML.slice(0, 100),
          rule: 'img-alt',
          severity: 'error',
          message: 'Image must have alt text',
          wcagLevel: 'A',
          fix: 'Add alt attribute or aria-hidden="true"',
        });
      }
    });
  }

  private checkLinks(container: HTMLElement): void {
    const links = container.querySelectorAll('a');
    links.forEach((link) => {
      if (!link.textContent?.trim() && !link.getAttribute('aria-label')) {
        this.addIssue({
          element: link.outerHTML.slice(0, 100),
          rule: 'link-text',
          severity: 'error',
          message: 'Link must have text content',
          wcagLevel: 'A',
          fix: 'Add text content or aria-label',
        });
      }

      if (link.href.startsWith('http') && !link.getAttribute('rel')?.includes('noopener')) {
        this.addIssue({
          element: link.outerHTML.slice(0, 100),
          rule: 'link-target',
          severity: 'warning',
          message: 'External links should use rel="noopener noreferrer"',
          wcagLevel: 'A',
          fix: 'Add rel="noopener noreferrer" to external links',
        });
      }
    });
  }

  private checkForms(container: HTMLElement): void {
    const inputs = container.querySelectorAll('input, select, textarea');
    inputs.forEach((input) => {
      const id = input.id;
      const label = id ? container.querySelector(`label[for="${id}"]`) : null;
      const ariaLabel = input.getAttribute('aria-label');
      const ariaLabelledby = input.getAttribute('aria-labelledby');

      if (!label && !ariaLabel && !ariaLabelledby && input.type !== 'hidden') {
        this.addIssue({
          element: input.outerHTML.slice(0, 100),
          rule: 'form-label',
          severity: 'error',
          message: 'Form input must have a label',
          wcagLevel: 'A',
          fix: 'Add a label element or aria-label',
        });
      }
    });
  }

  private checkHeadings(container: HTMLElement): void {
    const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let previousLevel = 0;

    headings.forEach((heading) => {
      const level = parseInt(heading.tagName[1]);
      if (level > previousLevel + 1 && previousLevel !== 0) {
        this.addIssue({
          element: heading.outerHTML.slice(0, 100),
          rule: 'heading-order',
          severity: 'warning',
          message: `Heading level skipped from h${previousLevel} to h${level}`,
          wcagLevel: 'A',
          fix: 'Use sequential heading levels',
        });
      }
      previousLevel = level;
    });
  }

  private checkColorContrast(container: HTMLElement): void {
    const elements = container.querySelectorAll('*');
    elements.forEach((element) => {
      const style = window.getComputedStyle(element);
      const color = style.color;
      const bgColor = style.backgroundColor;

      if (color && bgColor && color !== 'rgb(0, 0, 0)' && bgColor !== 'rgba(0, 0, 0, 0)') {
        // Simplified contrast check
        const contrast = this.calculateContrast(color, bgColor);
        if (contrast < 4.5) {
          this.addIssue({
            element: element.outerHTML.slice(0, 100),
            rule: 'color-contrast',
            severity: 'error',
            message: `Insufficient color contrast: ${contrast.toFixed(2)}:1`,
            wcagLevel: 'AA',
            fix: 'Increase color contrast to at least 4.5:1',
          });
        }
      }
    });
  }

  private calculateContrast(color1: string, color2: string): number {
    // Simplified contrast calculation
    return 4.5; // Placeholder
  }

  private checkAriaLabels(container: HTMLElement): void {
    const interactiveElements = container.querySelectorAll(
      'button, [role="button"], [role="tab"], [role="menuitem"]',
    );

    interactiveElements.forEach((element) => {
      if (!element.textContent?.trim() && !element.getAttribute('aria-label')) {
        this.addIssue({
          element: element.outerHTML.slice(0, 100),
          rule: 'aria-label',
          severity: 'error',
          message: 'Interactive element must have accessible name',
          wcagLevel: 'A',
          fix: 'Add text content or aria-label',
        });
      }
    });
  }

  private checkKeyboardNavigation(container: HTMLElement): void {
    const interactiveElements = container.querySelectorAll(
      'a, button, input, select, textarea, [tabindex]',
    );

    interactiveElements.forEach((element) => {
      const tabindex = element.getAttribute('tabindex');
      if (tabindex && parseInt(tabindex) > 0) {
        this.addIssue({
          element: element.outerHTML.slice(0, 100),
          rule: 'tabindex',
          severity: 'warning',
          message: 'Positive tabindex values are discouraged',
          wcagLevel: 'A',
          fix: 'Use tabindex="0" or manage focus order with JavaScript',
        });
      }
    });
  }

  private checkSemanticHTML(container: HTMLElement): void {
    const divsUsedAsButtons = container.querySelectorAll('div[onclick], span[onclick]');
    divsUsedAsButtons.forEach((element) => {
      this.addIssue({
        element: element.outerHTML.slice(0, 100),
        rule: 'semantic-html',
        severity: 'warning',
        message: 'Use semantic HTML elements instead of div with onclick',
        wcagLevel: 'A',
        fix: 'Use <button> or <a> instead of <div> with onclick',
      });
    });
  }

  private addIssue(issue: AccessibilityIssue): void {
    this.issues.push(issue);
  }

  getIssues(): AccessibilityIssue[] {
    return [...this.issues];
  }

  clear(): void {
    this.issues = [];
  }
}

export async function testAccessibility(
  container: HTMLElement,
): Promise<AccessibilityReport> {
  const tester = new AccessibilityTester();
  return tester.test(container);
}

export function reportAccessibility(report: AccessibilityReport): void {
  console.log('\n=== Accessibility Report ===');
  console.log(`Score: ${report.score}/100`);
  console.log(`Issues: ${report.issues.length}`);

  if (report.issues.length > 0) {
    console.log('\nIssues:');
    report.issues.forEach((issue) => {
      console.log(`  [${issue.severity.toUpperCase()}] ${issue.rule}: ${issue.message}`);
      if (issue.fix) {
        console.log(`    Fix: ${issue.fix}`);
      }
    });
  }
}
