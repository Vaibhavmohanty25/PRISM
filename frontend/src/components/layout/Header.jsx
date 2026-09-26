export default function Header() {
    return (
      <header className="h-16 border-b border-slate-200 bg-white px-8 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Project Intelligence Dashboard
          </h2>
  
          <p className="text-xs text-slate-500">
            Monitor progress, risks, forecasts, and project evidence
          </p>
        </div>
  
        <div className="text-sm text-slate-500">
          PRISM
        </div>
      </header>
    );
  }