import ResearchForm from '@/components/ResearchForm';

export default function Home() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900">New Research</h2>
        <p className="text-sm text-gray-500 mt-1">
          Enter a client name and any sales history to generate comprehensive prospect research.
        </p>
      </div>
      <ResearchForm />
    </div>
  );
}
