import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { z } from 'zod';
import { useFormValidation } from './validation';

const testSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  age: z.number().min(18, 'Must be 18 or older'),
});

describe('useFormValidation', () => {
  it('returns valid for correct data', () => {
    const { result } = renderHook(() => useFormValidation(testSchema));
    act(() => {
      const valid = result.current.validate({ name: 'Alice', email: 'alice@test.com', age: 25 });
      expect(valid).toBe(true);
    });
    expect(result.current.errors).toEqual({});
  });

  it('returns invalid and sets errors for wrong data', () => {
    const { result } = renderHook(() => useFormValidation(testSchema));
    act(() => {
      const valid = result.current.validate({ name: '', email: 'not-an-email', age: 15 });
      expect(valid).toBe(false);
    });
    expect(result.current.errors.name).toBe('Name is required');
    expect(result.current.errors.email).toBe('Invalid email');
    expect(result.current.errors.age).toBe('Must be 18 or older');
  });

  it('clears errors on subsequent valid validation', () => {
    const { result } = renderHook(() => useFormValidation(testSchema));
    act(() => {
      result.current.validate({ name: '', email: '', age: 0 });
    });
    expect(result.current.errors.name).toBeDefined();

    act(() => {
      const valid = result.current.validate({ name: 'Bob', email: 'bob@test.com', age: 30 });
      expect(valid).toBe(true);
    });
    expect(result.current.errors).toEqual({});
  });

  it('clears all errors with clearErrors', () => {
    const { result } = renderHook(() => useFormValidation(testSchema));
    act(() => {
      result.current.validate({ name: '', email: '', age: 0 });
    });
    expect(Object.keys(result.current.errors).length).toBeGreaterThan(0);

    act(() => {
      result.current.clearErrors();
    });
    expect(result.current.errors).toEqual({});
  });

  it('clears a single field error with clearFieldError', () => {
    const { result } = renderHook(() => useFormValidation(testSchema));
    act(() => {
      result.current.validate({ name: '', email: 'bad', age: 0 });
    });
    expect(result.current.errors.name).toBeDefined();
    expect(result.current.errors.email).toBeDefined();

    act(() => {
      result.current.clearFieldError('name');
    });
    expect(result.current.errors.name).toBeUndefined();
    expect(result.current.errors.email).toBeDefined();
  });

  it('handles deeply nested paths', () => {
    const nestedSchema = z.object({
      user: z.object({
        address: z.object({
          city: z.string().min(1, 'City is required'),
        }),
      }),
    });
    const { result } = renderHook(() => useFormValidation(nestedSchema));
    act(() => {
      const valid = result.current.validate({ user: { address: { city: '' } } });
      expect(valid).toBe(false);
    });
    expect(result.current.errors['user.address.city']).toBe('City is required');
  });

  it('stays referentially stable across renders', () => {
    const { result, rerender } = renderHook(() => useFormValidation(testSchema));
    const { validate, clearErrors, clearFieldError } = result.current;

    rerender();

    expect(result.current.validate).toBe(validate);
    expect(result.current.clearErrors).toBe(clearErrors);
    expect(result.current.clearFieldError).toBe(clearFieldError);
  });
});
