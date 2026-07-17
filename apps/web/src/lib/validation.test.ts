import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { z } from 'zod';
import { useFormValidation, getFieldError } from './validation';

const testSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  age: z.number().min(18, 'Must be 18 or older'),
});

describe('useFormValidation', () => {
  it('returns formData with initial values', () => {
    const { result } = renderHook(() => useFormValidation(testSchema, {
      name: 'Alice',
      email: 'alice@test.com',
      age: 25,
    }));
    expect(result.current.formData.name).toBe('Alice');
    expect(result.current.formData.email).toBe('alice@test.com');
    expect(result.current.formData.age).toBe(25);
    expect(result.current.errors).toEqual([]);
  });

  it('sets errors on invalid data when handleSubmit is called', () => {
    const { result } = renderHook(() => useFormValidation(testSchema, {
      name: '',
      email: 'not-an-email',
      age: 15,
    }));

    const onSubmit = vi.fn();
    act(() => {
      result.current.handleSubmit(onSubmit)({
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent);
    });

    expect(onSubmit).not.toHaveBeenCalled();
    expect(getFieldError(result.current.errors, 'name')).toBe('Name is required');
    expect(getFieldError(result.current.errors, 'email')).toBe('Invalid email');
    expect(getFieldError(result.current.errors, 'age')).toBe('Must be 18 or older');
  });

  it('calls onSubmit with valid data', () => {
    const { result } = renderHook(() => useFormValidation(testSchema, {
      name: 'Bob',
      email: 'bob@test.com',
      age: 30,
    }));

    const onSubmit = vi.fn();
    act(() => {
      result.current.handleSubmit(onSubmit)({
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent);
    });

    expect(onSubmit).toHaveBeenCalledWith({
      name: 'Bob',
      email: 'bob@test.com',
      age: 30,
    });
  });

  it('clears field error when handleChange is called for that field', () => {
    const { result } = renderHook(() => useFormValidation(testSchema, {
      name: '',
      email: 'bad',
      age: 0,
    }));

    const onSubmit = vi.fn();
    act(() => {
      result.current.handleSubmit(onSubmit)({
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent);
    });

    expect(getFieldError(result.current.errors, 'name')).toBe('Name is required');
    expect(getFieldError(result.current.errors, 'email')).toBeDefined();

    act(() => {
      result.current.handleChange('name', 'Alice');
    });

    expect(getFieldError(result.current.errors, 'name')).toBeUndefined();
    expect(getFieldError(result.current.errors, 'email')).toBeDefined();
  });

  it('handles deeply nested paths', () => {
    const nestedSchema = z.object({
      user: z.object({
        address: z.object({
          city: z.string().min(1, 'City is required'),
        }),
      }),
    });
    const { result } = renderHook(() => useFormValidation(nestedSchema, {
      user: { address: { city: '' } },
    }));

    const onSubmit = vi.fn();
    act(() => {
      result.current.handleSubmit(onSubmit)({
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent);
    });

    expect(onSubmit).not.toHaveBeenCalled();
    expect(getFieldError(result.current.errors, 'user.address.city')).toBe('City is required');
  });
});
