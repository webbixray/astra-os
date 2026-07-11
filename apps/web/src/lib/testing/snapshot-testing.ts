import { render } from '@testing-library/react';
import React from 'react';

export interface SnapshotOptions {
  serializer?: (value: unknown) => string;
  excludeKeys?: string[];
  includeKeys?: string[];
}

const defaultSerializer = (value: unknown): string => JSON.stringify(value, null, 2);

const snapshots = new Map<string, unknown>();

export function toMatchSnapshot(
  component: React.ReactElement,
  name: string,
  options?: SnapshotOptions,
): boolean {
  const { container } = render(component);
  const html = container.innerHTML;
  const serializer = options?.serializer || defaultSerializer;

  const existing = snapshots.get(name);
  const current = serializer(html);

  if (existing === undefined) {
    snapshots.set(name, current);
    console.log(`📸 Snapshot created: ${name}`);
    return true;
  }

  if (existing === current) {
    console.log(`✓ Snapshot matches: ${name}`);
    return true;
  }

  console.error(`✗ Snapshot mismatch: ${name}`);
  console.error(`Expected:\n${existing}\n\nReceived:\n${current}`);
  return false;
}

export function toMatchInlineSnapshot(
  component: React.ReactElement,
  inlineSnapshot: string,
  name?: string,
): boolean {
  const { container } = render(component);
  const html = container.innerHTML.trim();

  if (html === inlineSnapshot.trim()) {
    console.log(`✓ Inline snapshot matches${name ? `: ${name}` : ''}`);
    return true;
  }

  console.error(`✗ Inline snapshot mismatch${name ? `: ${name}` : ''}`);
  console.error(`Expected:\n${inlineSnapshot}\n\nReceived:\n${html}`);
  return false;
}

export function createSnapshot<T>(name: string, value: T): boolean {
  const serializer = defaultSerializer;
  const serialized = serializer(value);
  const existing = snapshots.get(name);

  if (existing === undefined) {
    snapshots.set(name, serialized);
    console.log(`📸 Snapshot created: ${name}`);
    return true;
  }

  if (existing === serialized) {
    console.log(`✓ Snapshot matches: ${name}`);
    return true;
  }

  console.error(`✗ Snapshot mismatch: ${name}`);
  return false;
}

export function updateSnapshot(name: string, value: unknown): void {
  snapshots.set(name, defaultSerializer(value));
  console.log(`📸 Snapshot updated: ${name}`);
}

export function clearSnapshots(): void {
  snapshots.clear();
}

export function getSnapshot(name: string): unknown {
  return snapshots.get(name);
}

export function hasSnapshot(name: string): boolean {
  return snapshots.has(name);
}

export function toMatchObject(actual: Record<string, unknown>, expected: Record<string, unknown>): boolean {
  for (const key of Object.keys(expected)) {
    if (!(key in actual)) {
      console.error(`Missing key: ${key}`);
      return false;
    }

    const actualValue = actual[key];
    const expectedValue = expected[key];

    if (typeof expectedValue === 'object' && expectedValue !== null) {
      if (!toMatchObject(actualValue as Record<string, unknown>, expectedValue as Record<string, unknown>)) {
        return false;
      }
    } else if (actualValue !== expectedValue) {
      console.error(`Value mismatch for key "${key}": expected ${expectedValue}, got ${actualValue}`);
      return false;
    }
  }

  return true;
}

export function toContain(actual: string, expected: string): boolean {
  if (!actual.includes(expected)) {
    console.error(`Expected "${actual}" to contain "${expected}"`);
    return false;
  }
  return true;
}

export function toHaveLength<T>(actual: T[], expected: number): boolean {
  if (actual.length !== expected) {
    console.error(`Expected length ${expected}, got ${actual.length}`);
    return false;
  }
  return true;
}

export function toBeDefined(actual: unknown): boolean {
  if (actual === undefined) {
    console.error('Expected value to be defined');
    return false;
  }
  return true;
}

export function toBeNull(actual: unknown): boolean {
  if (actual !== null) {
    console.error(`Expected null, got ${actual}`);
    return false;
  }
  return true;
}

export function toBeTruthy(actual: unknown): boolean {
  if (!actual) {
    console.error(`Expected truthy, got ${actual}`);
    return false;
  }
  return true;
}

export function toBeFalsy(actual: unknown): boolean {
  if (actual) {
    console.error(`Expected falsy, got ${actual}`);
    return false;
  }
  return true;
}

export function toEqual(actual: unknown, expected: unknown): boolean {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    console.error(`Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
    return false;
  }
  return true;
}

export function toBeGreaterThan(actual: number, expected: number): boolean {
  if (actual <= expected) {
    console.error(`Expected ${actual} to be greater than ${expected}`);
    return false;
  }
  return true;
}

export function toBeLessThan(actual: number, expected: number): boolean {
  if (actual >= expected) {
    console.error(`Expected ${actual} to be less than ${expected}`);
    return false;
  }
  return true;
}
