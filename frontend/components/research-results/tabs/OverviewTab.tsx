import { ResearchJob, WebSource } from '@/types';
import MarkdownText from '../shared/MarkdownText';
import Section from '../shared/Section';
import StatCard from '../shared/StatCard';

export default function OverviewTab({ job, sources = [] }: { job: ResearchJob; sources?: WebSource[] }) {
  const report = job.report;

  if (!report) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800">
        <p className="font-medium">Structured data not available for this research job.</p>
        <p className="text-sm mt-1">The raw research output is available in the <strong>Raw Output</strong> tab.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {report.founded_year && (
          <StatCard label="Founded" value={String(report.founded_year)} />
        )}
        {report.employee_count && (
          <StatCard label="Employees" value={report.employee_count} />
        )}
        {report.annual_revenue && (
          <StatCard label="Revenue" value={report.annual_revenue} />
        )}
        {report.digital_maturity && (
          <StatCard label="Digital Maturity" value={report.digital_maturity} className="capitalize" />
        )}
      </div>

      {/* Data Maturity — prose section, not a stat card */}
      {report.data_maturity && (
        <Section title="Data Maturity">
          <MarkdownText content={report.data_maturity} className="text-gray-900" sources={sources} />
        </Section>
      )}

      {/* Company Overview */}
      {report?.company_overview && (
        <Section title="Company Overview">
          <p className="text-gray-900">{report.company_overview}</p>
        </Section>
      )}

      {/* Key Decision Makers */}
      {report?.decision_makers && report.decision_makers.length > 0 && (
        <Section title="Key Decision Makers">
          <div className="grid gap-3">
            {report.decision_makers.map((dm, i) => (
              <div key={i} className="p-3 bg-gray-50 rounded-lg">
                <div className="font-medium text-gray-900">{dm.name}</div>
                <div className="text-sm text-gray-800">{dm.title}</div>
                {dm.background && (
                  <div className="text-sm text-gray-700 mt-1">{dm.background}</div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Pain Points & Opportunities */}
      <div className="grid md:grid-cols-2 gap-6">
        {report?.pain_points && report.pain_points.length > 0 && (
          <Section title="Pain Points">
            <ul className="space-y-2">
              {report.pain_points.map((point, i) => (
                <li key={i} className="flex items-start">
                  <span className="text-red-600 mr-2">-</span>
                  <span className="text-gray-900">{point}</span>
                </li>
              ))}
            </ul>
          </Section>
        )}
        {report?.opportunities && report.opportunities.length > 0 && (
          <Section title="Opportunities">
            <ul className="space-y-2">
              {report.opportunities.map((opp, i) => (
                <li key={i} className="flex items-start">
                  <span className="text-green-600 mr-2">+</span>
                  <span className="text-gray-900">{opp}</span>
                </li>
              ))}
            </ul>
          </Section>
        )}
      </div>

      {/* Talking Points */}
      {report?.talking_points && report.talking_points.length > 0 && (
        <Section title="Recommended Talking Points">
          <ul className="space-y-2">
            {report.talking_points.map((point, i) => (
              <li key={i} className="p-3 bg-blue-50 rounded-lg text-gray-900">
                {point}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}
