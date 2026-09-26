import { useNavigate } from "react-router-dom";
import { FolderKanban, ArrowRight } from "lucide-react";

export default function ProjectCard({
  projectName,
}) {
  const navigate = useNavigate();

  const openProject = () => {
    navigate(
      `/projects/${encodeURIComponent(projectName)}`
    );
  };

  return (
    <button
      onClick={openProject}
      className="w-full rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-slate-100 p-2">
            <FolderKanban
              size={20}
              className="text-slate-700"
            />
          </div>

          <div>
            <h3 className="font-semibold text-slate-900">
              {projectName}
            </h3>

            <p className="mt-1 text-xs text-slate-500">
              View project intelligence
            </p>
          </div>
        </div>

        <ArrowRight
          size={18}
          className="text-slate-400"
        />
      </div>
    </button>
  );
}