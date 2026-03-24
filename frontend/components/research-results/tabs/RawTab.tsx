export default function RawTab({ result }: { result: string }) {
  return (
    <pre className="whitespace-pre-wrap text-sm text-gray-800 bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
      {result}
    </pre>
  );
}
