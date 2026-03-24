'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { WebSource } from '@/types';
import { preprocessCitations } from '@/lib/citations';

export default function MarkdownText({
  content,
  className = '',
  sources = [],
}: {
  content: string;
  className?: string;
  sources?: WebSource[];
}) {
  const processedContent = sources.length
    ? preprocessCitations(content, sources)
    : content;

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      className={`prose prose-sm max-w-none ${className}`}
      urlTransform={(url) => url}
      components={{
        a: ({ href, children }) => {
          if (href?.startsWith('citation:')) {
            const n = parseInt(href.split(':')[1], 10);
            const source = sources[n - 1];
            return (
              <a
                href={source?.uri ?? '#'}
                target="_blank"
                rel="noopener noreferrer"
                title={source?.title ?? `Source ${n}`}
                className="no-underline"
              >
                <sup className="inline-flex items-center justify-center min-w-[1.1em] h-[1.1em] text-[0.65em] font-semibold bg-blue-100 text-blue-700 rounded-full px-1 hover:bg-blue-200 transition-colors cursor-pointer">
                  {n}
                </sup>
              </a>
            );
          }
          return (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          );
        },
      }}
    >
      {processedContent}
    </ReactMarkdown>
  );
}
