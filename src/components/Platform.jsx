import React from 'react';
import { motion } from 'framer-motion';
import { 
  FileSearch, 
  Map, 
  MessageSquare, 
  ArrowRight, 
  Zap, 
  ShieldCheck, 
  BarChart3, 
  Globe,
  Sparkles,
  CheckCircle2
} from 'lucide-react';
import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import resumeImg from "../assets/ResumeAnalyzer.jpg";
import roadmapImg from "../assets/Roadmap.jpg";
import interviewImg from "../assets/Interview.jpg";

const PlatformPage = () => {
const location = useLocation();

useEffect(() => {
  if (location.hash) {
    const element = document.querySelector(location.hash);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  }
}, [location]);

  const fadeIn = {
    initial: { opacity: 0, y: 30 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true },
    transition: { duration: 0.6, ease: "easeOut" }
  };

  const glassStyle = "bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden";
  
  const toolDetails = [
  {
    id: "resume",
    title: "Resume Analyzer",
    subtitle: "Optimize for the modern ATS landscape",
    description:
      "Our neural network scans your resume against thousands of job descriptions in real-time. It doesn't just check for keywords; it analyzes semantic relevance and quantifies your impact to ensure you pass through automated filters with a top-tier score.",
    features: [
      "ATS Compatibility Score",
      "Keyword Density Mapping",
      "Action-Verb Suggestions"
    ],
    icon: <FileSearch className="text-blue-400" size={24} />,
    image: resumeImg
  },
  {
    id: "roadmap",
    title: "Skill Roadmap",
    subtitle: "Precision-engineered learning paths",
    description:
      "Stop guessing what to learn next. By analyzing your current project history and target roles, our AI constructs a step-by-step curriculum. It identifies high-leverage skills that will most significantly increase your market value.",
    features: [
      "Gap Analysis Technology",
      "Curated Resource Index",
      "Milestone Tracking"
    ],
    icon: <Map className="text-purple-400" size={24} />,
    image: roadmapImg
  },
  {
    id: "interview",
    title: "Interview Simulator",
    subtitle: "Master the high-pressure environment",
    description:
      "Engage in voice-to-voice or text-based technical rounds. The AI interviewer adapts its difficulty based on your performance and provides detailed feedback.",
    features: [
      "Behavioral & Technical Modes",
      "Sentiment Analysis",
      "Instant Response Feedback"
    ],
    icon: <MessageSquare className="text-cyan-400" size={24} />,
    image: interviewImg
  }
];

  return (
    <div className="bg-[#050b14] text-white min-h-screen font-sans selection:bg-blue-500/30 overflow-x-hidden">
      
      <section className="relative pt-24 pb-16 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              The <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-white to-purple-400">Elevate AI</span> Platform
            </h1>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed mb-4">
              Advanced career intelligence tools designed to help developers navigate the 
              professional landscape through merit-based data and verified skill growth.
            </p>
          </motion.div>
        </div>
      </section>

      <div className="space-y-32 pb-32">
        {toolDetails.map((tool, idx) => (
          <section id={tool.id} key={tool.id} className="px-6">
            <div className={`max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center ${idx % 1 === 0 ? '' : 'lg:flex-row-reverse'}`}>
              
              <motion.div 
                {...fadeIn}
                className={idx % 2 !== 0 ? "lg:order-last" : ""}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-white/5 border border-white/10">
                    {tool.icon}
                  </div>
                  <span className="text-blue-400 font-semibold tracking-wide uppercase text-sm">{tool.subtitle}</span>
                </div>
                <h2 className="text-3xl md:text-4xl font-bold mb-6 italic">{tool.title}</h2>
                <p className="text-slate-400 text-lg leading-relaxed mb-8">
                  {tool.description}
                </p>
                
                <ul className="space-y-4 mb-8">
                  {tool.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-3 text-slate-300">
                      <CheckCircle2 size={18} className="text-blue-500" />
                      <span className="font-medium">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button className="px-6 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all flex items-center gap-2 font-bold group">
                  Learn More <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </button>
              </motion.div>

             <motion.div {...fadeIn} className="relative group">

  <div className="absolute -inset-1 bg-gradient-to-r from-blue-500/20 to-transparent blur-2xl opacity-50 group-hover:opacity-100 transition-opacity" />

  <div className={`${glassStyle} relative overflow-hidden bg-[#02050a] flex items-center justify-center p-2`}>

    <img
      src={tool.image}
      alt={tool.title}
      className="max-w-full h-auto object-contain transition-transform duration-500 group-hover:scale-105"
    />

    <div className="absolute top-4 left-4 flex gap-2">
      <div className="w-2 h-2 rounded-full bg-red-500/30" />
      <div className="w-2 h-2 rounded-full bg-yellow-500/30" />
      <div className="w-2 h-2 rounded-full bg-green-500/30" />
    </div>

  </div>

</motion.div>

            </div>
          </section>
        ))}
      </div>

      <section className="py-24 px-6 bg-white/[0.02] border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div {...fadeIn}>
            <h2 className="text-3xl font-bold mb-6">Unified Career Ecosystem</h2>
            <p className="text-slate-400 leading-relaxed mb-10">
              The Elevate ecosystem is more than just a set of tools; it’s a feedback loop. 
              Your simulated interviews inform your roadmap, and your roadmap builds your 
              resume all synced in one dashboard.
            </p>
            <div className="flex flex-wrap justify-center gap-8">
              <div className="flex items-center gap-2 text-slate-300">
                <Zap size={18} className="text-blue-400" /> <span>Real-time Sync</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <ShieldCheck size={18} className="text-blue-400" /> <span>Recruiter Verified</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <BarChart3 size={18} className="text-blue-400" /> <span>Market Analytics</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

   

    </div>
  );
};

export default PlatformPage;