import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Video, 
  MessageSquare, 
  Mic, 
  MicOff, 
  VideoOff, 
  Send, 
  Sparkles, 
  Clock, 
  ChevronRight, 
  AlertCircle,
  Lightbulb,
  MoreVertical
} from 'lucide-react';

// --- Sub-Components ---

const Badge = ({ children, variant = 'default' }) => {
  const styles = {
    default: "bg-white/10 text-slate-300",
    success: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[variant]}`}>
      {children}
    </span>
  );
};

const GlassCard = ({ children, className = "" }) => (
  <div className={`bg-white/[0.03] backdrop-blur-xl border border-white/[0.08] rounded-2xl ${className}`}>
    {children}
  </div>
);

const WebcamPreview = () => {
  const videoRef = useRef(null);
  const [isCameraOn, setIsCameraOn] = useState(true);

  useEffect(() => {
    if (isCameraOn) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => { if (videoRef.current) videoRef.current.srcObject = stream; })
        .catch(err => console.error("Camera error:", err));
    }
    return () => {
      if (videoRef.current?.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      }
    };
  }, [isCameraOn]);

  return (
    <GlassCard className="relative overflow-hidden aspect-video bg-black flex items-center justify-center">
      {isCameraOn ? (
        <video ref={videoRef} autoPlay muted className="w-full h-full object-cover" />
      ) : (
        <div className="flex flex-col items-center gap-3 text-slate-500">
          <VideoOff size={48} strokeWidth={1.5} />
          <span className="text-sm">Camera is off</span>
        </div>
      )}
      <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10">
        <motion.div 
          animate={{ opacity: [1, 0.5, 1] }} 
          transition={{ duration: 1.5, repeat: Infinity }}
          className="w-2 h-2 rounded-full bg-red-500" 
        />
        <span className="text-[10px] font-bold uppercase tracking-wider text-white">Live Recording</span>
      </div>
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-3">
        <button onClick={() => setIsCameraOn(!isCameraOn)} className="p-3 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
          {isCameraOn ? <Video size={20} /> : <VideoOff size={20} className="text-red-400" />}
        </button>
        <button className="p-3 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
          <Mic size={20} />
        </button>
      </div>
    </GlassCard>
  );
};

// --- Main Components ---

export default function InterviewSimulator() {
  const [mode, setMode] = useState('video'); // 'video' | 'text'
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  return (
    <div className="min-h-screen bg-[#050b14] text-slate-200 ml-[var(--sidebar-width)] p-8 font-sans">
      {/* Header */}
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white mb-2">AI Interview Simulator</h1>
          <p className="text-slate-400 text-sm">Practice your technical and behavioral skills with real-time feedback.</p>
        </div>
        
        <div className="flex bg-white/[0.04] p-1 rounded-xl border border-white/5">
          <button 
            onClick={() => setMode('video')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${mode === 'video' ? 'bg-white/10 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}
          >
            <Video size={16} /> Video Mode
          </button>
          <button 
            onClick={() => setMode('text')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${mode === 'text' ? 'bg-white/10 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}
          >
            <MessageSquare size={16} /> Text Mode
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {mode === 'video' ? (
          <motion.div 
            key="video-mode"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="grid grid-cols-12 gap-6 h-[calc(100vh-220px)]"
          >
            {/* Left: Webcam */}
            <div className="col-span-4 flex flex-col gap-6">
              <WebcamPreview />
              <GlassCard className="p-6 flex-1">
                <div className="flex items-center gap-2 mb-4 text-slate-300 font-medium">
                  <Lightbulb size={18} className="text-amber-400" />
                  AI Tips
                </div>
                <ul className="space-y-4 text-sm text-slate-400">
                  <li className="flex gap-3">
                    <span className="text-emerald-400 font-mono">01.</span>
                    Maintain eye contact with the camera to simulate engagement.
                  </li>
                  <li className="flex gap-3">
                    <span className="text-emerald-400 font-mono">02.</span>
                    Mention specific metrics when discussing your past projects.
                  </li>
                </ul>
              </GlassCard>
            </div>

            {/* Center: Question */}
            <div className="col-span-5">
              <GlassCard className="h-full p-8 flex flex-col relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8">
                  <Badge variant="warning">Medium</Badge>
                </div>
                
                <div className="mb-12">
                  <span className="text-emerald-400 font-mono text-xs uppercase tracking-[0.2em] mb-2 block">Question 03 of 08</span>
                  <h2 className="text-2xl font-medium text-white leading-relaxed">
                    "How would you optimize a React application that is experiencing performance bottlenecks in a large list of components?"
                  </h2>
                </div>

                <div className="mt-auto space-y-6">
                   <div className="flex items-center justify-between text-sm border-t border-white/5 pt-6">
                      <div className="flex items-center gap-2 text-slate-400">
                        <Clock size={16} /> 01:45 remaining
                      </div>
                      <div className="flex gap-2">
                        <Badge>React</Badge>
                        <Badge>Performance</Badge>
                      </div>
                   </div>

                   {isAnalyzing ? (
                     <div className="flex items-center gap-3 p-4 bg-emerald-500/5 rounded-xl border border-emerald-500/10">
                        <motion.div 
                          animate={{ rotate: 360 }} 
                          transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                        >
                          <Sparkles size={18} className="text-emerald-400" />
                        </motion.div>
                        <span className="text-sm text-emerald-400">AI is analyzing your body language and tone...</span>
                     </div>
                   ) : (
                     <button 
                       onClick={() => setIsAnalyzing(true)}
                       className="w-full py-4 bg-white text-black font-semibold rounded-xl hover:bg-slate-200 transition-colors flex items-center justify-center gap-2"
                     >
                       Submit Answer <ChevronRight size={18} />
                     </button>
                   )}
                </div>
              </GlassCard>
            </div>

            {/* Right: Notes */}
            <div className="col-span-3">
               <GlassCard className="h-full flex flex-col">
                  <div className="p-4 border-b border-white/5 flex justify-between items-center">
                    <span className="text-xs font-bold uppercase tracking-widest text-slate-500">Scratchpad</span>
                    <button className="text-slate-500 hover:text-white"><MoreVertical size={16} /></button>
                  </div>
                  <textarea 
                    className="flex-1 bg-transparent p-6 outline-none resize-none text-sm leading-relaxed text-slate-300 placeholder:text-slate-600"
                    placeholder="Jot down your thoughts here..."
                  />
               </GlassCard>
            </div>
          </motion.div>
        ) : (
          /* Text Interview Mode */
          <motion.div 
            key="text-mode"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="grid grid-cols-12 gap-6 h-[calc(100vh-220px)]"
          >
            <div className="col-span-8 flex flex-col gap-4 overflow-hidden">
               <GlassCard className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
                  <div className="flex gap-4">
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
                      <Sparkles size={16} />
                    </div>
                    <div className="bg-white/[0.05] p-4 rounded-2xl rounded-tl-none border border-white/5 max-w-[80%]">
                      <p className="text-sm leading-relaxed">
                        Great explanation of closures. Now, let's move to system design. How would you design a highly scalable real-time notification system?
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4 flex-row-reverse">
                    <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-white shrink-0">
                      AT
                    </div>
                    <div className="bg-emerald-500/10 p-4 rounded-2xl rounded-tr-none border border-emerald-500/20 max-w-[80%]">
                      <p className="text-sm leading-relaxed">
                        I would start by using a WebSocket-based architecture for the real-time connection, backed by a Redis Pub/Sub mechanism...
                      </p>
                    </div>
                  </div>
               </GlassCard>

               <div className="relative">
                  <textarea 
                    className="w-full h-32 bg-white/[0.03] border border-white/10 rounded-2xl p-6 pr-20 outline-none focus:border-emerald-500/50 transition-colors text-sm placeholder:text-slate-600 resize-none"
                    placeholder="Type your detailed answer here..."
                  />
                  <button className="absolute bottom-6 right-6 p-3 bg-white text-black rounded-xl hover:bg-slate-200 transition-all shadow-xl">
                    <Send size={18} />
                  </button>
               </div>
            </div>

            <div className="col-span-4 space-y-6">
              <GlassCard className="p-6">
                <h3 className="text-sm font-medium text-white mb-4">Confidence Score</h3>
                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden mb-2">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: '78%' }}
                    className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400"
                  />
                </div>
                <div className="flex justify-between text-[10px] font-bold uppercase text-slate-500">
                  <span>Analyzing...</span>
                  <span>78%</span>
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <h3 className="text-sm font-medium text-white mb-4">Keywords Detected</h3>
                <div className="flex flex-wrap gap-2">
                  {['Scalability', 'WebSockets', 'Latency', 'Redis', 'Load Balancing'].map(tag => (
                    <Badge key={tag}>{tag}</Badge>
                  ))}
                </div>
              </GlassCard>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}