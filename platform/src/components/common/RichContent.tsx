import React, { useMemo } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { ChatUnitsShowcase, ShowcaseUnit } from '../chat/ChatUnitsShowcase';
import { ChatToursShowcase, ShowcaseTour } from '../chat/ChatToursShowcase';
import { resolveUnitsByIds, STATIC_CATALOG_UNITS } from '../../services/catalogService';

interface RichContentProps {
  content: string;
  className?: string;
  onDirectSend?: (prompt: string) => void;
  isStreaming?: boolean;
}

interface ParsedBlock {
  type: 'html' | 'units' | 'tours';
  html?: string;
  units?: ShowcaseUnit[];
  tours?: ShowcaseTour[];
}

export const RichContent: React.FC<RichContentProps> = ({
  content,
  className = '',
  onDirectSend,
  isStreaming = false,
}) => {
  const blocks = useMemo<ParsedBlock[]>(() => {
    if (!content) return [];

    const result: ParsedBlock[] = [];
    // Regex matches ```units ... ``` or ```units_json ... ``` or ```tours_json ... ```
    const codeBlockRegex = /```(units|units_json|tours_json)\s*([\s\S]*?)```/g;

    let lastIndex = 0;
    let match: RegExpExecArray | null;

    const sanitizeChunk = (rawText: string): string => {
      let rawHtml = '';
      try {
        rawHtml = marked.parse(rawText, { gfm: true, breaks: true }) as string;
      } catch {
        rawHtml = rawText;
      }
      return DOMPurify.sanitize(rawHtml, {
        ADD_TAGS: [
          'table',
          'thead',
          'tbody',
          'tr',
          'th',
          'td',
          'span',
          'div',
          'p',
          'h1',
          'h2',
          'h3',
          'h4',
          'ul',
          'ol',
          'li',
          'strong',
          'em',
          'code',
          'pre',
          'br'
        ],
        ADD_ATTR: ['class', 'style', 'href', 'target', 'rel']
      });
    };

    while ((match = codeBlockRegex.exec(content)) !== null) {
      const matchIndex = match.index;
      if (matchIndex > lastIndex) {
        const textBefore = content.substring(lastIndex, matchIndex);
        if (textBefore.trim()) {
          result.push({ type: 'html', html: sanitizeChunk(textBefore) });
        }
      }

      const blockType = match[1];
      const blockBody = match[2].trim();

      try {
        if (blockType === 'units') {
          // Can be array of IDs: [101, 102] or comma separated: 101, 102
          let parsedIds: any[] = [];
          if (blockBody.startsWith('[') && blockBody.endsWith(']')) {
            parsedIds = JSON.parse(blockBody);
          } else {
            parsedIds = blockBody.split(',').map((s) => s.trim());
          }
          const units = resolveUnitsByIds(parsedIds);
          if (units.length > 0) {
            result.push({ type: 'units', units });
          } else {
            result.push({ type: 'html', html: sanitizeChunk(match[0]) });
          }
        } else if (blockType === 'units_json') {
          const parsedUnits: ShowcaseUnit[] = JSON.parse(blockBody);
          result.push({ type: 'units', units: parsedUnits });
        } else if (blockType === 'tours_json') {
          const parsedTours: ShowcaseTour[] = JSON.parse(blockBody);
          result.push({ type: 'tours', tours: parsedTours });
        }
      } catch (err) {
        // Fallback to raw code display if parsing fails
        result.push({ type: 'html', html: sanitizeChunk(match[0]) });
      }

      lastIndex = matchIndex + match[0].length;
    }

    if (lastIndex < content.length) {
      const remainingText = content.substring(lastIndex);
      if (remainingText.trim()) {
        result.push({ type: 'html', html: sanitizeChunk(remainingText) });
      }
    }

    return result;
  }, [content]);

  if (blocks.length === 0) return null;

  return (
    <div className={`space-y-3 ${className}`}>
      {blocks.map((block, idx) => {
        if (block.type === 'units' && block.units) {
          return (
            <ChatUnitsShowcase
              key={idx}
              units={block.units}
              initialLimit={3}
              onDirectSend={onDirectSend}
              isStreaming={isStreaming}
            />
          );
        }
        if (block.type === 'tours' && block.tours) {
          return <ChatToursShowcase key={idx} tours={block.tours} />;
        }
        return (
          <div
            key={idx}
            className="rich-chat-content text-xs sm:text-sm leading-relaxed text-slate-200"
            dangerouslySetInnerHTML={{ __html: block.html || '' }}
          />
        );
      })}
    </div>
  );
};
