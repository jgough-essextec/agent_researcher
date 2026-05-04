'use client';
import React, { useState, useEffect } from 'react';
import type { OsintCommandsResponse, TerminalSubmission } from '../../../types/osint';
import { getOsintCommands, submitTerminalOutput } from '../../../lib/api';

interface Phase2DnsPanelProps {
  jobId: string;
  onSubmitted: () => void;
}

export function Phase2DnsPanel({ jobId, onSubmitted }: Phase2DnsPanelProps) {
  const [commands, setCommands] = useState<OsintCommandsResponse | null>(null);
  const [pastedOutput, setPastedOutput] = useState('');
  const [copied, setCopied] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getOsintCommands(jobId)
      .then(setCommands)
      .catch(() => setError('Failed to load commands'));
  }, [jobId]);

  const handleCopyAll = async () => {
    if (!commands?.rounds[0]?.commands) return;
    await navigator.clipboard.writeText(commands.rounds[0].commands.join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSubmit = async () => {
    if (!pastedOutput.trim()) return;
    setSubmitting(true);
    try {
      const submission: TerminalSubmission = {
        command_type: 'dig',
        command_text: 'Mixed commands',
        output_text: pastedOutput,
      };
      await submitTerminalOutput(jobId, [submission]);
      onSubmitted();
    } catch {
      setError('Failed to submit. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const lineCount = pastedOutput ? pastedOutput.split('\n').filter(Boolean).length : 0;

  if (!commands) {
    return <div className="text-gray-500 text-sm">Loading commands...</div>;
  }

  const round = commands.rounds[0];

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-800">Phase 2: DNS &amp; Infrastructure</h2>
      {round && (
        <>
          <p className="text-gray-600 text-sm">{round.rationale}</p>
          <div className="bg-gray-900 rounded-lg p-4 space-y-1">
            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-400 text-xs font-medium uppercase tracking-wide">
                Terminal Commands — Round {round.round_number}
              </span>
              <button
                onClick={handleCopyAll}
                className="text-xs bg-gray-700 hover:bg-gray-600 text-gray-200 px-3 py-1 rounded transition-colors"
              >
                {copied ? 'Copied!' : 'Copy All'}
              </button>
            </div>
            {round.commands.map((cmd, i) => (
              <div key={i} className="font-mono text-sm">
                <span className="text-gray-500">$ </span>
                <span className="text-green-300">{cmd}</span>
              </div>
            ))}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Paste terminal output here:
            </label>
            <textarea
              value={pastedOutput}
              onChange={(e) => setPastedOutput(e.target.value)}
              placeholder="Paste the complete terminal output here..."
              className="w-full font-mono text-sm min-h-[180px] max-h-[400px] p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {lineCount > 0 && (
              <p className="text-xs text-gray-500">{lineCount} lines pasted</p>
            )}
          </div>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <div className="flex gap-3">
            <button
              onClick={handleSubmit}
              disabled={!pastedOutput.trim() || submitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? 'Submitting...' : 'Submit Output'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
