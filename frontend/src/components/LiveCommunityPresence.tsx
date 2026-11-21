import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../api';

interface LiveCommunityPresenceProps {
  className?: string;
}

export const LiveCommunityPresence: React.FC<LiveCommunityPresenceProps> = ({ className = '' }) => {
  // 100% real live data: starts at 1 for the current active user
  const [liveCount, setLiveCount] = useState<number>(1);

  // Client session id stored in localStorage
  const clientId = useMemo(() => {
    if (typeof window === 'undefined') return 'anon';
    let id = localStorage.getItem('dat_presence_cid');
    if (!id) {
      id = 'usr_' + Math.random().toString(36).substring(2, 12);
      localStorage.setItem('dat_presence_cid', id);
    }
    return id;
  }, []);

  // Poll heartbeat ping every 20s strictly for real live active clients
  useEffect(() => {
    let mounted = true;
    const sendPing = async () => {
      try {
        const res = await api.pingPresence(clientId);
        if (mounted && typeof res?.real_connected === 'number') {
          setLiveCount(Math.max(1, res.real_connected));
        }
      } catch {
        if (mounted) {
          setLiveCount(1);
        }
      }
    };

    sendPing();
    const interval = setInterval(sendPing, 20000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [clientId]);

  // Miniature figurine matching the actual live count
  const dockImage = useMemo(() => {
    if (liveCount <= 1) return '/assets/crowd/crowd_1.png';
    if (liveCount <= 6) return '/assets/crowd/crowd_6.png';
    if (liveCount <= 20) return '/assets/crowd/crowd_18.png';
    if (liveCount <= 100) return '/assets/crowd/crowd_80.png';
    if (liveCount <= 500) return '/assets/crowd/crowd_370.png';
    return '/assets/crowd/crowd_5000.png';
  }, [liveCount]);

  return (
    <footer
      className={`fixed bottom-4 inset-x-0 mx-auto w-fit z-30 max-w-[94vw] transition-all duration-300 no-print select-none ${className}`}
      aria-label="Live Active Learners Presence"
    >
      <div className="bg-white/95 backdrop-blur-md border border-[#D8D4CB] rounded-full shadow-[0_4px_16px_rgba(0,0,0,0.06)] px-3.5 py-1.5 flex items-center gap-2.5 sm:gap-3">
        {/* Miniature 3D Figurine */}
        <div className="relative -my-1 h-7 w-7 flex items-center justify-center shrink-0">
          <img
            src={dockImage}
            alt="Candidate figurine"
            className="h-7 w-auto object-contain drop-shadow-sm"
          />
        </div>

        {/* Real Live Beacon */}
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider font-mono-exam">
            Live
          </span>
        </div>

        {/* Real Live Count Only */}
        <div className="flex items-center gap-1.5 text-xs text-[#18181B] pr-1">
          <span className="font-mono-exam font-bold text-sm text-[#1E3A5F]">{liveCount}</span>
          <span className="font-medium text-[#44403C]">
            {liveCount === 1 ? 'designer practicing live' : 'designers practicing live'}
          </span>
        </div>
      </div>
    </footer>
  );
};
