import { GapAnalysis, WebSource } from '@/types';
import MarkdownText from '../shared/MarkdownText';
import Section from '../shared/Section';
import GapList from '../shared/GapList';
import StarOrSaveButton from '../shared/StarOrSaveButton';

interface GapsTabProps {
  gaps: GapAnalysis;
  sources?: WebSource[];
  projectId?: string;
  iterationId?: string;
  clientName: string;
}

export default function GapsTab({ gaps, sources = [], projectId, iterationId, clientName }: GapsTabProps) {
  const isParsingFailure =
    gaps.analysis_notes?.startsWith('Analysis parsing failed') &&
    gaps.technology_gaps.length === 0 &&
    gaps.capability_gaps.length === 0 &&
    gaps.process_gaps.length === 0;

  if (isParsingFailure) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
        <p className="font-medium">Gap analysis could not be parsed for this research job.</p>
        <p className="text-sm mt-1">Please re-run the research to regenerate gap analysis.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Confidence Score */}
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
        <span className="text-gray-800">Analysis Confidence</span>
        <span className={`font-medium ${
          gaps.confidence_score >= 0.7 ? 'text-green-600' :
          gaps.confidence_score >= 0.4 ? 'text-yellow-600' :
          'text-red-600'
        }`}>
          {Math.round(gaps.confidence_score * 100)}%
        </span>
      </div>

      {/* Priority Areas */}
      {gaps.priority_areas && gaps.priority_areas.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-gray-700">Priority Areas</h4>
            <StarOrSaveButton
              projectId={projectId}
              iterationId={iterationId}
              clientName={clientName}
              contentType="gapanalysis"
              objectId={gaps.id}
              category="gap"
            />
          </div>
          <div className="space-y-2">
            {gaps.priority_areas.map((area, i) => (
              <div key={i} className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-gray-900">
                <span className="font-medium">#{i + 1}</span> <MarkdownText content={area} sources={sources} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Gaps Grid */}
      <div className="grid md:grid-cols-3 gap-4">
        {gaps.technology_gaps && gaps.technology_gaps.length > 0 && (
          <GapList title="Technology Gaps" items={gaps.technology_gaps} color="red" sources={sources} />
        )}
        {gaps.capability_gaps && gaps.capability_gaps.length > 0 && (
          <GapList title="Capability Gaps" items={gaps.capability_gaps} color="orange" sources={sources} />
        )}
        {gaps.process_gaps && gaps.process_gaps.length > 0 && (
          <GapList title="Process Gaps" items={gaps.process_gaps} color="purple" sources={sources} />
        )}
      </div>

      {/* Recommendations */}
      {gaps.recommendations && gaps.recommendations.length > 0 && (
        <Section title="Recommendations">
          <ul className="space-y-2">
            {gaps.recommendations.map((rec, i) => (
              <li key={i} className="p-3 bg-green-50 rounded-lg text-gray-900">
                <MarkdownText content={rec} sources={sources} />
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Analysis Notes */}
      {gaps.analysis_notes && (
        <Section title="Analysis Notes">
          <MarkdownText content={gaps.analysis_notes} className="text-gray-800 text-sm" sources={sources} />
        </Section>
      )}
    </div>
  );
}
