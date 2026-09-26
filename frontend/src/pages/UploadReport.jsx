import {
    useRef,
    useState,
  } from "react";
  
  import {
    UploadCloud,
    FileText,
    CheckCircle2,
    AlertCircle,
    Loader2,
    X,
  } from "lucide-react";
  
  import {
    uploadReport,
  } from "../api/prismApi";
  
  
  export default function UploadReport() {
    const inputRef = useRef(null);
  
    const [file, setFile] = useState(null);
    const [dragging, setDragging] = useState(false);
  
    const [uploading, setUploading] = useState(false);
  
    const [result, setResult] = useState(null);
    const [error, setError] = useState("");
  
  
    const chooseFile = (selectedFile) => {
      if (!selectedFile) {
        return;
      }
  
      setFile(selectedFile);
      setResult(null);
      setError("");
    };
  
  
    const handleDrop = (event) => {
      event.preventDefault();
  
      setDragging(false);
  
      const droppedFile =
        event.dataTransfer.files?.[0];
  
      chooseFile(droppedFile);
    };
  
  
    const handleUpload = async () => {
      if (!file) {
        setError(
          "Please select a report first."
        );
  
        return;
      }
  
      try {
        setUploading(true);
        setError("");
        setResult(null);
  
        const response = await uploadReport(
          file
        );
  
        setResult(response);
  
      } catch (err) {
        console.error(err);
  
        const apiMessage =
          err.response?.data?.error?.message;
  
        setError(
          apiMessage ||
            "PRISM could not process this report."
        );
      } finally {
        setUploading(false);
      }
    };
  
  
    const clearFile = () => {
      setFile(null);
      setResult(null);
      setError("");
  
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    };
  
  
    const extracted =
      result?.processing_result?.extracted_data;
  
  
    return (
      <div className="mx-auto max-w-5xl space-y-8">
  
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Upload Progress Report
          </h1>
  
          <p className="mt-2 text-sm text-slate-500">
            Upload PDF, image, Excel, or CSV reports.
            PRISM will extract project data and make it
            available to the intelligence agent.
          </p>
        </div>
  
  
        <div
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => {
            setDragging(false);
          }}
          onDrop={handleDrop}
          className={[
            "rounded-2xl border-2 border-dashed p-10 text-center transition",
            dragging
              ? "border-slate-900 bg-slate-100"
              : "border-slate-300 bg-white",
          ].join(" ")}
        >
          <UploadCloud
            size={44}
            className="mx-auto text-slate-500"
          />
  
          <h2 className="mt-4 text-lg font-semibold text-slate-900">
            Drop your construction report here
          </h2>
  
          <p className="mt-2 text-sm text-slate-500">
            PDF, PNG, JPG, Excel, or CSV
          </p>
  
          <button
            onClick={() =>
              inputRef.current?.click()
            }
            className="mt-6 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
          >
            Select File
          </button>
  
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.xlsx,.xls,.csv"
            className="hidden"
            onChange={(event) =>
              chooseFile(
                event.target.files?.[0]
              )
            }
          />
        </div>
  
  
        {file && (
          <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
  
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-slate-100 p-2">
                <FileText
                  size={22}
                  className="text-slate-700"
                />
              </div>
  
              <div>
                <p className="font-medium text-slate-900">
                  {file.name}
                </p>
  
                <p className="text-xs text-slate-500">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
  
  
            <div className="flex items-center gap-2">
  
              <button
                onClick={clearFile}
                disabled={uploading}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={18} />
              </button>
  
  
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="flex items-center gap-2 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-60"
              >
                {uploading ? (
                  <>
                    <Loader2
                      size={17}
                      className="animate-spin"
                    />
                    Processing...
                  </>
                ) : (
                  <>
                    <UploadCloud size={17} />
                    Upload & Analyze
                  </>
                )}
              </button>
  
            </div>
          </div>
        )}
  
  
        {error && (
          <div className="flex gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <AlertCircle size={20} />
            {error}
          </div>
        )}
  
  
        {result && (
          <div className="rounded-2xl border border-emerald-200 bg-white p-6 shadow-sm">
  
            <div className="flex items-center gap-3">
              <CheckCircle2
                size={24}
                className="text-emerald-600"
              />
  
              <div>
                <h2 className="font-semibold text-slate-900">
                  Report processed successfully
                </h2>
  
                <p className="text-sm text-slate-500">
                  PRISM has added the extracted data
                  to the current analysis session.
                </p>
              </div>
            </div>
  
  
            {extracted && (
              <div className="mt-6 grid gap-4 md:grid-cols-2">
  
                <InfoCard
                  label="Project"
                  value={
                    extracted.project_name ||
                    "Not detected"
                  }
                />
  
                <InfoCard
                  label="Report Date"
                  value={
                    extracted.report_date ||
                    "Not detected"
                  }
                />
  
                <InfoCard
                  label="Location"
                  value={
                    extracted.location ||
                    "Not detected"
                  }
                />
  
                <InfoCard
                  label="Activities"
                  value={
                    extracted.activities?.length ?? 0
                  }
                />
  
              </div>
            )}
  
  
            {extracted?.activities?.length > 0 && (
              <div className="mt-6">
  
                <h3 className="mb-3 font-semibold text-slate-900">
                  Extracted Activities
                </h3>
  
                <div className="space-y-3">
  
                  {extracted.activities.map(
                    (activity, index) => (
                      <div
                        key={`${activity.activity_name}-${index}`}
                        className="rounded-xl bg-slate-50 p-4"
                      >
                        <div className="flex items-center justify-between">
  
                          <div>
                            <p className="font-medium text-slate-900">
                              {activity.activity_name}
                            </p>
  
                            <p className="mt-1 text-sm text-slate-500">
                              {activity.status ||
                                "Status unavailable"}
                            </p>
                          </div>
  
                          <div className="text-right">
                            <p className="text-xl font-bold text-slate-900">
                              {activity.progress_percentage ??
                                "—"}
                              {activity.progress_percentage !=
                                null && "%"}
                            </p>
  
                            <p className="text-xs text-slate-500">
                              Progress
                            </p>
                          </div>
  
                        </div>
                      </div>
                    )
                  )}
  
                </div>
              </div>
            )}
  
          </div>
        )}
  
      </div>
    );
  }
  
  
  function InfoCard({
    label,
    value,
  }) {
    return (
      <div className="rounded-xl bg-slate-50 p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {label}
        </p>
  
        <p className="mt-1 font-semibold text-slate-900">
          {value}
        </p>
      </div>
    );
  }