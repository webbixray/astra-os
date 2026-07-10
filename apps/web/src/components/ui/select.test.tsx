import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Select } from './select';

const options = [
  { value: 'option1', label: 'Option 1' },
  { value: 'option2', label: 'Option 2' },
  { value: 'option3', label: 'Option 3' },
];

describe('Select', () => {
  it('renders all options', () => {
    render(<Select options={options} />);
    expect(screen.getByText('Option 1')).toBeInTheDocument();
    expect(screen.getByText('Option 2')).toBeInTheDocument();
    expect(screen.getByText('Option 3')).toBeInTheDocument();
  });

  it('renders placeholder when provided', () => {
    render(<Select options={options} placeholder="Choose an option" />);
    expect(screen.getByText('Choose an option')).toBeInTheDocument();
  });

  it('allows selecting an option', async () => {
    const user = userEvent.setup();
    render(<Select options={options} />);
    const select = screen.getByRole('combobox');
    await user.selectOptions(select, 'option2');
    expect(select).toHaveValue('option2');
  });

  it('can be disabled', () => {
    render(<Select options={options} disabled />);
    expect(screen.getByRole('combobox')).toBeDisabled();
  });
});
