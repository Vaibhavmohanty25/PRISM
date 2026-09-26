import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Loader2,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

import {
  getProjectPredictiveSummary,
} from "../api/prismApi";


export default function ProjectDetails() {
  const { projectName } = useParams();

  const decodedProjectName =
    decodeURIComponent(projectName || "");

  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  useEffect(() => {
    loadProject();
  }, [projectName]);


  const loadProject = async () => {
    try {
      setLoading(true);
      setError("");

      const data =
        await getProjectPredictiveSummary(
          decodedProjectName
        );

      setSummary(data);

    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.error?.message ||
          "Could not load project intelligence."
      );

    } finally {
      setLoading(false);
    }
  };


  if (loading) {
    return (
      <div className="flex items-center gap-3 text-slate-500">
        <Loader2
          size={20}
          className="animate-spin"
        />
        Loading project intelligence...
      </div>
    );
  }


  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-red-700">
        {error}
      </div>
    );
  }


  if (!summary) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        No project data available.
      </div>
    );
  }


  return (
    <div className="space-y-8">

      <div>
        <p className="text-sm font-medium text-slate-500">
          Project Intelligence
        </p>

        <h1 className="mt-1 text-3xl font-bold text-slate-900">
          {summary.project_name}
        </h1>

        <p className="mt-2 text-sm text-slate-500">
          Predictive overview generated from uploaded
          project reports.
        </p>
      </div>


      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

        <MetricCard
          title="Total Activities"
          value={summary.total_activity_count}
          icon={Activity}
        />

        <MetricCard
          title="Active Activities"
          value={summary.active_activity_count}
          icon={TrendingUp}
        />

        <MetricCard
          title="Completed"
          value={summary.completed_activity_count}
          icon={CheckCircle2}
        />

        <MetricCard
          title="Requiring Attention"
          value={
            summary.activities_requiring_attention?.length ?? 0
          }
          icon={AlertTriangle}
        />

      </section>


      <section className="grid gap-6 lg:grid-cols-2">

        <DistributionCard
          title="Forecast Status"
          icon={BarChart3}
          data={
            summary.forecast_status_distribution
          }
        />

        <DistributionCard
          title="Confidence Levels"
          icon={ShieldCheck}
          data={
            summary.confidence_level_distribution
          }
        />

        <DistributionCard
          title="Predictive Risk"
          icon={AlertTriangle}
          data={
            summary.predictive_risk_distribution
          }
        />

        <DistributionCard
          title="Decision Support Priority"
          icon={TrendingUp}
          data={
            summary.decision_support_priority_distribution
          }
        />

      </section>


      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

        <div className="mb-5">
          <h2 className="text-lg font-semibold text-slate-900">
            Activities Requiring Attention
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Activities where PRISM recommends review
            or further evidence.
          </p>
        </div>


        {summary.activities_requiring_attention?.length >
        0 ? (
          <div className="space-y-4">

            {summary.activities_requiring_attention.map(
              (activity) => (
                <AttentionCard
                  key={activity.activity_name}
                  activity={activity}
                />
              )
            )}

          </div>
        ) : (
          <div className="rounded-xl bg-slate-50 p-5 text-sm text-slate-500">
            No activities currently require attention.
          </div>
        )}

      </section>


      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

        <h2 className="text-lg font-semibold text-slate-900">
          Evidence Limitations
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Data quality or evidence constraints detected
          by PRISM.
        </p>


        {summary.evidence_limitations?.length > 0 ? (
          <div className="mt-5 space-y-3">

            {summary.evidence_limitations.map(
              (item, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4"
                >
                  <AlertTriangle
                    size={18}
                    className="mt-0.5 shrink-0 text-amber-600"
                  />

                  <p className="text-sm text-amber-900">
                    {item}
                  </p>
                </div>
              )
            )}

          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-500">
            No evidence limitations detected.
          </p>
        )}

      </section>

    </div>
  );
}


function MetricCard({
  title,
  value,
  icon: Icon,
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

      <div className="flex items-center justify-between">

        <div>
          <p className="text-sm text-slate-500">
            {title}
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-900">
            {value}
          </p>
        </div>

        <div className="rounded-xl bg-slate-100 p-3">
          <Icon
            size={22}
            className="text-slate-700"
          />
        </div>

      </div>

    </div>
  );
}


function DistributionCard({
  title,
  data,
  icon: Icon,
}) {
  if (!data) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

      <div className="flex items-center gap-3">

        <div className="rounded-lg bg-slate-100 p-2">
          <Icon
            size={19}
            className="text-slate-700"
          />
        </div>

        <h2 className="font-semibold text-slate-900">
          {title}
        </h2>

      </div>


      <div className="mt-5 space-y-3">

        {Object.entries(data).map(
          ([key, value]) => (
            <div
              key={key}
              className="flex items-center justify-between"
            >

              <span className="text-sm text-slate-600">
                {formatLabel(key)}
              </span>

              <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-800">
                {value}
              </span>

            </div>
          )
        )}

      </div>

    </div>
  );
}


function AttentionCard({
  activity,
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">

        <div>

          <h3 className="font-semibold text-slate-900">
            {activity.activity_name}
          </h3>

          <div className="mt-3 flex flex-wrap gap-2">

            <Badge
              label={`Forecast: ${formatLabel(
                activity.forecast_status
              )}`}
            />

            <Badge
              label={`Confidence: ${formatLabel(
                activity.confidence_level
              )}`}
            />

            <Badge
              label={`Risk: ${formatLabel(
                activity.predictive_risk_level
              )}`}
            />

            <Badge
              label={`Priority: ${formatLabel(
                activity.decision_support_priority
              )}`}
            />

          </div>

        </div>


        <div className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm">
          {formatLabel(
            activity.decision_support_response
          )}
        </div>

      </div>


      {activity.decision_support_trigger && (
        <div className="mt-5">

          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Trigger
          </p>

          <p className="mt-1 text-sm text-slate-700">
            {formatLabel(
              activity.decision_support_trigger
            )}
          </p>

        </div>
      )}


      {activity.limitations?.length > 0 && (
        <div className="mt-5">

          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Limitations
          </p>

          <ul className="mt-2 space-y-2">

            {activity.limitations.map(
              (item, index) => (
                <li
                  key={index}
                  className="text-sm text-slate-600"
                >
                  • {item}
                </li>
              )
            )}

          </ul>

        </div>
      )}

    </div>
  );
}


function Badge({
  label,
}) {
  return (
    <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">
      {label}
    </span>
  );
}


function formatLabel(value) {
  if (!value) {
    return "Not assessed";
  }

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase()
    );
}