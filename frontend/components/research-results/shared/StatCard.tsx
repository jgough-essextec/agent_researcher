export default function StatCard({ label, value, className = '' }: { label: string; value: string; className?: string }) {
  return (
    <div className="p-3 bg-gray-50 rounded-lg text-center">
      <div className="text-xs text-gray-500">{label}</div>
      <div className={`font-medium text-gray-900 ${className}`}>{value}</div>
    </div>
  );
}
