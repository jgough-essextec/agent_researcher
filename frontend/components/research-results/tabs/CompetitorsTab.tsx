import { CompetitorCaseStudy } from '@/types';
import StarOrSaveButton from '../shared/StarOrSaveButton';

interface CompetitorsTabProps {
  caseStudies: CompetitorCaseStudy[];
  projectId?: string;
  iterationId?: string;
  clientName: string;
}

export default function CompetitorsTab({ caseStudies, projectId, iterationId, clientName }: CompetitorsTabProps) {
  return (
    <div className="space-y-4">
      <p className="text-gray-800 mb-4">
        Found {caseStudies.length} relevant competitor case studies
      </p>
      {caseStudies.map((cs, i) => (
        <div key={i} className="border border-gray-200 rounded-lg p-4">
          <div className="flex justify-between items-start mb-2">
            <div>
              <h4 className="font-medium text-gray-900">{cs.competitor_name}</h4>
              <p className="text-sm text-gray-700 capitalize">{cs.vertical?.replace('_', ' ')}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                {Math.round(cs.relevance_score * 100)}% match
              </span>
              <StarOrSaveButton
                projectId={projectId}
                iterationId={iterationId}
                clientName={clientName}
                contentType="competitorcasestudy"
                objectId={cs.id}
                category="case_study"
              />
            </div>
          </div>
          <h5 className="font-medium text-gray-800 mt-3">{cs.case_study_title}</h5>
          <p className="text-gray-900 text-sm mt-1">{cs.summary}</p>

          {cs.technologies_used && cs.technologies_used.length > 0 && (
            <div className="mt-3">
              <span className="text-xs font-medium text-gray-700">Technologies:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {cs.technologies_used.map((tech, j) => (
                  <span key={j} className="px-2 py-0.5 bg-gray-100 text-gray-800 text-xs rounded">
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          )}

          {cs.outcomes && cs.outcomes.length > 0 && (
            <div className="mt-3">
              <span className="text-xs font-medium text-gray-700">Outcomes:</span>
              <ul className="mt-1 space-y-1">
                {cs.outcomes.map((outcome, j) => (
                  <li key={j} className="text-sm text-gray-900 flex items-start">
                    <span className="text-green-600 mr-1">+</span>
                    {outcome}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
