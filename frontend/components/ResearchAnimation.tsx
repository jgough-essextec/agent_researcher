'use client';

import { useEffect, useRef, useState } from 'react';

interface ResearchAnimationProps {
  currentStep?: string;
  clientName: string;
}

type StepKey =
  | 'pending'
  | 'research'
  | 'classify'
  | 'competitors'
  | 'gap_analysis'
  | 'internal_ops'
  | 'correlate'
  | 'finalize';

const STEP_PHRASES: Record<StepKey, string[]> = {
  pending: [
    'Warming up the research engines...',
    'Clearing the mission briefing...',
    'Assembling the intelligence team...',
  ],
  research: [
    'Interrogating the entire internet...',
    'Making Gemini earn its keep...',
    'Vacuuming up every public byte about them...',
    'Leaving no stone unindexed...',
  ],
  classify: [
    'Sorting them into the right filing cabinet...',
    "Assigning the industry label (don't worry, it won't hurt)...",
    'Pigeon-holing them — in the most useful way possible...',
  ],
  internal_ops: [
    'Reading Glassdoor between the lines...',
    'Decoding their LinkedIn signals...',
    'Finding the noise beneath the PR...',
    "Triangulating what their employees actually think...",
  ],
  competitors: [
    'Spying on the competition (legally, of course)...',
    'Collecting competitive dirt...',
    'Mapping who\'s bragging about what...',
    'Checking what the rivals have been up to...',
  ],
  gap_analysis: [
    'Finding the cracks in their armor...',
    "Spotting where they're flying blind...",
    'Locating the missing puzzle pieces...',
    'Identifying the white space...',
  ],
  correlate: [
    'Cross-referencing all the signals...',
    'Weaving the intelligence threads together...',
    'Building your unfair advantage map...',
    'Connecting the dots...',
  ],
  finalize: [
    'Polishing the intelligence package...',
    'Compiling your battle briefing...',
    'Almost ready to brief the team...',
    'Putting the bow on it...',
  ],
};

const STEP_ORDER: StepKey[] = [
  'research',
  'classify',
  'internal_ops',
  'competitors',
  'gap_analysis',
  'correlate',
  'finalize',
];

const STEP_LABELS: Record<StepKey, string> = {
  pending: 'Starting',
  research: 'Researching',
  classify: 'Classifying',
  internal_ops: 'Operations',
  competitors: 'Competitors',
  gap_analysis: 'Gap Analysis',
  correlate: 'Correlating',
  finalize: 'Finalizing',
};

function resolveStep(step?: string): StepKey {
  if (!step || step === '') return 'pending';
  if (STEP_PHRASES[step as StepKey]) return step as StepKey;
  return 'pending';
}

function getStepIndex(step: StepKey): number {
  return STEP_ORDER.indexOf(step);
}

// SVG orbital animation — central "brain" with orbiting data nodes
function AgentOrbitSVG() {
  return (
    <svg
      width="200"
      height="200"
      viewBox="0 0 200 200"
      className="overflow-visible"
      aria-hidden="true"
    >
      <defs>
        {/* Glow filter for the core */}
        <filter id="coreGlow">
          <feGaussianBlur stdDeviation="4" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        {/* Subtle glow for nodes */}
        <filter id="nodeGlow">
          <feGaussianBlur stdDeviation="2" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Outer orbit ring */}
      <circle
        cx="100"
        cy="100"
        r="72"
        fill="none"
        stroke="#dbeafe"
        strokeWidth="1"
        strokeDasharray="4 6"
        className="animate-[spin_20s_linear_infinite]"
        style={{ transformOrigin: '100px 100px' }}
      />

      {/* Inner orbit ring */}
      <circle
        cx="100"
        cy="100"
        r="48"
        fill="none"
        stroke="#e0e7ff"
        strokeWidth="1"
        strokeDasharray="3 8"
        className="animate-[spin_14s_linear_infinite_reverse]"
        style={{ transformOrigin: '100px 100px' }}
      />

      {/* Orbiting nodes on outer ring — 6 nodes at 60° intervals */}
      {[0, 60, 120, 180, 240, 300].map((deg, i) => (
        <g
          key={i}
          className={`animate-[spin_${[20, 20, 20, 20, 20, 20][i]}s_linear_infinite]`}
          style={{ transformOrigin: '100px 100px', animationDelay: `${-i * 3.33}s` }}
        >
          <circle
            cx={100 + 72 * Math.cos((deg * Math.PI) / 180)}
            cy={100 + 72 * Math.sin((deg * Math.PI) / 180)}
            r={i % 2 === 0 ? 5 : 3.5}
            fill={i % 3 === 0 ? '#3b82f6' : i % 3 === 1 ? '#6366f1' : '#8b5cf6'}
            filter="url(#nodeGlow)"
            opacity="0.85"
          />
        </g>
      ))}

      {/* Orbiting nodes on inner ring — 4 nodes */}
      {[45, 135, 225, 315].map((deg, i) => (
        <g
          key={`inner-${i}`}
          className="animate-[spin_14s_linear_infinite_reverse]"
          style={{ transformOrigin: '100px 100px', animationDelay: `${-i * 3.5}s` }}
        >
          <circle
            cx={100 + 48 * Math.cos((deg * Math.PI) / 180)}
            cy={100 + 48 * Math.sin((deg * Math.PI) / 180)}
            r={4}
            fill={i % 2 === 0 ? '#06b6d4' : '#0ea5e9'}
            filter="url(#nodeGlow)"
            opacity="0.75"
          />
        </g>
      ))}

      {/* Connection lines — static, between core and a few outer nodes */}
      {[30, 150, 270].map((deg, i) => (
        <line
          key={`line-${i}`}
          x1="100"
          y1="100"
          x2={100 + 72 * Math.cos((deg * Math.PI) / 180)}
          y2={100 + 72 * Math.sin((deg * Math.PI) / 180)}
          stroke="#bfdbfe"
          strokeWidth="1"
          strokeDasharray="3 4"
          opacity="0.5"
        />
      ))}

      {/* Core pulsing circle */}
      <circle
        cx="100"
        cy="100"
        r="22"
        fill="#eff6ff"
        stroke="#3b82f6"
        strokeWidth="2"
        filter="url(#coreGlow)"
        className="animate-[pulse_2s_ease-in-out_infinite]"
      />

      {/* Core inner circle */}
      <circle cx="100" cy="100" r="14" fill="#3b82f6" opacity="0.9" />

      {/* Magnifying glass icon in center */}
      <circle
        cx="98"
        cy="98"
        r="6"
        fill="none"
        stroke="white"
        strokeWidth="2"
      />
      <line
        x1="103"
        y1="103"
        x2="108"
        y2="108"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function ResearchAnimation({ currentStep, clientName }: ResearchAnimationProps) {
  const step = resolveStep(currentStep);
  const phrases = STEP_PHRASES[step];
  const stepIndex = getStepIndex(step);

  const [phraseIndex, setPhraseIndex] = useState(0);
  const [visible, setVisible] = useState(true);
  const prevStepRef = useRef(step);

  // Reset phrase when step changes
  useEffect(() => {
    if (prevStepRef.current !== step) {
      prevStepRef.current = step;
      setVisible(false);
      const reset = setTimeout(() => {
        setPhraseIndex(0);
        setVisible(true);
      }, 300);
      return () => clearTimeout(reset);
    }
  }, [step]);

  // Rotate phrases every 4 seconds with fade
  useEffect(() => {
    const interval = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setPhraseIndex((i) => (i + 1) % phrases.length);
        setVisible(true);
      }, 300);
    }, 4000);
    return () => clearInterval(interval);
  }, [phrases.length]);

  return (
    <div
      className="flex flex-col items-center justify-center py-12 px-6 gap-6"
      data-testid="research-animation"
    >
      {/* Header */}
      <p className="text-sm font-medium text-blue-500 tracking-widest uppercase">
        Researching {clientName}
      </p>

      {/* SVG orbital animation */}
      <div className="relative">
        <AgentOrbitSVG />
      </div>

      {/* Rotating phrase */}
      <p
        className="text-base text-gray-600 text-center max-w-xs transition-opacity duration-300 min-h-[1.5rem]"
        style={{ opacity: visible ? 1 : 0 }}
        data-testid="research-phrase"
      >
        {phrases[phraseIndex]}
      </p>

      {/* Stage journey pills */}
      <div className="flex flex-wrap justify-center gap-2 mt-2" data-testid="step-pills">
        {STEP_ORDER.map((s, i) => {
          const isCurrent = s === step;
          const isCompleted = stepIndex >= 0 && i < stepIndex;
          return (
            <span
              key={s}
              data-step={s}
              className={[
                'px-2.5 py-0.5 rounded-full text-xs font-medium transition-all duration-500',
                isCurrent
                  ? 'bg-blue-100 text-blue-700 ring-1 ring-blue-400 animate-[pulse_2s_ease-in-out_infinite]'
                  : isCompleted
                  ? 'bg-green-50 text-green-600'
                  : 'bg-gray-100 text-gray-400',
              ].join(' ')}
            >
              {STEP_LABELS[s]}
            </span>
          );
        })}
      </div>
    </div>
  );
}
