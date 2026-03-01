// API helper for the audio optimizer backend
export async function startJob(file, platform, referenceFile, config) {
    const form = new FormData();
    form.append('file', file);
    if (referenceFile) form.append('reference', referenceFile);

    const params = new URLSearchParams({ platform, config: JSON.stringify(config) });
    const res = await fetch(`/optimize?${params}`, { method: 'POST', body: form });

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Upload failed (${res.status})`);
    }

    return res.json(); // { job_id }
}

export function subscribeProgress(jobId, onUpdate) {
    const es = new EventSource(`/progress/${jobId}`);
    es.onmessage = (ev) => {
        const data = JSON.parse(ev.data);
        onUpdate(data);
        if (data.status === 'done' || data.status === 'error') es.close();
    };
    es.onerror = () => es.close();
    return () => es.close();
}

export async function fetchJobInfo(jobId) {
    const res = await fetch(`/job/${jobId}`);
    return res.json();
}

export async function fetchBlob(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Download failed');
    return res.blob();
}
