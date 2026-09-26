export default function MetricCard({
    title,
    value,
    subtitle,
  }) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm font-medium text-slate-500">
          {title}
        </p>
  
        <p className="mt-2 text-3xl font-bold text-slate-900">
          {value}
        </p>
  
        {subtitle && (
          <p className="mt-1 text-xs text-slate-400">
            {subtitle}
          </p>
        )}
      </div>
    );
  }