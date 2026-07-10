'use client';

import { useCallback, useState } from 'react';
import type { ZodSchema, ZodError } from 'zod';

export interface FieldErrors {
  [field: string]: string | undefined;
}

export function useFormValidation<T extends Record<string, unknown>>(schema: ZodSchema<T>) {
  const [errors, setErrors] = useState<FieldErrors>({});

  const validate = useCallback(
    (data: unknown): data is T => {
      const result = schema.safeParse(data);
      if (result.success) {
        setErrors({});
        return true;
      }
      const fieldErrors: FieldErrors = {};
      for (const issue of (result.error as ZodError).issues) {
        const path = issue.path.join('.');
        fieldErrors[path] = issue.message;
      }
      setErrors(fieldErrors);
      return false;
    },
    [schema],
  );

  const clearErrors = useCallback(() => setErrors({}), []);
  const clearFieldError = useCallback((field: string) => {
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  }, []);

  return { errors, validate, clearErrors, clearFieldError };
}
