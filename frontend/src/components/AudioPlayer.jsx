import { useState, useRef, useEffect } from 'react';
import { Play, Pause, Download } from 'lucide-react';
import './AudioPlayer.css';

export default function AudioPlayer({ optimizedBlob, originalBlob, platform }) {
    const [activeTab, setActiveTab] = useState('optimized');
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [waveformError, setWaveformError] = useState(false);

    const audioRef = useRef(null);
    const canvasRef = useRef(null);
    const audioCtxRef = useRef(null);

    const activeBlob = activeTab === 'optimized' ? optimizedBlob : originalBlob;

    // Setup audio element
    useEffect(() => {
        if (!activeBlob) return;

        const url = URL.createObjectURL(activeBlob);
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.src = url;
            setIsPlaying(false);
            setCurrentTime(0);
        } else {
            audioRef.current = new Audio(url);
            audioRef.current.addEventListener('timeupdate', () => {
                setCurrentTime(audioRef.current.currentTime);
            });
            audioRef.current.addEventListener('loadedmetadata', () => {
                setDuration(audioRef.current.duration);
            });
            audioRef.current.addEventListener('ended', () => {
                setIsPlaying(false);
                setCurrentTime(0);
            });
        }

        drawWaveform(activeBlob);

        return () => URL.revokeObjectURL(url);
    }, [activeBlob]);

    const togglePlay = () => {
        if (!audioRef.current) return;
        if (isPlaying) {
            audioRef.current.pause();
        } else {
            audioRef.current.play();
        }
        setIsPlaying(!isPlaying);
    };

    const handleSeek = (e) => {
        if (!audioRef.current || !duration) return;
        const time = (e.target.value / 1000) * duration;
        audioRef.current.currentTime = time;
        setCurrentTime(time);
    };

    const drawWaveform = async (blob) => {
        setWaveformError(false);
        try {
            if (!audioCtxRef.current) {
                audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
            }
            const buf = await blob.arrayBuffer();
            const decoded = await audioCtxRef.current.decodeAudioData(buf);
            const data = decoded.getChannelData(0);

            const canvas = canvasRef.current;
            if (!canvas) return;

            const dpr = window.devicePixelRatio || 1;
            const w = canvas.parentElement.clientWidth;
            const h = canvas.parentElement.clientHeight;
            canvas.width = w * dpr;
            canvas.height = h * dpr;
            canvas.style.width = w + 'px';
            canvas.style.height = h + 'px';

            const ctx = canvas.getContext('2d');
            ctx.scale(dpr, dpr);
            ctx.clearRect(0, 0, w, h);

            const step = Math.ceil(data.length / w);
            const mid = h / 2;

            const gradient = ctx.createLinearGradient(0, 0, w, 0);
            if (activeTab === 'optimized') {
                gradient.addColorStop(0, '#7c5cfc');
                gradient.addColorStop(1, '#a78bfa');
            } else {
                gradient.addColorStop(0, '#6b6b6b');
                gradient.addColorStop(1, '#a3a3a3');
            }
            ctx.fillStyle = gradient;

            for (let i = 0; i < w; i++) {
                let min = 1, max = -1;
                for (let j = 0; j < step; j++) {
                    const v = data[i * step + j] || 0;
                    if (v < min) min = v;
                    if (v > max) max = v;
                }
                const barH = Math.max(1, (max - min) * mid * 0.9);
                ctx.fillRect(i, mid - barH / 2, 1, barH);
            }
        } catch (e) {
            console.error('Waveform error', e);
            setWaveformError(true);
        }
    };

    const downloadFile = () => {
        if (!optimizedBlob) return;
        const url = URL.createObjectURL(optimizedBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `optimized_${platform}.wav`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const fmtTime = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
    const progress = duration ? (currentTime / duration) * 1000 : 0;

    if (!optimizedBlob) return null;

    return (
        <div className="audio-player glass">
            <div className="ap-tabs">
                <button
                    className={`ap-tab ${activeTab === 'optimized' ? 'active' : ''}`}
                    onClick={() => setActiveTab('optimized')}
                >
                    🔊 Optimized
                </button>
                <button
                    className={`ap-tab ${activeTab === 'original' ? 'active' : ''}`}
                    onClick={() => setActiveTab('original')}
                >
                    📁 Original
                </button>
            </div>

            <div className="ap-body">
                <div className="waveform-box">
                    <canvas ref={canvasRef} className="waveform-canvas" />
                    {waveformError && <div className="waveform-overlay">Could not render waveform</div>}
                </div>

                <div className="ap-controls">
                    <button className={`play-btn ${isPlaying ? 'playing' : ''}`} onClick={togglePlay}>
                        {isPlaying ? <Pause size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" className="ml-1" />}
                    </button>

                    <input
                        type="range"
                        className="seek-bar"
                        min="0" max="1000"
                        value={progress}
                        onChange={handleSeek}
                    />

                    <span className="time-display">
                        {fmtTime(currentTime)} / {fmtTime(duration)}
                    </span>
                </div>
            </div>

            <div className="ap-footer">
                <button className="dl-btn" onClick={downloadFile}>
                    <Download size={18} />
                    Download Optimized WAV
                </button>
            </div>
        </div>
    );
}
