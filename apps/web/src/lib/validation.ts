export interface ValidationError {
  field: string;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

export type ValidationRule<T> = {
  validate: (value: T, formData: Record<string, unknown>) => boolean;
  message: string;
};

export function validateRequired(value: unknown, fieldName: string): ValidationError | null {
  if (value === null || value === undefined || value === '') {
    return { field: fieldName, message: `${fieldName} is required` };
  }
  return null;
}

export function validateEmail(value: string): ValidationError | null {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) {
    return { field: 'email', message: 'Invalid email address' };
  }
  return null;
}

export function validateUrl(value: string): ValidationError | null {
  try {
    new URL(value);
    return null;
  } catch {
    return { field: 'url', message: 'Invalid URL' };
  }
}

export function validateMinLength(value: string, min: number, fieldName: string): ValidationError | null {
  if (value.length < min) {
    return { field: fieldName, message: `${fieldName} must be at least ${min} characters` };
  }
  return null;
}

export function validateMaxLength(value: string, max: number, fieldName: string): ValidationError | null {
  if (value.length > max) {
    return { field: fieldName, message: `${fieldName} must be at most ${max} characters` };
  }
  return null;
}

export function validatePattern(value: string, pattern: RegExp, fieldName: string, message: string): ValidationError | null {
  if (!pattern.test(value)) {
    return { field: fieldName, message };
  }
  return null;
}

export function validateNumber(value: string, fieldName: string): ValidationError | null {
  if (isNaN(Number(value))) {
    return { field: fieldName, message: `${fieldName} must be a number` };
  }
  return null;
}

export function validateMin(value: number, min: number, fieldName: string): ValidationError | null {
  if (value < min) {
    return { field: fieldName, message: `${fieldName} must be at least ${min}` };
  }
  return null;
}

export function validateMax(value: number, max: number, fieldName: string): ValidationError | null {
  if (value > max) {
    return { field: fieldName, message: `${fieldName} must be at most ${max}` };
  }
  return null;
}

export function validateDate(value: string, fieldName: string): ValidationError | null {
  const date = new Date(value);
  if (isNaN(date.getTime())) {
    return { field: fieldName, message: `${fieldName} must be a valid date` };
  }
  return null;
}

export function validateDateRange(
  startDate: string,
  endDate: string,
  fieldName: string,
): ValidationError | null {
  const start = new Date(startDate);
  const end = new Date(endDate);
  if (start > end) {
    return { field: fieldName, message: 'Start date must be before end date' };
  }
  return null;
}

export function validatePhone(value: string): ValidationError | null {
  const phoneRegex = /^\+?[1-9]\d{1,14}$/;
  if (!phoneRegex.test(value.replace(/[\s\-()]/g, ''))) {
    return { field: 'phone', message: 'Invalid phone number' };
  }
  return null;
}

export function validatePassword(value: string): ValidationError | null {
  const errors: string[] = [];

  if (value.length < 8) errors.push('at least 8 characters');
  if (!/[A-Z]/.test(value)) errors.push('an uppercase letter');
  if (!/[a-z]/.test(value)) errors.push('a lowercase letter');
  if (!/[0-9]/.test(value)) errors.push('a number');
  if (!/[!@#$%^&*]/.test(value)) errors.push('a special character (!@#$%^&*)');

  if (errors.length > 0) {
    return { field: 'password', message: `Password must contain ${errors.join(', ')}` };
  }
  return null;
}

export function validateConfirmPassword(password: string, confirmPassword: string): ValidationError | null {
  if (password !== confirmPassword) {
    return { field: 'confirmPassword', message: 'Passwords do not match' };
  }
  return null;
}

export function validateForm(
  data: Record<string, unknown>,
  rules: Record<string, ValidationRule<unknown>[]>,
): ValidationResult {
  const errors: ValidationError[] = [];

  for (const [field, fieldRules] of Object.entries(rules)) {
    const value = data[field];

    for (const rule of fieldRules) {
      if (!rule.validate(value, data)) {
        errors.push({ field, message: rule.message });
        break;
      }
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

export function getFieldError(errors: ValidationError[], field: string): string | undefined {
  return errors.find((e) => e.field === field)?.message;
}

export function hasFieldError(errors: ValidationError[], field: string): boolean {
  return errors.some((e) => e.field === field);
}
