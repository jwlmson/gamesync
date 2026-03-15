import { useState, useRef, useCallback } from 'react';
import { Music, Upload, Play, Pause, Trash2 } from 'lucide-react';
import { getSounds, uploadSound, deleteSound, getSoundFileUrl, type SoundAsset } from '../api/client';
import { useApi } from '../hooks/useApi';

type Tab = 'built_in' | 'custom';

export default function SoundLibraryScreen() {
  const [activeTab, setActiveTab] = useState<Tab>('built_in');
  const [currentlyPlaying, setCurrentlyPlaying] = useState<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [deleteInProgress, setDeleteInProgress] = useState<number | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const {
    data: builtInSounds,
    loading: builtInLoading,
    error: builtInError,
    refetch: refetchBuiltIn,
  } = useApi(() => getSounds('built_in'), []);

  const {
    data: customSounds,
    loading: customLoading,
    error: customError,
    refetch: refetchCustom,
  } = useApi(() => getSounds('custom'), []);

  const sounds = activeTab === 'built_in' ? builtInSounds : customSounds;
  const loading = activeTab === 'built_in' ? builtInLoading : customLoading;
  const error = activeTab === 'built_in' ? builtInError : customError;

  const handlePlay = useCallback((sound: SoundAsset) => {
    // If clicking the same sound that's playing, toggle pause/play
    if (currentlyPlaying === sound.id && audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play();
        setIsPlaying(true);
      }
      return;
    }

    // Stop any currently playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
    }

    const audio = new Audio(getSoundFileUrl(sound.id));
    audio.addEventListener('ended', () => {
      setCurrentlyPlaying(null);
      setIsPlaying(false);
    });
    audio.addEventListener('error', () => {
      setCurrentlyPlaying(null);
      setIsPlaying(false);
    });
    audio.play();
    audioRef.current = audio;
    setCurrentlyPlaying(sound.id);
    setIsPlaying(true);
  }, [currentlyPlaying, isPlaying]);

  const handleUpload = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/x-wav'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|ogg)$/i)) {
      setUploadError('Only MP3, WAV, and OGG files are accepted.');
      return;
    }

    setUploadError(null);
    setUploadProgress(0);

    try {
      // Simulate progress since fetch doesn't natively support upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev === null || prev >= 90) return prev;
          return prev + 10;
        });
      }, 200);

      await uploadSound(file);

      clearInterval(progressInterval);
      setUploadProgress(100);

      // Brief delay to show 100% then clear
      setTimeout(() => setUploadProgress(null), 600);
      refetchCustom();
    } catch (e: any) {
      setUploadError(e.message || 'Upload failed');
      setUploadProgress(null);
    }
  }, [refetchCustom]);

  const handleDelete = useCallback(async (sound: SoundAsset) => {
    if (deleteInProgress) return;

    setDeleteInProgress(sound.id);
    try {
      // Stop playback if deleting the currently playing sound
      if (currentlyPlaying === sound.id && audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
        setCurrentlyPlaying(null);
        setIsPlaying(false);
      }
      await deleteSound(sound.id);
      refetchCustom();
    } catch (e: any) {
      // Could show an error toast here
      console.error('Delete failed:', e.message);
    } finally {
      setDeleteInProgress(null);
    }
  }, [deleteInProgress, currentlyPlaying, refetchCustom]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleUpload(e.dataTransfer.files);
  };

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="max-w-[1920px] mx-auto px-6 py-8">
      {/* Page Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 border-2 border-navy bg-navy flex items-center justify-center">
          <Music className="w-6 h-6 text-cream" />
        </div>
        <div>
          <h2 className="font-rokkitt text-3xl font-bold text-navy uppercase tracking-wide">
            Sound Library
          </h2>
          <p className="font-archivo text-sm text-muted uppercase tracking-wider">
            Manage built-in and custom sound effects
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b-2 border-navy mb-6">
        <button
          onClick={() => setActiveTab('built_in')}
          className={`px-6 py-3 font-archivo text-sm font-bold uppercase tracking-wider transition-colors ${
            activeTab === 'built_in'
              ? 'text-accent border-b-4 border-accent -mb-[2px]'
              : 'text-muted hover:text-navy'
          }`}
        >
          Built-In
        </button>
        <button
          onClick={() => setActiveTab('custom')}
          className={`px-6 py-3 font-archivo text-sm font-bold uppercase tracking-wider transition-colors ${
            activeTab === 'custom'
              ? 'text-accent border-b-4 border-accent -mb-[2px]'
              : 'text-muted hover:text-navy'
          }`}
        >
          Custom
        </button>
      </div>

      {/* Upload Zone (Custom tab only) */}
      {activeTab === 'custom' && (
        <div className="mb-6">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`card-hard p-8 text-center cursor-pointer transition-colors ${
              dragOver ? 'bg-accent/10 border-accent' : 'hover:bg-navy/5'
            }`}
          >
            <Upload className="w-10 h-10 text-muted mx-auto mb-3" />
            <p className="font-archivo text-sm font-bold text-navy uppercase tracking-wider mb-1">
              Drop audio files here or click to browse
            </p>
            <p className="font-archivo text-xs text-muted">
              Accepts MP3, WAV, OGG
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".mp3,.wav,.ogg,audio/mpeg,audio/wav,audio/ogg"
              className="hidden"
              onChange={(e) => handleUpload(e.target.files)}
            />
          </div>

          {/* Upload Progress */}
          {uploadProgress !== null && (
            <div className="mt-3">
              <div className="w-full h-3 border-2 border-navy bg-cream">
                <div
                  className="h-full bg-accent transition-all duration-200"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="font-archivo text-xs text-muted mt-1 uppercase tracking-wider">
                {uploadProgress < 100 ? `Uploading... ${uploadProgress}%` : 'Upload complete!'}
              </p>
            </div>
          )}

          {/* Upload Error */}
          {uploadError && (
            <div className="mt-3 p-3 border-2 border-red-700 bg-red-50 text-red-700">
              <p className="font-archivo text-sm font-bold">{uploadError}</p>
            </div>
          )}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="card-hard p-12 text-center">
          <p className="font-archivo text-sm font-bold text-muted uppercase tracking-wider animate-pulse">
            Loading sounds...
          </p>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="card-hard p-8 text-center">
          <p className="font-archivo text-sm font-bold text-red-700 uppercase tracking-wider mb-4">
            {error}
          </p>
          <button
            onClick={activeTab === 'built_in' ? refetchBuiltIn : refetchCustom}
            className="btn-secondary text-xs"
          >
            Retry
          </button>
        </div>
      )}

      {/* Sound List */}
      {!loading && !error && sounds && (
        <>
          {sounds.length === 0 ? (
            <div className="card-hard p-12 text-center">
              <Music className="w-10 h-10 text-muted mx-auto mb-3 opacity-40" />
              <p className="font-archivo text-sm font-bold text-muted uppercase tracking-wider">
                {activeTab === 'built_in'
                  ? 'No built-in sounds available'
                  : 'No custom sounds yet. Upload one above!'}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {sounds.map((sound) => (
                <div
                  key={sound.id}
                  className={`card-hard flex items-center gap-4 px-5 py-4 transition-colors ${
                    currentlyPlaying === sound.id ? 'bg-accent/5' : ''
                  }`}
                >
                  {/* Play/Pause Button */}
                  <button
                    onClick={() => handlePlay(sound)}
                    className="w-10 h-10 border-2 border-navy flex items-center justify-center flex-shrink-0 hover:bg-accent hover:text-cream transition-colors"
                    title={currentlyPlaying === sound.id && isPlaying ? 'Pause' : 'Play'}
                  >
                    {currentlyPlaying === sound.id && isPlaying ? (
                      <Pause className="w-5 h-5" />
                    ) : (
                      <Play className="w-5 h-5 ml-0.5" />
                    )}
                  </button>

                  {/* Sound Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-archivo text-sm font-bold text-navy truncate">
                      {sound.name}
                    </p>
                    <p className="font-archivo text-xs text-muted">
                      {formatDuration(sound.duration_seconds)} &middot; {formatFileSize(sound.file_size_bytes)}
                    </p>
                  </div>

                  {/* Duration Badge */}
                  <span className="font-archivo text-xs font-bold text-muted bg-navy/10 px-3 py-1 border border-navy/20 flex-shrink-0">
                    {formatDuration(sound.duration_seconds)}
                  </span>

                  {/* Delete Button (Custom tab only) */}
                  {activeTab === 'custom' && (
                    <button
                      onClick={() => handleDelete(sound)}
                      disabled={deleteInProgress === sound.id}
                      className={`w-10 h-10 border-2 border-navy flex items-center justify-center flex-shrink-0 transition-colors ${
                        deleteInProgress === sound.id
                          ? 'opacity-50 cursor-not-allowed'
                          : 'hover:bg-red-700 hover:border-red-700 hover:text-cream'
                      }`}
                      title="Delete sound"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
