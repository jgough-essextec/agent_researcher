'use client';
import React, { useState, useRef } from 'react';
import { uploadOsintScreenshot, skipOsintScreenshots } from '../../../lib/api';

interface Phase3ScreenshotPanelProps {
  jobId: string;
  primaryDomain: string;
  onSubmitted: () => void;
  onSkipped: () => void;
}

type ScreenshotSource = 'dnsdumpster' | 'shodan' | 'other';

const SITE_INSTRUCTIONS = [
  {
    name: 'DNSDumpster',
    url: 'https://dnsdumpster.com',
    instruction: 'Enter: [domain] and screenshot the infrastructure map',
    source: 'dnsdumpster' as ScreenshotSource,
  },
  {
    name: 'Shodan',
    url: 'https://shodan.io',
    instruction: 'Search: ssl:[domain] and screenshot the results',
    source: 'shodan' as ScreenshotSource,
  },
];

export function Phase3ScreenshotPanel({
  jobId,
  primaryDomain,
  onSubmitted,
  onSkipped,
}: Phase3ScreenshotPanelProps) {
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState<string[]>([]);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedSource, setSelectedSource] = useState<ScreenshotSource>('dnsdumpster');

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      await uploadOsintScreenshot(jobId, file, selectedSource);
      setUploaded((prev) => [...prev, file.name]);
      onSubmitted();
    } catch {
      setError('Upload failed. Ensure the file is a valid image (PNG, JPG, or WebP).');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSkip = async () => {
    try {
      await skipOsintScreenshots(jobId);
      onSkipped();
    } catch {
      setError('Failed to skip. Please try again.');
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-800">Phase 3: Browser-Based OSINT</h2>
      <p className="text-gray-600 text-sm">
        Visit the sites below, take screenshots, and upload them for AI analysis.
      </p>

      {SITE_INSTRUCTIONS.map((site) => (
        <div key={site.name} className="border border-gray-200 rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-800">{site.name}</h3>
            <a
              href={site.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline text-sm"
            >
              Open {site.name} ↗
            </a>
          </div>
          <p className="text-sm text-gray-600">
            {site.instruction.replace('[domain]', primaryDomain)}
          </p>
        </div>
      ))}

      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center space-y-3">
        <p className="text-gray-500 text-sm">Upload screenshots here</p>
        <div className="flex items-center justify-center gap-3">
          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value as ScreenshotSource)}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="dnsdumpster">DNSDumpster</option>
            <option value="shodan">Shodan</option>
            <option value="other">Other</option>
          </select>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50 transition-colors"
          >
            {uploading ? 'Uploading...' : 'Upload Screenshot'}
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          onChange={handleFileChange}
          className="hidden"
        />
        {uploaded.length > 0 && (
          <div className="text-sm text-green-600 space-y-1">
            {uploaded.map((name) => (
              <div key={name}>✓ {name}</div>
            ))}
          </div>
        )}
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <button
        onClick={handleSkip}
        className="text-sm text-gray-500 hover:text-gray-700 underline"
      >
        Skip screenshots and continue without them
      </button>
    </div>
  );
}
