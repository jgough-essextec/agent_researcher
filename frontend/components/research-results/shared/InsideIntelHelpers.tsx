import { GapCorrelation, WebSource } from '@/types';
import MarkdownText from './MarkdownText';

export function RatingStars({ rating }: { rating: number }) {
  const safeRating = Number.isFinite(Number(rating)) ? Number(rating) : 0;
  const fullStars = Math.floor(safeRating);
  const hasHalfStar = safeRating % 1 >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

  return (
    <div className="flex items-center">
      {[...Array(fullStars)].map((_, i) => (
        <span key={`full-${i}`} className="text-yellow-400">★</span>
      ))}
      {hasHalfStar && <span className="text-yellow-400">★</span>}
      {[...Array(emptyStars)].map((_, i) => (
        <span key={`empty-${i}`} className="text-gray-300">★</span>
      ))}
    </div>
  );
}

export function RatingCard({ label, value }: { label: string; value: number }) {
  const safeValue = Number.isFinite(value) ? value : 0;
  const getColor = (val: number) => {
    if (val >= 4) return 'text-green-600';
    if (val >= 3) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="p-3 bg-gray-50 rounded-lg text-center">
      <div className={`text-lg font-bold ${getColor(safeValue)}`}>{safeValue.toFixed(1)}</div>
      <div className="text-xs text-gray-600">{label}</div>
    </div>
  );
}

export function SentimentTrend({ trend }: { trend: 'improving' | 'declining' | 'stable' }) {
  const config = {
    improving: { icon: '↑', color: 'text-green-600', label: 'Improving' },
    declining: { icon: '↓', color: 'text-red-600', label: 'Declining' },
    stable: { icon: '→', color: 'text-gray-600', label: 'Stable' },
  };
  const { icon, color, label } = config[trend] || config.stable;

  return (
    <div>
      <div className={`text-2xl font-bold ${color}`}>{icon}</div>
      <div className="text-sm text-gray-700">Trend: {label}</div>
    </div>
  );
}

export function EmployeeTrend({ trend }: { trend: 'growing' | 'shrinking' | 'stable' }) {
  const config = {
    growing: { icon: '↑', color: 'text-green-600', label: 'Growing' },
    shrinking: { icon: '↓', color: 'text-red-600', label: 'Shrinking' },
    stable: { icon: '→', color: 'text-gray-600', label: 'Stable' },
  };
  const { icon, color, label } = config[trend] || config.stable;

  return (
    <div>
      <div className={`text-xl font-bold ${color}`}>{icon}</div>
      <div className="text-xs text-gray-700">Employee Trend: {label}</div>
    </div>
  );
}

export function SentimentBadge({
  sentiment,
  className = '',
  size = 'md',
}: {
  sentiment: 'positive' | 'negative' | 'neutral' | 'mixed' | string;
  className?: string;
  size?: 'sm' | 'md';
}) {
  const config: Record<string, { bg: string; text: string }> = {
    positive: { bg: 'bg-green-100', text: 'text-green-800' },
    negative: { bg: 'bg-red-100', text: 'text-red-800' },
    neutral: { bg: 'bg-gray-100', text: 'text-gray-800' },
    mixed: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
  };
  const { bg, text } = config[sentiment] || config.neutral;
  const sizeClass = size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2 py-1 text-xs';

  return (
    <span className={`${sizeClass} ${bg} ${text} rounded capitalize ${className}`}>
      {sentiment}
    </span>
  );
}

export function GapCorrelationCard({
  correlation,
  sources = [],
}: {
  correlation: GapCorrelation;
  sources?: WebSource[];
}) {
  const typeColors = {
    technology: 'border-l-red-400',
    capability: 'border-l-orange-400',
    process: 'border-l-purple-400',
  };
  const evidenceColors = {
    supporting: 'bg-green-50 text-green-800',
    contradicting: 'bg-red-50 text-red-800',
    neutral: 'bg-gray-50 text-gray-800',
  };

  return (
    <div className={`p-3 bg-white border border-gray-200 rounded-lg border-l-4 ${typeColors[correlation.gap_type as keyof typeof typeColors] || 'border-l-gray-400'}`}>
      <div className="flex items-start justify-between mb-2">
        <div>
          <span className="text-xs font-medium text-gray-500 uppercase">{correlation.gap_type} gap</span>
          <p className="text-sm font-medium text-gray-900 mt-0.5">{correlation.description}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 text-xs rounded ${evidenceColors[correlation.evidence_type as keyof typeof evidenceColors]}`}>
            {correlation.evidence_type}
          </span>
          <span className={`text-xs font-medium ${
            correlation.confidence >= 0.7 ? 'text-green-600' :
            correlation.confidence >= 0.4 ? 'text-yellow-600' :
            'text-gray-500'
          }`}>
            {Math.round(correlation.confidence * 100)}%
          </span>
        </div>
      </div>
      <div className="text-sm text-gray-700 mb-2">
        <span className="font-medium">Evidence:</span> <MarkdownText content={correlation.evidence} className="inline" sources={sources} />
      </div>
      {correlation.sales_implication && (
        <div className="text-sm text-blue-700 bg-blue-50 p-2 rounded">
          <span className="font-medium">Sales Implication:</span> <MarkdownText content={correlation.sales_implication} className="inline" sources={sources} />
        </div>
      )}
    </div>
  );
}
