import React, { useEffect, useState } from 'react';
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Compass,
  Eye,
  Filter,
  Image as ImageIcon,
  Layers,
  Sparkles,
  Tag,
  Zap,
} from 'lucide-react';
import type { GATVisualGK } from '../../types';
import { api } from '../../api';

interface GATGkBoardProps {
  onPracticeQuestion?: (questionId: string) => void;
}

export const GATGkBoard: React.FC<GATGkBoardProps> = ({ onPracticeQuestion }) => {
  const [visuals, setVisuals] = useState<GATVisualGK[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedItem, setSelectedItem] = useState<GATVisualGK | null>(null);

  const categories = [
    { key: 'all', label: 'All Visual Boards' },
    { key: 'crafts_textiles', label: 'Crafts & Textiles' },
    { key: 'architecture', label: 'Monuments & Architecture' },
    { key: 'designers', label: 'Designers & History' },
    { key: 'logos_symbols', label: 'Logos & Symbols' },
    { key: 'art_heritage', label: 'Art & Heritage' },
  ];

  useEffect(() => {
    const fetchVisuals = async () => {
      setLoading(true);
      try {
        const data = await api.listGATVisualGK(selectedCategory);
        setVisuals(data);
        if (data.length > 0 && !selectedItem) {
          setSelectedItem(data[0]);
        }
      } catch (err) {
        console.error('Failed to load visual GK boards', err);
      } finally {
        setLoading(false);
      }
    };
    fetchVisuals();
  }, [selectedCategory]);

  return (
    <div className="space-y-6">
      {/* Category Pills Header */}
      <div className="flex flex-wrap items-center gap-2 border-b border-[#E4E1DA] pb-4">
        {categories.map((c) => (
          <button
            key={c.key}
            type="button"
            onClick={() => setSelectedCategory(c.key)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
              selectedCategory === c.key
                ? 'bg-[#1E3A5F] text-white shadow-2xs'
                : 'bg-white border border-[#D8D4CB] text-[#57534E] hover:bg-stone-50'
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="py-20 text-center space-y-2">
          <div className="inline-block w-6 h-6 border-2 border-[#1E3A5F] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-[#78716C]">Loading visual awareness boards...</p>
        </div>
      ) : visuals.length === 0 ? (
        <div className="p-8 text-center bg-white border border-[#E4E1DA] rounded-xl text-sm text-[#78716C]">
          No visual boards found for this category.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {visuals.map((item) => (
            <article
              key={item.id}
              className="bg-white border border-[#E4E1DA] rounded-xl overflow-hidden hover:border-[#1E3A5F]/40 transition-all shadow-2xs flex flex-col"
            >
              <div className="h-48 overflow-hidden bg-stone-100 relative group">
                <img
                  src={item.image_url}
                  alt={item.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <span className="absolute bottom-2.5 left-2.5 px-2 py-0.5 rounded bg-black/60 backdrop-blur-xs text-white text-[11px] font-medium">
                  {item.subcategory.replace('_', ' ').toUpperCase()}
                </span>
              </div>

              <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <h4 className="font-serif-editorial text-lg font-medium text-[#18181B]">
                    {item.title}
                  </h4>
                  <p className="text-xs text-[#57534E] leading-relaxed line-clamp-2">
                    {item.description}
                  </p>

                  <div className="space-y-1.5 pt-2">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-[#78716C]">
                      High-Yield Exam Facts:
                    </span>
                    <ul className="space-y-1">
                      {item.key_facts.slice(0, 3).map((fact, fIdx) => (
                        <li
                          key={fIdx}
                          className="text-xs text-[#27272A] flex items-start gap-1.5 leading-snug"
                        >
                          <span className="text-[#1E3A5F] font-bold mt-0.5">•</span>
                          <span>{fact}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {item.related_quiz_question_id && (
                  <div className="pt-3 border-t border-[#F2EFE9] flex items-center justify-between">
                    <span className="text-[11px] text-[#78716C]">Includes exam question</span>
                    <button
                      type="button"
                      onClick={() => onPracticeQuestion?.(item.related_quiz_question_id!)}
                      className="text-xs font-semibold text-[#1E3A5F] hover:underline inline-flex items-center gap-1 cursor-pointer"
                    >
                      Solve Question &rarr;
                    </button>
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};
