import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
  glow?: boolean;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hoverEffect = false,
  glow = false,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-xl transition-all duration-200 ${
        hoverEffect ? 'hover:border-indigo-500/40 hover:bg-slate-900/90 hover:shadow-xl hover:shadow-indigo-500/5 hover:-translate-y-0.5' : ''
      } ${
        glow ? 'border-indigo-500/30 shadow-lg shadow-indigo-500/10' : ''
      } ${onClick ? 'cursor-pointer' : ''} ${className}`}
    >
      {children}
    </div>
  );
};

interface SectionHeaderProps {
  icon: React.ElementType;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  iconColor?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  icon: Icon,
  title,
  subtitle,
  action,
  iconColor = 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
}) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
      <div className="flex items-center space-x-3">
        <div className={`p-2.5 rounded-xl border flex items-center justify-center shrink-0 ${iconColor}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-base sm:text-lg font-bold text-slate-100 tracking-tight">{title}</h2>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="flex items-center space-x-2">{action}</div>}
    </div>
  );
};
