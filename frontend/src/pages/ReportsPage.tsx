import { useState } from 'react'
import { Link } from 'react-router-dom'
import { prismApi } from '../lib/api'
import { StatePanel } from '../components/StatePanel'
import { SectionHeader } from '../components/SectionHeader'

export function ReportsPage() {
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')
  const select = (candidate: File | undefined) => { if (candidate) { setFile(candidate); setStatus('idle'); setMessage('') } }
  const upload = async () => { if (!file) return; setStatus('uploading'); try { const response = await prismApi.uploadReport(file); setStatus('success'); setMessage(`${response.original_filename} was processed successfully.`) } catch (error) { setStatus('error'); setMessage(error instanceof Error ? error.message : 'The report could not be processed.') } }
  return <div className="page"><SectionHeader eyebrow="Reports" title="Add a progress report" description="Upload a supported report and PRISM will extract, validate, and refresh its analytical evidence on the server." />
    <section className="upload-layout"><div className="panel upload-panel"><label className="drop-zone" onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); select(event.dataTransfer.files[0]) }}><input type="file" accept=".pdf,.png,.jpg,.jpeg,.xlsx,.xls,.csv" onChange={event => select(event.target.files?.[0])} /><span className="upload-icon">↥</span><strong>{file ? file.name : 'Drop a report here or browse'}</strong><span>PDF, PNG, JPG, XLSX, XLS, or CSV · up to 10 MiB</span></label>{file && <div className="selected-file"><span>{file.name}</span><button className="text-button" onClick={() => setFile(null)}>Remove</button></div>}<button className="button upload-button" disabled={!file || status === 'uploading'} onClick={upload}>{status === 'uploading' ? 'Processing report…' : 'Process report'}</button></div><div className="panel upload-info"><span className="eyebrow">Server-side processing</span><h2>What happens next</h2><ol><li>The report is sent to the FastAPI upload endpoint.</li><li>Extraction and schema validation happen on the server.</li><li>Recorded project history becomes available after processing.</li></ol><p className="muted">PRISM does not expose extraction credentials to the browser.</p></div></section>
    {status === 'success' && <StatePanel kind="info" title="Report processed" message={message} action={<Link className="button secondary" to="/projects">View projects</Link>} />}{status === 'error' && <StatePanel kind="error" title="Report processing failed" message={message} />}
  </div>
}
