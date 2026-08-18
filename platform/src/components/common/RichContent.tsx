import React, { useMemo } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

interface RichContentProps {
  content: string;
  className?: string;
}

export const RichContent: React.FC<RichContentProps> = ({ content, className = '' }) => {
  const sanitizedHtml = useMemo(() => {
    if (!content) return '';

    // If the content is already HTML or markdown, marked handles both gracefully
    let rawHtml = '';
    try {
      rawHtml = marked.parse(content, { gfm: true, breaks: true }) as string;
    } catch (e) {
      rawHtml = content;
    }

    // Sanitize with DOMPurify
    return DOMPurify.sanitize(rawHtml, {
      ADD_TAGS: ['table', 'thead', 'tbody', 'tr', 'th', 'td', 'span', 'div', 'p', 'h1', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'strong', 'em', 'code', 'pre', 'br'],
      ADD_ATTR: ['class', 'style', 'href', 'target', 'rel']
    });
  }, [content]);

  return (
    <div
      className={`rich-chat-content text-xs sm:text-sm leading-relaxed text-slate-200 ${className}`}
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
    />
  );
};
