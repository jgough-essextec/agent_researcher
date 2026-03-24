import { WebSource } from '@/types';
import MarkdownText from './MarkdownText';

export default function GapList({
  title,
  items,
  color,
  sources = [],
}: {
  title: string;
  items: string[];
  color: 'red' | 'orange' | 'purple';
  sources?: WebSource[];
}) {
  const colorClasses = {
    red: 'bg-red-50 border-red-200',
    orange: 'bg-orange-50 border-orange-200',
    purple: 'bg-purple-50 border-purple-200',
  };

  return (
    <div>
      <h5 className="text-sm font-medium text-gray-700 mb-2">{title}</h5>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className={`p-2 text-sm rounded border ${colorClasses[color]}`}>
            <MarkdownText content={item} sources={sources} />
          </li>
        ))}
      </ul>
    </div>
  );
}
