import React from 'react';

interface SiteCardProps {
  site: any;
  isSelected: boolean;
  onToggle: (siteId: string) => void;
}

const SiteCard: React.FC<SiteCardProps> = ({ site, isSelected, onToggle }) => {
  const category = site.category || 'Site';
  const opening = site.opening_hours || 'Hours unknown';

  return (
    <div
      className="group border rounded-lg p-4 cursor-pointer transition-all duration-200 hover:bg-indigo-50 border-indigo-200"
      onClick={() => onToggle(site.id)}
      role="button"
      tabIndex={0}
    >
      <div className="flex items-start gap-3">
        {/* Category indicator */}
        <div className="w-10 h-10 rounded bg-indigo-100 flex items-center justify-center flex-shrink-0">
          <span className="text-indigo-600 text-sm">
            {category.charAt(0)?.toUpperCase() || '?'}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900 line-clamp-1">
            {site.name || site.site_name}
          </h4>
          <p className="text-sm text-gray-500 line-clamp-1">
            {opening}
          </p>
        </div>
      </div>

      {/* Selection indicator */}
      <div className="absolute right-2 top-2 size-3 rounded-full flex items-center justify-center text-indigo-500 group-hover:text-indigo-600 transition-colors">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onToggle(site.id)}
          className="size-2 opacity-0 group-hover:opacity-100 cursor-pointer"
        />
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={3}
          className="select-none"
        >
          <path d="M5 13l4 4L19 7" />
        </svg>
      </div>
    </div>
  );
};

export default SiteCard;