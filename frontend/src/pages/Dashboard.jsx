import {
    useEffect,
    useState,
  } from "react";
  
  import {
    Activity,
    FolderKanban,
    BrainCircuit,
  } from "lucide-react";
  
  import {
    getProjects,
  } from "../api/prismApi";
  
  import MetricCard from "../components/dashboard/MetricCard";
  import ProjectCard from "../components/dashboard/ProjectCard";
  
  
  export default function Dashboard() {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
  
    useEffect(() => {
      loadProjects();
    }, []);
  
    const loadProjects = async () => {
      try {
        setLoading(true);
        setError("");
  
        const data = await getProjects();
  
        if (Array.isArray(data)) {
          setProjects(data);
        } else if (Array.isArray(data.projects)) {
          setProjects(data.projects);
        } else {
          setProjects([]);
        }
      } catch (err) {
        console.error(err);
  
        setError(
          "Could not connect to the PRISM backend."
        );
      } finally {
        setLoading(false);
      }
    };
  
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Project Intelligence
          </h1>
  
          <p className="mt-1 text-sm text-slate-500">
            Monitor construction projects and explore
            predictive insights from PRISM.
          </p>
        </div>
  
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard
            title="Projects"
            value={projects.length}
            subtitle="Projects currently loaded"
          />
  
          <MetricCard
            title="Analytics Engine"
            value="Active"
            subtitle="Deterministic project intelligence"
          />
  
          <MetricCard
            title="PRISM Agent"
            value="Online"
            subtitle="Groq-powered investigation layer"
          />
        </div>
  
        <section>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Projects
              </h2>
  
              <p className="text-sm text-slate-500">
                Projects extracted from uploaded reports.
              </p>
            </div>
  
            <button
              onClick={loadProjects}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Refresh
            </button>
          </div>
  
          {loading && (
            <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-500">
              Loading projects...
            </div>
          )}
  
          {!loading && error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">
              {error}
            </div>
          )}
  
          {!loading &&
            !error &&
            projects.length === 0 && (
              <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
                <FolderKanban
                  size={36}
                  className="mx-auto text-slate-400"
                />
  
                <h3 className="mt-4 font-semibold text-slate-900">
                  No projects yet
                </h3>
  
                <p className="mt-1 text-sm text-slate-500">
                  Upload a construction progress report
                  to start analyzing a project.
                </p>
              </div>
            )}
  
          {!loading &&
            !error &&
            projects.length > 0 && (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {projects.map((project) => {
                  const projectName =
                    typeof project === "string"
                      ? project
                      : project.project_name ??
                        project.name ??
                        "Unnamed Project";
  
                  return (
                    <ProjectCard
                      key={projectName}
                      projectName={projectName}
                    />
                  );
                })}
              </div>
            )}
        </section>
      </div>
    );
  }