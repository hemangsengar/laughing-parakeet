import { useState } from 'react';
import { Sparkles, PlayCircle, Loader2, AlertCircle } from 'lucide-react';
import UploadZone from './components/UploadZone';
import AudioPlayer from './components/AudioPlayer';
import { startJob, subscribeProgress, fetchJobInfo, fetchBlob } from './api';
import './App.css';

export default function App() {
  const [file, setFile] = useState(null);

  const [jobState, setJobState] = useState({
    status: 'idle', // idle, running, done, error
    stage: 0,
    stageName: '',
    error: '',
    stageTimes: {},
    totalTime: 0
  });

  const [resultBlobs, setResultBlobs] = useState({ opt: null, orig: null });

  const buildConfig = () => {
    return {
      stages: {
        isolate: { enabled: true },
        denoise: { enabled: true },
        master: { enabled: true },
        normalize: { enabled: true, lufs: -14 }
      }
    };
  };

  const handleProcess = async () => {
    if (!file) return;

    setJobState({ status: 'running', stage: 0, stageName: 'Uploading...', error: '', stageTimes: {}, totalTime: 0 });
    setResultBlobs({ opt: null, orig: null });

    try {
      // Hardcode platform and reference for one-click magic
      const { job_id } = await startJob(file, 'youtube', null, buildConfig());

      subscribeProgress(job_id, async (data) => {
        setJobState(prev => ({
          ...prev,
          status: data.status,
          stage: data.stage || prev.stage,
          stageName: data.stage_name || prev.stageName,
          error: data.error || prev.error,
          stageTimes: data.stage_times || prev.stageTimes
        }));

        if (data.status === 'done') {
          try {
            const info = await fetchJobInfo(job_id);
            setJobState(prev => ({ ...prev, totalTime: info.elapsed }));

            const [opt, orig] = await Promise.all([
              fetchBlob(`/download/${job_id}`),
              fetchBlob(`/original/${job_id}`)
            ]);
            setResultBlobs({ opt, orig });
          } catch (e) {
            setJobState(prev => ({ ...prev, status: 'error', error: 'Failed to download results' }));
          }
        }
      });
    } catch (err) {
      setJobState(prev => ({ ...prev, status: 'error', error: err.message }));
    }
  };

  const reset = () => {
    setFile(null);
    setJobState({ status: 'idle', stage: 0, stageName: '', error: '', stageTimes: {}, totalTime: 0 });
    setResultBlobs({ opt: null, orig: null });
  };

  const isRunning = jobState.status === 'running';

  return (
    <div className="app-container">
      <div className="bg-glow"></div>

      <header className="header">
        <div className="badge">
          <span className="badge-dot"></span>
          Pro Audio Studio
        </div>
        <h1>Audio Optimizer</h1>
        <p className="subtitle">AI-powered mastering, denoising, and studio effects.</p>
      </header>

      <main className="main-content">
        <div className="studio-card glass">
          <div className="card-body">

            {/* 1. Upload State */}
            {jobState.status === 'idle' && !resultBlobs.opt && (
              <UploadZone
                file={file}
                onFileChange={setFile}
                disabled={isRunning}
              />
            )}

            {/* 2. Ready to Process State */}
            {jobState.status === 'idle' && file && !resultBlobs.opt && (
              <div className="controls-section">
                <button
                  className="go-btn magic-btn"
                  onClick={handleProcess}
                >
                  <Sparkles size={18} /> Enhance Audio Automatically
                </button>
              </div>
            )}

            {/* 3. Processing State */}
            {isRunning && (
              <div className="processing-state">
                <div className="magic-spinner">
                  <div className="glow-ring"></div>
                  <Loader2 className="spinner icon" size={48} />
                </div>
                <h3>Applying AI Magic...</h3>
                <p className="magic-stage">{jobState.stageName}</p>
              </div>
            )}

            {/* Error State */}
            {jobState.status === 'error' && (
              <div className="error-box">
                <AlertCircle size={18} />
                <div className="err-text">
                  <strong>Processing failed</strong>
                  <p>{jobState.error}</p>
                </div>
                <button className="reset-btn mt-2" onClick={reset}>Try Again</button>
              </div>
            )}

            {resultBlobs.opt && (
              <div className="result-section">
                <div className="result-header">
                  <Sparkles size={16} className="text-success" />
                  <h3>Optimization Complete</h3>
                  <span className="time-badge">{jobState.totalTime}s</span>
                  <button className="reset-btn" onClick={reset}>Optimize Another</button>
                </div>

                <AudioPlayer
                  optimizedBlob={resultBlobs.opt}
                  originalBlob={resultBlobs.orig}
                  platform="youtube"
                />
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="footer">
        Powered by AI Audio Models & FFmpeg
      </footer>
    </div>
  );
}
