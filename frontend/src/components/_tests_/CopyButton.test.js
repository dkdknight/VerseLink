import { render, screen, fireEvent } from '@testing-library/react';
import CopyButton from '../CopyButton';

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

beforeEach(() => {
  Object.assign(navigator, {
    clipboard: {
      writeText: jest.fn().mockResolvedValue(),
    },
  });
});

test('copies text to clipboard and shows feedback', async () => {
  render(<CopyButton text="org-123" />);

  const button = screen.getByRole('button', { name: /copier/i });
  fireEvent.click(button);

  expect(navigator.clipboard.writeText).toHaveBeenCalledWith('org-123');

  await screen.findByText(/copié/i);
});