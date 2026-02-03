'use client';

import { useState } from 'react';
import { ResearchJob, ResearchReport, CompetitorCaseStudy, GapAnalysis } from '@/types';

interface ResearchResultsProps {
  job: ResearchJob;
}

type TabId = 'overview' | 'report' | 'competitors' | 'gaps' | 'raw';

export default function ResearchResults({ job }: ResearchResultsProps) {
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  const tabs = [
    { id: 'overview' as TabId, label: 'Overview', available: true },
    { id: 'report' as TabId, label: 'Deep Research', available: !!job.report },
    { id: 'competitors' as TabId, label: 'Competitors', available: !!job.competitor_case_studies?.length },
    { id: 'gaps' as TabId, label: 'Gap Analysis', available: !!job.gap_analysis },
    { id: 'raw' as TabId, label: 'Raw Output', available: !!job.result },
  ];

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium text-gray-900">{job.client_name}</h3>
            {job.vertical && (
              <span className="text-sm text-gray-500 capitalize">{job.vertical.replace('_', ' ')}</span>
            )}
          </div>
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
            job.status === 'completed' ? 'bg-green-100 text-green-800' :
            job.status === 'failed' ? 'bg-red-100 text-red-800' :
            job.status === 'running' ? 'bg-blue-100 text-blue-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {job.status}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 bg-white">
        <nav className="flex -mb-px overflow-x-auto">
          {tabs.filter(t => t.available).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="p-4 bg-white">
        {job.status === 'running' || job.status === 'pending' ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Researching...</span>
          </div>
        ) : job.status === 'failed' ? (
          <p className="text-red-600">{job.error || 'Research failed'}</p>
        ) : (
          <>
            {activeTab === 'overview' && <OverviewTab job={job} />}
            {activeTab === 'report' && job.report && <ReportTab report={job.report} />}
            {activeTab === 'competitors' && job.competitor_case_studies && (
              <CompetitorsTab caseStudies={job.competitor_case_studies} />
            )}
            {activeTab === 'gaps' && job.gap_analysis && <GapsTab gaps={job.gap_analysis} />}
            {activeTab === 'raw' && <RawTab result={job.result} />}
          </>
        )}
      </div>
    </div>
  );
}

function OverviewTab({ job }: { job: ResearchJob }) {
  const report = job.report;

  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {report?.founded_year && (
          <StatCard label="Founded" value={String(report.founded_year)} />
        )}
        {report?.employee_count && (
          <StatCard label="Employees" value={report.employee_count} />
        )}
        {report?.annual_revenue && (
          <StatCard label="Revenue" value={report.annual_revenue} />
        )}
        {report?.digital_maturity && (
          <StatCard label="Digital Maturity" value={report.digital_maturity} className="capitalize" />
        )}
      </div>

      {/* Company Overview */}
      {report?.company_overview && (
        <Section title="Company Overview">
          <p className="text-gray-700">{report.company_overview}</p>
        </Section>
      )}

      {/* Key Decision Makers */}
      {report?.decision_makers && report.decision_makers.length > 0 && (
        <Section title="Key Decision Makers">
          <div className="grid gap-3">
            {report.decision_makers.map((dm, i) => (
              <div key={i} className="p-3 bg-gray-50 rounded-lg">
                <div className="font-medium text-gray-900">{dm.name}</div>
                <div className="text-sm text-gray-600">{dm.title}</div>
                {dm.background && (
                  <div className="text-sm text-gray-500 mt-1">{dm.background}</div>
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
                  <span className="text-red-500 mr-2">-</span>
                  <span className="text-gray-700">{point}</span>
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
                  <span className="text-green-500 mr-2">+</span>
                  <span className="text-gray-700">{opp}</span>
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
              <li key={i} className="p-3 bg-blue-50 rounded-lg text-gray-700">
                {point}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

function ReportTab({ report }: { report: ResearchReport }) {
  return (
    <div className="space-y-6">
      {/* Company Details */}
      <Section title="Company Details">
        <div className="grid md:grid-cols-2 gap-4">
          {report.headquarters && <DetailRow label="Headquarters" value={report.headquarters} />}
          {report.website && (
            <DetailRow label="Website" value={
              <a href={report.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                {report.website}
              </a>
            } />
          )}
          {report.founded_year && <DetailRow label="Founded" value={String(report.founded_year)} />}
          {report.employee_count && <DetailRow label="Employees" value={report.employee_count} />}
          {report.annual_revenue && <DetailRow label="Revenue" value={report.annual_revenue} />}
        </div>
      </Section>

      {/* AI Assessment */}
      <Section title="Digital & AI Assessment">
        <div className="grid md:grid-cols-3 gap-4 mb-4">
          {report.digital_maturity && (
            <div className="p-3 bg-gray-50 rounded-lg text-center">
              <div className="text-sm text-gray-500">Digital Maturity</div>
              <div className="font-medium capitalize">{report.digital_maturity}</div>
            </div>
          )}
          {report.ai_adoption_stage && (
            <div className="p-3 bg-gray-50 rounded-lg text-center">
              <div className="text-sm text-gray-500">AI Adoption</div>
              <div className="font-medium capitalize">{report.ai_adoption_stage}</div>
            </div>
          )}
        </div>
        {report.ai_footprint && (
          <p className="text-gray-700">{report.ai_footprint}</p>
        )}
      </Section>

      {/* Recent News */}
      {report.recent_news && report.recent_news.length > 0 && (
        <Section title="Recent News">
          <div className="space-y-3">
            {report.recent_news.map((news, i) => (
              <div key={i} className="p-3 bg-gray-50 rounded-lg">
                <div className="font-medium text-gray-900">{news.title}</div>
                <div className="text-sm text-gray-600 mt-1">{news.summary}</div>
                <div className="text-xs text-gray-500 mt-2">
                  {news.date && <span>{news.date}</span>}
                  {news.source && <span> - {news.source}</span>}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Strategic Goals */}
      {report.strategic_goals && report.strategic_goals.length > 0 && (
        <Section title="Strategic Goals">
          <ul className="space-y-2">
            {report.strategic_goals.map((goal, i) => (
              <li key={i} className="flex items-start">
                <span className="text-blue-500 mr-2">{i + 1}.</span>
                <span className="text-gray-700">{goal}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Key Initiatives */}
      {report.key_initiatives && report.key_initiatives.length > 0 && (
        <Section title="Key Initiatives">
          <ul className="space-y-2">
            {report.key_initiatives.map((init, i) => (
              <li key={i} className="p-3 bg-gray-50 rounded-lg text-gray-700">
                {init}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

function CompetitorsTab({ caseStudies }: { caseStudies: CompetitorCaseStudy[] }) {
  return (
    <div className="space-y-4">
      <p className="text-gray-600 mb-4">
        Found {caseStudies.length} relevant competitor case studies
      </p>
      {caseStudies.map((cs, i) => (
        <div key={i} className="border border-gray-200 rounded-lg p-4">
          <div className="flex justify-between items-start mb-2">
            <div>
              <h4 className="font-medium text-gray-900">{cs.competitor_name}</h4>
              <p className="text-sm text-gray-500 capitalize">{cs.vertical?.replace('_', ' ')}</p>
            </div>
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
              {Math.round(cs.relevance_score * 100)}% match
            </span>
          </div>
          <h5 className="font-medium text-gray-800 mt-3">{cs.case_study_title}</h5>
          <p className="text-gray-600 text-sm mt-1">{cs.summary}</p>

          {cs.technologies_used && cs.technologies_used.length > 0 && (
            <div className="mt-3">
              <span className="text-xs font-medium text-gray-500">Technologies:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {cs.technologies_used.map((tech, j) => (
                  <span key={j} className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          )}

          {cs.outcomes && cs.outcomes.length > 0 && (
            <div className="mt-3">
              <span className="text-xs font-medium text-gray-500">Outcomes:</span>
              <ul className="mt-1 space-y-1">
                {cs.outcomes.map((outcome, j) => (
                  <li key={j} className="text-sm text-gray-600 flex items-start">
                    <span className="text-green-500 mr-1">+</span>
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

function GapsTab({ gaps }: { gaps: GapAnalysis }) {
  return (
    <div className="space-y-6">
      {/* Confidence Score */}
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
        <span className="text-gray-600">Analysis Confidence</span>
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
        <Section title="Priority Areas">
          <div className="space-y-2">
            {gaps.priority_areas.map((area, i) => (
              <div key={i} className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-gray-700">
                <span className="font-medium">#{i + 1}</span> {area}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Gaps Grid */}
      <div className="grid md:grid-cols-3 gap-4">
        {gaps.technology_gaps && gaps.technology_gaps.length > 0 && (
          <GapList title="Technology Gaps" items={gaps.technology_gaps} color="red" />
        )}
        {gaps.capability_gaps && gaps.capability_gaps.length > 0 && (
          <GapList title="Capability Gaps" items={gaps.capability_gaps} color="orange" />
        )}
        {gaps.process_gaps && gaps.process_gaps.length > 0 && (
          <GapList title="Process Gaps" items={gaps.process_gaps} color="purple" />
        )}
      </div>

      {/* Recommendations */}
      {gaps.recommendations && gaps.recommendations.length > 0 && (
        <Section title="Recommendations">
          <ul className="space-y-2">
            {gaps.recommendations.map((rec, i) => (
              <li key={i} className="p-3 bg-green-50 rounded-lg text-gray-700">
                {rec}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Analysis Notes */}
      {gaps.analysis_notes && (
        <Section title="Analysis Notes">
          <p className="text-gray-600 text-sm">{gaps.analysis_notes}</p>
        </Section>
      )}
    </div>
  );
}

function RawTab({ result }: { result: string }) {
  return (
    <pre className="whitespace-pre-wrap text-sm text-gray-800 bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
      {result}
    </pre>
  );
}

// Helper Components
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="font-medium text-gray-900 mb-3">{title}</h4>
      {children}
    </div>
  );
}

function StatCard({ label, value, className = '' }: { label: string; value: string; className?: string }) {
  return (
    <div className="p-3 bg-gray-50 rounded-lg text-center">
      <div className="text-xs text-gray-500">{label}</div>
      <div className={`font-medium text-gray-900 ${className}`}>{value}</div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-100">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-900">{value}</span>
    </div>
  );
}

function GapList({ title, items, color }: { title: string; items: string[]; color: 'red' | 'orange' | 'purple' }) {
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
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
