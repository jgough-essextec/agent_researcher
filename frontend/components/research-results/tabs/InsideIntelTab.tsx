import { InternalOpsIntel, WebSource } from '@/types';
import MarkdownText from '../shared/MarkdownText';
import Section from '../shared/Section';
import {
  RatingStars,
  RatingCard,
  SentimentTrend,
  EmployeeTrend,
  SentimentBadge,
  GapCorrelationCard,
} from '../shared/InsideIntelHelpers';

export default function InsideIntelTab({ intel, sources = [] }: { intel: InternalOpsIntel; sources?: WebSource[] }) {
  return (
    <div className="space-y-6">
      {/* Section 1: Employee Sentiment Overview */}
      {intel.employee_sentiment && (
        <Section title="Employee Sentiment Overview">
          <div className="space-y-4">
            {/* Overall Rating */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <span className="text-gray-800 font-medium">Overall Rating</span>
                <RatingStars rating={intel.employee_sentiment.overall_rating} />
              </div>
              <span className="text-lg font-bold text-gray-900">
                {intel.employee_sentiment.overall_rating.toFixed(1)}/5.0
              </span>
            </div>

            {/* Category Ratings */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <RatingCard label="Work-Life Balance" value={intel.employee_sentiment.work_life_balance} />
              <RatingCard label="Compensation" value={intel.employee_sentiment.compensation} />
              <RatingCard label="Culture" value={intel.employee_sentiment.culture} />
              <RatingCard label="Management" value={intel.employee_sentiment.management} />
            </div>

            {/* Recommend & Trend */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-blue-50 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-600">{intel.employee_sentiment.recommend_pct}%</div>
                <div className="text-sm text-gray-700">Would Recommend</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg text-center">
                <SentimentTrend trend={intel.employee_sentiment.trend} />
              </div>
            </div>

            {/* Themes */}
            <div className="grid md:grid-cols-2 gap-4">
              {intel.employee_sentiment.positive_themes.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Positive Themes</h5>
                  <div className="flex flex-wrap gap-2">
                    {intel.employee_sentiment.positive_themes.map((theme, i) => (
                      <span key={i} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        {theme}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {intel.employee_sentiment.negative_themes.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Negative Themes</h5>
                  <div className="flex flex-wrap gap-2">
                    {intel.employee_sentiment.negative_themes.map((theme, i) => (
                      <span key={i} className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                        {theme}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </Section>
      )}

      {/* Section 2: Talent & Hiring Intelligence */}
      {intel.job_postings && (
        <Section title="Talent & Hiring Intelligence">
          <div className="space-y-4">
            {/* Total Openings */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-800 font-medium">Total Open Positions</span>
              <span className="text-2xl font-bold text-gray-900">{intel.job_postings.total_openings}</span>
            </div>

            {/* Departments Hiring */}
            {Object.keys(intel.job_postings.departments_hiring).length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Departments Hiring</h5>
                <div className="space-y-2">
                  {Object.entries(intel.job_postings.departments_hiring)
                    .sort(([, a], [, b]) => b - a)
                    .map(([dept, count]) => (
                      <div key={dept} className="flex items-center justify-between">
                        <span className="text-gray-800">{dept}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500 rounded-full"
                              style={{
                                width: `${(count / Math.max(...Object.values(intel.job_postings.departments_hiring))) * 100}%`
                              }}
                            />
                          </div>
                          <span className="text-gray-900 font-medium w-8 text-right">{count}</span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Skills Sought */}
            {intel.job_postings.skills_sought.length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Key Skills Sought</h5>
                <div className="flex flex-wrap gap-2">
                  {intel.job_postings.skills_sought.map((skill, i) => (
                    <span key={i} className="px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Seniority Distribution */}
            {Object.keys(intel.job_postings.seniority_distribution).length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Seniority Distribution</h5>
                <div className="flex gap-3">
                  {Object.entries(intel.job_postings.seniority_distribution).map(([level, count]) => (
                    <div key={level} className="text-center p-2 bg-gray-50 rounded-lg flex-1">
                      <div className="font-bold text-gray-900">{count}</div>
                      <div className="text-xs text-gray-600">{level}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Urgency Signals */}
            {intel.job_postings.urgency_signals.length > 0 && (
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <h5 className="text-sm font-medium text-orange-800 mb-2">Urgency Signals</h5>
                <ul className="space-y-1">
                  {intel.job_postings.urgency_signals.map((signal, i) => (
                    <li key={i} className="text-sm text-orange-900 flex items-start">
                      <span className="mr-2">-</span>
                      {signal}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Hiring Insights */}
            {intel.job_postings.insights && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <MarkdownText content={intel.job_postings.insights} className="text-gray-900 text-sm" sources={sources} />
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Section 3: Digital & Social Presence */}
      {intel.linkedin_presence && (
        <Section title="Digital & Social Presence">
          <div className="space-y-4">
            {/* LinkedIn Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-blue-50 rounded-lg text-center">
                <div className="text-xl font-bold text-blue-600">
                  {intel.linkedin_presence.follower_count.toLocaleString()}
                </div>
                <div className="text-xs text-gray-700">LinkedIn Followers</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg text-center">
                <div className="text-lg font-medium text-gray-900 capitalize">
                  {intel.linkedin_presence.engagement_level}
                </div>
                <div className="text-xs text-gray-700">Engagement Level</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg text-center">
                <EmployeeTrend trend={intel.linkedin_presence.employee_trend} />
              </div>
            </div>

            {/* Recent Posts */}
            {intel.linkedin_presence.recent_posts.length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Recent Company Posts</h5>
                <div className="space-y-2">
                  {intel.linkedin_presence.recent_posts.slice(0, 3).map((post, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-lg">
                      <div className="font-medium text-gray-900 text-sm">{post.title}</div>
                      <div className="text-xs text-gray-700 mt-1">{post.summary}</div>
                      {post.date && <div className="text-xs text-gray-500 mt-1">{post.date}</div>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Notable Changes */}
            {intel.linkedin_presence.notable_changes.length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Notable Changes</h5>
                <ul className="space-y-1">
                  {intel.linkedin_presence.notable_changes.map((change, i) => (
                    <li key={i} className="text-sm text-gray-900 flex items-start">
                      <span className="text-blue-600 mr-2">-</span>
                      {change}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Section 4: Public Sentiment Analysis */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Social Media Mentions */}
        {intel.social_media_mentions && intel.social_media_mentions.length > 0 && (
          <Section title="Social Media Mentions">
            <div className="space-y-3">
              {intel.social_media_mentions.map((mention, i) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900 capitalize">{mention.platform}</span>
                    <SentimentBadge sentiment={mention.sentiment} />
                  </div>
                  <p className="text-sm text-gray-800">{mention.summary}</p>
                  {mention.topic && (
                    <span className="inline-block mt-2 px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded">
                      {mention.topic}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* News Sentiment */}
        {intel.news_sentiment && (
          <Section title="News Coverage">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <span className="text-gray-700 text-sm">Overall Sentiment</span>
                  <SentimentBadge sentiment={intel.news_sentiment.overall_sentiment} className="ml-2" />
                </div>
                <div className="text-right">
                  <span className="text-xs text-gray-500">Coverage: </span>
                  <span className="text-sm font-medium text-gray-900 capitalize">
                    {intel.news_sentiment.coverage_volume}
                  </span>
                </div>
              </div>

              {intel.news_sentiment.topics.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Key Topics</h5>
                  <div className="flex flex-wrap gap-2">
                    {intel.news_sentiment.topics.map((topic, i) => (
                      <span key={i} className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {intel.news_sentiment.headlines.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Recent Headlines</h5>
                  <div className="space-y-2">
                    {intel.news_sentiment.headlines.slice(0, 5).map((headline, i) => (
                      <div key={i} className="p-2 bg-gray-50 rounded flex items-start justify-between gap-2">
                        <div>
                          <div className="text-sm text-gray-900">{headline.title}</div>
                          <div className="text-xs text-gray-500">
                            {headline.source} {headline.date && `- ${headline.date}`}
                          </div>
                        </div>
                        <SentimentBadge sentiment={headline.sentiment} size="sm" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Section>
        )}
      </div>

      {/* Section 5: Gap Correlation Insights */}
      {intel.gap_correlations && intel.gap_correlations.length > 0 && (
        <Section title="Gap Correlation Insights">
          <p className="text-sm text-gray-700 mb-4">
            Cross-referencing identified gaps with internal operations evidence
          </p>
          <div className="space-y-3">
            {intel.gap_correlations.map((corr, i) => (
              <GapCorrelationCard key={i} correlation={corr} sources={sources} />
            ))}
          </div>
        </Section>
      )}

      {/* Section 6: Key Insights & Recommendations */}
      {intel.key_insights && intel.key_insights.length > 0 && (
        <Section title="Key Insights & Recommendations">
          <div className="space-y-2">
            {intel.key_insights.map((insight, i) => (
              <div key={i} className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <MarkdownText content={insight} className="text-gray-900" sources={sources} />
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Metadata Footer */}
      <div className="p-3 bg-gray-50 rounded-lg flex items-center justify-between text-sm">
        <div className="flex items-center gap-4">
          <span className="text-gray-600">
            Confidence: <span className={`font-medium ${
              intel.confidence_score >= 0.7 ? 'text-green-600' :
              intel.confidence_score >= 0.4 ? 'text-yellow-600' :
              'text-red-600'
            }`}>{Math.round(intel.confidence_score * 100)}%</span>
          </span>
          {intel.data_freshness && (
            <span className="text-gray-600">
              Data: <span className="text-gray-900">{intel.data_freshness.replace('_', ' ')}</span>
            </span>
          )}
        </div>
      </div>

      {/* Analysis Notes */}
      {intel.analysis_notes && (
        <MarkdownText content={intel.analysis_notes} className="text-xs text-gray-500 italic" sources={sources} />
      )}
    </div>
  );
}
