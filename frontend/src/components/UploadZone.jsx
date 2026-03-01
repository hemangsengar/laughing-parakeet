import { useCallback, useRef, useState } from 'react';
import { Upload, Music, X } from 'lucide-react';
import './UploadZone.css';

export default function UploadZone({ file, onFileChange, disabled }) {
    const [dragOver, setDragOver] = useState(false);
    const inputRef = useRef();

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setDragOver(false);
        if (e.dataTransfer.files.length) onFileChange(e.dataTransfer.files[0]);
    }, [onFileChange]);

    const handleClick = () => !disabled && inputRef.current.click();

    const fmt = (b) => b < 1048576 ? (b / 1024).toFixed(1) + ' KB' : (b / 1048576).toFixed(1) + ' MB';

    return (
        <div
            className={`upload-zone ${file ? 'has-file' : ''} ${dragOver ? 'drag-over' : ''} ${disabled ? 'locked' : ''}`}
            onClick={handleClick}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
        >
            <div className="upload-zone__icon">
                {file ? <Music size={20} /> : <Upload size={20} />}
            </div>

            {!file ? (
                <>
                    <p className="upload-zone__title">Drop your audio file here</p>
                    <p className="upload-zone__hint">WAV · MP3 · M4A · FLAC · OGG · AAC</p>
                </>
            ) : (
                <div className="upload-zone__file">
                    <span className="upload-zone__name">{file.name}</span>
                    <span className="upload-zone__size">{fmt(file.size)}</span>
                    <button className="upload-zone__remove" onClick={(e) => { e.stopPropagation(); onFileChange(null); }}>
                        <X size={14} />
                    </button>
                </div>
            )}

            <input
                ref={inputRef}
                type="file"
                accept=".wav,.mp3,.m4a,.flac,.ogg,.aac,.wma"
                hidden
                onChange={(e) => e.target.files.length && onFileChange(e.target.files[0])}
            />
        </div>
    );
}
