import { useState } from 'react';
import { ChevronDown, Sliders, Wind, Volume2, Mic2 } from 'lucide-react';
import './EffectsPanel.css';

export default function EffectsPanel({ effects, onEffectsChange, disabled }) {
    const [isOpen, setIsOpen] = useState(false);

    const toggleEffect = (fx, e) => {
        e.stopPropagation();
        if (disabled) return;
        onEffectsChange({
            ...effects,
            [fx]: { ...effects[fx], enabled: !effects[fx].enabled }
        });
    };

    const updateParam = (fx, param, value) => {
        onEffectsChange({
            ...effects,
            [fx]: { ...effects[fx], [param]: value }
        });
    };

    return (
        <div className={`fx-panel ${disabled ? 'locked' : ''}`}>
            <div
                className="fx-header"
                onClick={() => setIsOpen(!isOpen)}
                role="button"
                aria-expanded={isOpen}
            >
                <Sliders size={16} className="fx-header-icon" />
                <h3>Advanced Studio Effects</h3>
                <span className="fx-subtitle">(Optional)</span>
                <ChevronDown size={16} className={`fx-arrow ${isOpen ? 'open' : ''}`} />
            </div>

            <div className={`fx-body ${isOpen ? 'open' : ''}`}>

                {/* Wind Removal */}
                <div className="fx-section">
                    <div className="fx-row">
                        <Wind size={18} className="fx-icon" />
                        <span className="fx-label">Wind Removal & Low Cut</span>
                        <button
                            className={`fx-toggle ${effects.wind_removal.enabled ? 'on' : 'off'}`}
                            onClick={(e) => toggleEffect('wind_removal', e)}
                            disabled={disabled}
                        >
                            <div className="toggle-thumb" />
                        </button>
                    </div>
                    <div className="slider-group full">
                        <div className="slider-item">
                            <label>
                                Cutoff Frequency
                                <span className="val">{effects.wind_removal.cutoff} Hz</span>
                            </label>
                            <input
                                type="range" min="40" max="200" step="5"
                                value={effects.wind_removal.cutoff}
                                onChange={(e) => updateParam('wind_removal', 'cutoff', parseInt(e.target.value))}
                                disabled={!effects.wind_removal.enabled || disabled}
                            />
                        </div>
                    </div>
                </div>

                {/* 3-Band EQ */}
                <div className="fx-section">
                    <div className="fx-row">
                        <Sliders size={18} className="fx-icon" />
                        <span className="fx-label">3-Band Parametric EQ</span>
                        <button
                            className={`fx-toggle ${effects.eq.enabled ? 'on' : 'off'}`}
                            onClick={(e) => toggleEffect('eq', e)}
                            disabled={disabled}
                        >
                            <div className="toggle-thumb" />
                        </button>
                    </div>
                    <div className="slider-group triple">
                        <div className="slider-item">
                            <label>Low (200Hz) <span className="val">{effects.eq.low > 0 ? '+' : ''}{effects.eq.low} dB</span></label>
                            <input
                                type="range" min="-12" max="12" step="0.5"
                                value={effects.eq.low}
                                onChange={(e) => updateParam('eq', 'low', parseFloat(e.target.value))}
                                disabled={!effects.eq.enabled || disabled}
                            />
                        </div>
                        <div className="slider-item">
                            <label>Mid (1kHz) <span className="val">{effects.eq.mid > 0 ? '+' : ''}{effects.eq.mid} dB</span></label>
                            <input
                                type="range" min="-12" max="12" step="0.5"
                                value={effects.eq.mid}
                                onChange={(e) => updateParam('eq', 'mid', parseFloat(e.target.value))}
                                disabled={!effects.eq.enabled || disabled}
                            />
                        </div>
                        <div className="slider-item">
                            <label>High (4kHz) <span className="val">{effects.eq.high > 0 ? '+' : ''}{effects.eq.high} dB</span></label>
                            <input
                                type="range" min="-12" max="12" step="0.5"
                                value={effects.eq.high}
                                onChange={(e) => updateParam('eq', 'high', parseFloat(e.target.value))}
                                disabled={!effects.eq.enabled || disabled}
                            />
                        </div>
                    </div>
                </div>

                {/* Compressor */}
                <div className="fx-section">
                    <div className="fx-row">
                        <Volume2 size={18} className="fx-icon" />
                        <span className="fx-label">Vocal Compressor</span>
                        <button
                            className={`fx-toggle ${effects.compressor.enabled ? 'on' : 'off'}`}
                            onClick={(e) => toggleEffect('compressor', e)}
                            disabled={disabled}
                        >
                            <div className="toggle-thumb" />
                        </button>
                    </div>
                    <div className="slider-group grid-2x2">
                        <div className="slider-item">
                            <label>Threshold <span className="val">{effects.compressor.threshold} dB</span></label>
                            <input
                                type="range" min="-60" max="0" step="1"
                                value={effects.compressor.threshold}
                                onChange={(e) => updateParam('compressor', 'threshold', parseFloat(e.target.value))}
                                disabled={!effects.compressor.enabled || disabled}
                            />
                        </div>
                        <div className="slider-item">
                            <label>Ratio <span className="val">{effects.compressor.ratio}:1</span></label>
                            <input
                                type="range" min="1" max="20" step="0.5"
                                value={effects.compressor.ratio}
                                onChange={(e) => updateParam('compressor', 'ratio', parseFloat(e.target.value))}
                                disabled={!effects.compressor.enabled || disabled}
                            />
                        </div>
                        <div className="slider-item">
                            <label>Attack <span className="val">{effects.compressor.attack} ms</span></label>
                            <input
                                type="range" min="0.1" max="100" step="0.5"
                                value={effects.compressor.attack}
                                onChange={(e) => updateParam('compressor', 'attack', parseFloat(e.target.value))}
                                disabled={!effects.compressor.enabled || disabled}
                            />
                        </div>
                        <div className="slider-item">
                            <label>Release <span className="val">{effects.compressor.release} ms</span></label>
                            <input
                                type="range" min="5" max="500" step="5"
                                value={effects.compressor.release}
                                onChange={(e) => updateParam('compressor', 'release', parseFloat(e.target.value))}
                                disabled={!effects.compressor.enabled || disabled}
                            />
                        </div>
                    </div>
                </div>

                {/* Reverb */}
                <div className="fx-section">
                    <div className="fx-row">
                        <Mic2 size={18} className="fx-icon" />
                        <span className="fx-label">Studio Reverb</span>
                        <button
                            className={`fx-toggle ${effects.reverb.enabled ? 'on' : 'off'}`}
                            onClick={(e) => toggleEffect('reverb', e)}
                            disabled={disabled}
                        >
                            <div className="toggle-thumb" />
                        </button>
                    </div>
                    <div className="slider-group">
                        <div className="slider-item">
                            <label>Room Size <span className="val">{Math.round(effects.reverb.room * 100)}%</span></label>
                            <input
                                type="range" min="5" max="100" step="1"
                                value={Math.round(effects.reverb.room * 100)}
                                onChange={(e) => updateParam('reverb', 'room', parseInt(e.target.value) / 100)}
                                disabled={!effects.reverb.enabled || disabled}
                            />
                        </div>
                        <div className="slider-item">
                            <label>Wet/Dry Mix <span className="val">{Math.round(effects.reverb.wet * 100)}%</span></label>
                            <input
                                type="range" min="0" max="80" step="1"
                                value={Math.round(effects.reverb.wet * 100)}
                                onChange={(e) => updateParam('reverb', 'wet', parseInt(e.target.value) / 100)}
                                disabled={!effects.reverb.enabled || disabled}
                            />
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
