import { WebSource } from '@/types';

export default function SourcesTab({ sources }: { sources: WebSource[] }) {
  return (
    <div className="space-y-4">
      <p className="text-gray-800 mb-4">
        Research grounded with {sources.length} web source{sources.length !== 1 ? 's' : ''}
      </p>
      <div className="space-y-3">
        {sources.map((source, i) => (
          <div key={i} id={`source-${i + 1}`} className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-xs text-blue-600 font-medium">{i + 1}</span>
              </div>
              <div className="flex-1 min-w-0">
                <h5 className="font-medium text-gray-900 truncate">
                  {source.title || 'Untitled Source'}
                </h5>
                {source.uri && (
                  <a
                    href={source.uri}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:text-blue-800 hover:underline truncate block mt-1"
                  >
                    {source.uri}
                  </a>
                )}
              </div>
              {source.uri && (
                <a
                  href={source.uri}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-shrink-0 px-3 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded-full hover:bg-blue-100 transition-colors"
                >
                  Open
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-500 mt-4">
        Sources are collected via Google Search grounding to provide real-time, verified information.
      </p>
    </div>
  );
}
