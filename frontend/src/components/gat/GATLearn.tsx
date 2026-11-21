import React, { useEffect, useState } from 'react';
import {
  ArrowRight,
  BookOpen,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Code,
  FileText,
  Lightbulb,
  Sparkles,
} from 'lucide-react';
import type { GATLearningTopic, GATSection } from '../../types';
import { api } from '../../api';

interface GATLearnProps {
  initialSection?: GATSection;
  onStartPracticeTopic: (section: GATSection, topicName: string) => void;
}

export const GATLearn: React.FC<GATLearnProps> = ({
  initialSection = 'quantitative_ability',
  onStartPracticeTopic,
}) => {
  const [activeSection, setActiveSection] = useState<GATSection>(initialSection);
  const [topics, setTopics] = useState<GATLearningTopic[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTopicId, setExpandedTopicId] = useState<string | null>(null);

  useEffect(() => {
    setActiveSection(initialSection);
  }, [initialSection]);

  useEffect(() => {
    const fetchTopics = async () => {
      setLoading(true);
      try {
        const data = await api.listGATLearningTopics(activeSection);
        setTopics(data);
        if (data.length > 0) {
          setExpandedTopicId(data[0].id);
        }
      } catch (err) {
        console.error('Failed to load learning topics', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTopics();
  }, [activeSection]);

  const sections: { key: GATSection; label: string; desc: string }[] = [
    {
      key: 'quantitative_ability',
      label: 'Quantitative Ability',
      desc: 'Percentages, Ratios, Speed-Distance, Geometry & Work',
    },
    {
      key: 'analytical_reasoning',
      label: 'Analytical Reasoning',
      desc: 'Spatial Projections, Syllogisms, Cube Cuts & Patterns',
    },
    {
      key: 'english',
      label: 'English & Verbal',
      desc: 'Vocabulary, Sentence Sequences, Comprehension & Idioms',
    },
    {
      key: 'gk_awareness',
      label: 'GK & Awareness',
      desc: 'Indian Crafts, Design History, Architecture & Visual Identity',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Subject Selector Tabs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
        {sections.map((s) => {
          const isActive = activeSection === s.key;
          return (
            <button
              key={s.key}
              type="button"
              onClick={() => setActiveSection(s.key)}
              className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                isActive
                  ? 'bg-white border-[#1E3A5F] ring-1 ring-[#1E3A5F] shadow-xs'
                  : 'bg-[#FAF9F6] border-[#E4E1DA] hover:bg-white hover:border-[#D8D4CB]'
              }`}
            >
              <div
                className={`text-sm font-semibold ${
                  isActive ? 'text-[#1E3A5F]' : 'text-[#18181B]'
                }`}
              >
                {s.label}
              </div>
              <p className="text-[11px] text-[#78716C] mt-0.5 line-clamp-1">{s.desc}</p>
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="py-16 text-center space-y-2">
          <div className="inline-block w-6 h-6 border-2 border-[#1E3A5F] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-[#78716C]">Loading syllabus concepts...</p>
        </div>
      ) : topics.length === 0 ? (
        <div className="p-8 text-center bg-white border border-[#E4E1DA] rounded-xl text-sm text-[#78716C]">
          No modules registered for this subject yet.
        </div>
      ) : (
        <div className="space-y-4">
          {topics.map((topic) => {
            const isExpanded = expandedTopicId === topic.id;

            return (
              <div
                key={topic.id}
                className="bg-white border border-[#E4E1DA] rounded-xl overflow-hidden transition-all shadow-2xs"
              >
                {/* Topic Header Accordion Strip */}
                <div
                  onClick={() => setExpandedTopicId(isExpanded ? null : topic.id)}
                  className="px-6 py-4 flex items-center justify-between gap-4 cursor-pointer hover:bg-stone-50/50"
                >
                  <div className="flex items-center gap-3">
                    <span className="p-2 rounded-lg bg-[#FAF9F6] border border-[#E4E1DA] text-[#1E3A5F]">
                      <BookOpen className="w-4 h-4" />
                    </span>
                    <div>
                      <h4 className="font-semibold text-base text-[#18181B]">{topic.title}</h4>
                      <p className="text-xs text-[#78716C] mt-0.5">{topic.summary}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span className="font-mono-exam text-xs px-2 py-0.5 rounded bg-stone-100 text-[#57534E]">
                      {topic.total_questions} Practice Qs
                    </span>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-[#78716C]" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-[#78716C]" />
                    )}
                  </div>
                </div>

                {/* Expanded Concept Content */}
                {isExpanded && (
                  <div className="px-6 pb-6 pt-2 border-t border-[#F2EFE9] space-y-6">
                    {/* Concept Explanation */}
                    <div className="space-y-2">
                      <h5 className="text-xs font-semibold uppercase tracking-wider text-[#78716C] flex items-center gap-1.5">
                        <Lightbulb className="w-3.5 h-3.5 text-amber-600" />
                        Core Concept & Technique
                      </h5>
                      <p className="text-sm leading-relaxed text-[#27272A] bg-[#FCFBF9] p-4 rounded-xl border border-[#E4E1DA]">
                        {topic.concept_markdown}
                      </p>
                    </div>

                    {/* Key Formulas or Facts */}
                    {topic.key_formulas_or_facts.length > 0 && (
                      <div className="space-y-2">
                        <h5 className="text-xs font-semibold uppercase tracking-wider text-[#78716C] flex items-center gap-1.5">
                          <Code className="w-3.5 h-3.5 text-[#1E3A5F]" />
                          Important Formulas & Ground Truth Rules
                        </h5>
                        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {topic.key_formulas_or_facts.map((formula, fIdx) => (
                            <li
                              key={fIdx}
                              className="text-xs font-mono-exam bg-[#FAF9F6] border border-[#E4E1DA] rounded-lg p-3 text-[#18181B] flex items-start gap-2"
                            >
                              <span className="text-[#1E3A5F] font-bold">•</span>
                              <span>{formula}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Worked Examples */}
                    {topic.worked_examples.length > 0 && (
                      <div className="space-y-3">
                        <h5 className="text-xs font-semibold uppercase tracking-wider text-[#78716C] flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                          Worked Exam Problem
                        </h5>
                        {topic.worked_examples.map((ex, eIdx) => (
                          <div
                            key={eIdx}
                            className="bg-white border border-[#E4E1DA] rounded-xl p-4 space-y-2"
                          >
                            <div className="text-xs font-semibold text-[#1E3A5F] uppercase">
                              {ex.title}
                            </div>
                            <div className="text-sm font-medium text-[#18181B] bg-stone-50 p-2.5 rounded-lg border border-stone-200">
                              {ex.problem}
                            </div>
                            <div className="text-xs text-[#44403C] leading-relaxed whitespace-pre-line pl-2 border-l-2 border-[#1E3A5F]">
                              <strong>Solution:</strong> {ex.solution}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Practice Topic CTA */}
                    <div className="pt-2 flex justify-end">
                      <button
                        type="button"
                        onClick={() => onStartPracticeTopic(topic.section, topic.topic)}
                        className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-lg bg-[#1E3A5F] text-white hover:bg-[#162C49] cursor-pointer"
                      >
                        Practice {topic.topic} Questions
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
