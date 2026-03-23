import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { ResearchAnimation } from '@/components/ResearchAnimation';

describe('ResearchAnimation', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders without crashing with no currentStep', () => {
    render(<ResearchAnimation clientName="Acme Corp" />);
    expect(screen.getByTestId('research-animation')).toBeTruthy();
  });

  it('displays the client name in the header', () => {
    render(<ResearchAnimation clientName="Contoso" />);
    expect(screen.getByText(/Researching Contoso/i)).toBeTruthy();
  });

  it('shows a phrase from the pending set when no step provided', () => {
    render(<ResearchAnimation clientName="Acme" />);
    const phrase = screen.getByTestId('research-phrase').textContent ?? '';
    const pendingPhrases = [
      'Warming up the research engines...',
      'Clearing the mission briefing...',
      'Assembling the intelligence team...',
    ];
    expect(pendingPhrases).toContain(phrase);
  });

  it('shows a phrase matching the research step', () => {
    render(<ResearchAnimation currentStep="research" clientName="Acme" />);
    const phrase = screen.getByTestId('research-phrase').textContent ?? '';
    const researchPhrases = [
      'Interrogating the entire internet...',
      'Making Gemini earn its keep...',
      'Vacuuming up every public byte about them...',
      'Leaving no stone unindexed...',
    ];
    expect(researchPhrases).toContain(phrase);
  });

  it('renders the SVG orbital animation element', () => {
    const { container } = render(<ResearchAnimation clientName="Acme" />);
    const svg = container.querySelector('svg');
    expect(svg).toBeTruthy();
  });

  it('renders step pills for all workflow stages', () => {
    render(<ResearchAnimation clientName="Acme" />);
    const pills = screen.getByTestId('step-pills');
    expect(pills.querySelectorAll('[data-step]').length).toBe(7);
  });

  it('highlights the current step pill in blue', () => {
    render(<ResearchAnimation currentStep="classify" clientName="Acme" />);
    const classifyPill = screen.getByTestId('step-pills').querySelector('[data-step="classify"]');
    expect(classifyPill?.className).toContain('blue');
  });

  it('marks prior steps as completed (green)', () => {
    render(<ResearchAnimation currentStep="competitors" clientName="Acme" />);
    const pills = screen.getByTestId('step-pills');
    // research and classify come before competitors
    const researchPill = pills.querySelector('[data-step="research"]');
    const classifyPill = pills.querySelector('[data-step="classify"]');
    expect(researchPill?.className).toContain('green');
    expect(classifyPill?.className).toContain('green');
  });

  it('marks upcoming steps as grey', () => {
    render(<ResearchAnimation currentStep="research" clientName="Acme" />);
    const pills = screen.getByTestId('step-pills');
    const finalizePill = pills.querySelector('[data-step="finalize"]');
    expect(finalizePill?.className).toContain('gray');
  });

  it('rotates phrase after 4 seconds', () => {
    render(<ResearchAnimation currentStep="research" clientName="Acme" />);
    const firstPhrase = screen.getByTestId('research-phrase').textContent;

    act(() => {
      vi.advanceTimersByTime(4300);
    });

    // After one cycle the phrase index has advanced — phrase may or may not differ
    // depending on how many phrases exist; just verify no crash and element still present
    expect(screen.getByTestId('research-phrase')).toBeTruthy();
    // With 4 phrases, after 4s the second phrase shows (index 1)
    const secondPhrase = screen.getByTestId('research-phrase').textContent;
    // They could be the same only if phrases.length === 1, which is not the case
    const researchPhrases = [
      'Interrogating the entire internet...',
      'Making Gemini earn its keep...',
      'Vacuuming up every public byte about them...',
      'Leaving no stone unindexed...',
    ];
    expect(researchPhrases).toContain(secondPhrase);
    // After 4s the index should have moved from 0 to 1
    expect(secondPhrase).not.toBe(firstPhrase);
  });

  it('handles unknown step values gracefully (falls back to pending)', () => {
    render(<ResearchAnimation currentStep="unknown_step" clientName="Acme" />);
    const phrase = screen.getByTestId('research-phrase').textContent ?? '';
    const pendingPhrases = [
      'Warming up the research engines...',
      'Clearing the mission briefing...',
      'Assembling the intelligence team...',
    ];
    expect(pendingPhrases).toContain(phrase);
  });

  it('shows finalize phrases when step is finalize', () => {
    render(<ResearchAnimation currentStep="finalize" clientName="Acme" />);
    const phrase = screen.getByTestId('research-phrase').textContent ?? '';
    const finalizePhrases = [
      'Polishing the intelligence package...',
      'Compiling your battle briefing...',
      'Almost ready to brief the team...',
      'Putting the bow on it...',
    ];
    expect(finalizePhrases).toContain(phrase);
  });
});
