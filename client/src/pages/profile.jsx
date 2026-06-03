import React, { useState, useRef, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  User, Mail, Phone, MapPin, Camera, Edit2, Check, X,
  Linkedin, Globe, Code, Shield,
  Lock, Briefcase, Target, UploadCloud, Sparkles,
  Plus, Trash2
} from 'lucide-react';
import Sidebar from '../components/sidebar';
import axios from "axios";
import { useParams } from "react-router-dom";

const API = import.meta.env.VITE_API_URL || "https://elevateai-0xxl.onrender.com";

// ─── Cache ────────────────────────────────────────────────────────────────────
const getPageCache = () => {
  window.__ELEVATEAI_PAGE_CACHE__ = window.__ELEVATEAI_PAGE_CACHE__ || {};
  return window.__ELEVATEAI_PAGE_CACHE__;
};

// ─── Static sub-components (no motion on every render) ───────────────────────
const GlassCard = ({ children, className = "" }) => (
  <div className={`bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 shadow-xl ${className}`}>
    {children}
  </div>
);

const SectionHeader = ({ icon: Icon, title }) => (
  <div className="flex items-center gap-3 mb-6">
    <div className="p-2 bg-blue-500/20 rounded-lg">
      <Icon className="w-5 h-5 text-blue-400" />
    </div>
    <h3 className="text-xl font-semibold text-white/90">{title}</h3>
  </div>
);

const EditableInput = ({ label, value, setValue, icon: Icon, type = "text", disabled = false }) => {
  const [isEditing, setIsEditing] = useState(false);
  return (
    <div className="group relative mb-4">
      <label className="text-xs font-medium text-gray-400 mb-1.5 block ml-1">{label}</label>
      <div className="relative flex items-center">
        <div className="absolute left-3 text-gray-500"><Icon size={16} /></div>
        <input
          disabled={!isEditing || disabled}
          value={value ?? ""}
          onChange={(e) => {
            if (type === "tel") setValue(e.target.value.replace(/\D/g, ""));
            else setValue(e.target.value);
          }}
          type={type}
          className={`w-full bg-black/20 border ${isEditing ? 'border-blue-500/50' : 'border-white/5'} rounded-xl py-2.5 pl-10 pr-12 text-gray-200 disabled:opacity-50 transition-colors`}
        />
        {!disabled && (
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="absolute right-2 p-1.5 hover:bg-white/10 rounded-lg text-gray-400"
          >
            {isEditing ? <Check size={16} className="text-green-400" /> : <Edit2 size={14} />}
          </button>
        )}
      </div>
    </div>
  );
};

// Skeleton for loading state
const SkeletonCard = () => (
  <div className="bg-white/5 border border-white/10 rounded-2xl p-6 animate-pulse space-y-3">
    <div className="h-4 bg-white/10 rounded w-1/3" />
    <div className="h-3 bg-white/10 rounded w-full" />
    <div className="h-3 bg-white/10 rounded w-4/5" />
  </div>
);

const StatsPanel = ({ projects, skills, certifications, modulesCompleted }) => {
  const stats = [
    { label: "Projects Built", value: projects?.length ?? 0, border: "border-l-amber-500" },
    { label: "Modules Completed", value: modulesCompleted ?? 0, border: "border-l-purple-500" },
    { label: "Skills Mastered", value: skills?.length ?? 0, border: "border-l-emerald-500" },
    { label: "Certifications", value: certifications?.length ?? 0, border: "border-l-pink-500" },
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {stats.map((s, i) => (
        <div key={i} className={`bg-white/5 border border-white/10 rounded-2xl p-5 border-l-4 ${s.border} flex flex-col items-center justify-center text-center`}>
          <span className="text-2xl font-black text-white">{s.value}</span>
          <span className="text-[10px] text-gray-500 uppercase font-bold tracking-widest mt-1">{s.label}</span>
        </div>
      ))}
    </div>
  );
};

const ProfessionalLinks = ({ links, setLinks, linkedin, setLinkedin, isOwnProfile }) => {
  const [editing, setEditing] = useState({ linkedin: false, portfolio: false });

  const updateLink = (platform, value) => {
    setLinks(prev => {
      const idx = prev.findIndex(l => l.platform === platform);
      if (idx !== -1) { const u = [...prev]; u[idx] = { ...u[idx], url: value }; return u; }
      return [...prev, { platform, url: value }];
    });
  };

  const getUrl = (platform) => links.find(l => l.platform === platform)?.url ?? "";

  return (
    <GlassCard>
      <SectionHeader icon={Globe} title="Professional Links" />
      <div className="space-y-4">
        {/* LinkedIn */}
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-blue-400"><Linkedin size={16} /></div>
          <input
            disabled={!editing.linkedin || !isOwnProfile}
            value={linkedin ?? ""}
            onChange={(e) => setLinkedin(e.target.value)}
            placeholder="LinkedIn Profile URL"
            className={`w-full bg-black/20 border ${editing.linkedin ? "border-blue-500/50" : "border-white/5"} rounded-xl py-2.5 pl-10 pr-12 text-gray-300 disabled:opacity-60`}
          />
          {isOwnProfile && (
            <button onClick={() => setEditing(p => ({ ...p, linkedin: !p.linkedin }))}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 hover:bg-white/10 rounded-lg text-gray-400">
              {editing.linkedin ? <Check size={16} className="text-green-400" /> : <Edit2 size={14} />}
            </button>
          )}
        </div>
        {/* Portfolio */}
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-purple-400"><Globe size={16} /></div>
          <input
            disabled={!editing.portfolio || !isOwnProfile}
            value={getUrl("portfolio")}
            onChange={(e) => updateLink("portfolio", e.target.value)}
            placeholder="Portfolio Website URL"
            className={`w-full bg-black/20 border ${editing.portfolio ? "border-blue-500/50" : "border-white/5"} rounded-xl py-2.5 pl-10 pr-12 text-gray-300 disabled:opacity-60`}
          />
          {isOwnProfile && (
            <button onClick={() => setEditing(p => ({ ...p, portfolio: !p.portfolio }))}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 hover:bg-white/10 rounded-lg text-gray-400">
              {editing.portfolio ? <Check size={16} className="text-green-400" /> : <Edit2 size={14} />}
            </button>
          )}
        </div>
      </div>
    </GlassCard>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
const ProfilePage = () => {
  const { id } = useParams();
  // Seed from localStorage immediately — zero blank flash
  const storedUser = (() => {
    try { return JSON.parse(localStorage.getItem("user") || "null"); } catch { return null; }
  })();
  const currentUser = storedUser;
  const isOwnProfile = !id || String(currentUser?.id) === String(id);

  const [loading, setLoading] = useState(true);
  const [user, setUser]         = useState(null);
  const [image, setImage]       = useState(null);
  const [coverImage, setCoverImage] = useState(null);
  const [resume, setResume]     = useState(null);
  const [name, setName]         = useState("");
  const [username, setUsername] = useState("");
  const [phone, setPhone]       = useState("");
  const [bio, setBio]           = useState("");
  const [current_role, setCurrentRole] = useState("");
  const [target_role, setTargetRole]   = useState("");
  const [links, setLinks]       = useState([]);
  const [linkedin, setLinkedin] = useState("");
  const [showSuccess, setShowSuccess] = useState(false);
  const [saving, setSaving]     = useState(false);

  const profileInputRef = useRef(null);
  const coverInputRef   = useRef(null);
  const resumeInputRef  = useRef(null);

  const loadUser = useCallback((data) => {
    setUser(data);
    setName(data.name ?? "");
    setUsername(data.username ?? "");
    setPhone(data.phone ?? "");
    setBio(data.bio ?? "");
    setCurrentRole(data.current_role ?? "");
    setTargetRole(data.target_role ?? "");
    setLinks(Array.isArray(data.professional_links) ? data.professional_links : []);
    setLinkedin(data.linkedin ?? "");
    setImage(data.profile_image ?? null);
    setCoverImage(data.cover_image ?? null);
    setResume(data.resume ?? null);
    setLoading(false);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const cache = getPageCache();
    const cacheKey = id ? `profile:${id}` : "profile:me";

    // 1. Serve from cache instantly
    if (cache[cacheKey]) {
      loadUser(cache[cacheKey]);
      return;
    }

    // 2. For own profile, seed from localStorage immediately so UI isn't blank
    if (!id && storedUser) {
      loadUser({ ...storedUser, professional_links: [] });
    }

    // 3. Fetch full data in background
    const url = id ? `${API}/user/${id}` : `${API}/me`;
    axios.get(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(res => {
        cache[cacheKey] = res.data;
        loadUser(res.data);
      })
      .catch(err => {
        console.error("Profile fetch error:", err);
        setLoading(false);
      });
  }, [id, loadUser]); // eslint-disable-line

  const saveProfile = async () => {
    const token = localStorage.getItem("token");
    setSaving(true);
    try {
      await axios.post(`${API}/profile/update`, {
        name, username, phone, bio, current_role, target_role, linkedin, professional_links: links
      }, { headers: { Authorization: `Bearer ${token}` } });

      const cache = getPageCache();
      const updated = { ...(cache["profile:me"] || user || {}), name, username, phone, bio, current_role, target_role, linkedin, professional_links: links };
      cache["profile:me"] = updated;
      loadUser(updated);
      localStorage.setItem("user", JSON.stringify({ ...(storedUser || {}), name, username }));

      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    const current_password = prompt("Enter current password");
    const new_password = prompt("Enter new password");
    const confirm_password = prompt("Confirm new password");
    if (!current_password || !new_password || !confirm_password) return;
    if (new_password !== confirm_password) { alert("Passwords do not match"); return; }
    if (new_password.length < 6) { alert("Password must be at least 6 characters"); return; }
    try {
      await axios.post(`${API}/change-password`, { current_password, new_password },
        { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } });
      alert("Password updated successfully");
    } catch (err) {
      alert(err.response?.data?.detail || "Error updating password");
    }
  };

  const uploadFile = async (file, endpoint, setter) => {
    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post(`${API}${endpoint}`, formData, {
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" }
      });
      const dataKey = Object.keys(res.data)[0];
      setter(res.data[dataKey]);
    } catch (err) {
      console.error(`Upload to ${endpoint} failed`, err);
    }
  };

  const handleFileChange = (e, type) => {
    const file = e.target.files[0];
    if (!file) return;
    if (type === "profile") uploadFile(file, "/profile/upload-image", setImage);
    if (type === "cover")   uploadFile(file, "/profile/upload-cover", setCoverImage);
    if (type === "resume")  uploadFile(file, "/profile/upload-resume", setResume);
  };

  // Show skeleton only if nothing is available yet (cache miss AND no localStorage)
  if (loading && !user) {
    return (
      <div className="min-h-screen bg-[#050b14] text-gray-300">
        <Sidebar />
        <main style={{ marginLeft: "var(--sidebar-width)" }} className="p-8">
          <div className="max-w-6xl mx-auto space-y-6 pt-4">
            <div className="h-48 bg-white/5 rounded-3xl animate-pulse" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
            </div>
            <SkeletonCard />
            <SkeletonCard />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050b14] text-gray-300 selection:bg-blue-500/30">
      <Sidebar />

      <main style={{ marginLeft: "var(--sidebar-width)" }} className="flex-1 flex flex-col overflow-y-auto p-4 md:p-8">
        <div className="max-w-6xl mx-auto pt-4 pb-20 w-full">

          {/* Cover + Avatar */}
          <div className="relative mb-8">
            <div className="group relative h-48 w-full rounded-3xl border border-white/10 overflow-hidden bg-gradient-to-r from-blue-900/40 via-purple-900/40 to-black">
              {coverImage && <img src={`${API}${coverImage}`} alt="Cover" className="w-full h-full object-cover" />}
              {isOwnProfile && (
                <>
                  <button onClick={() => coverInputRef.current?.click()}
                    className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-black/50 hover:bg-black/70 backdrop-blur-md rounded-lg text-xs font-medium text-white opacity-0 group-hover:opacity-100 transition-all border border-white/10">
                    <Camera size={14} /> Change Cover
                  </button>
                  <input ref={coverInputRef} type="file" className="hidden" onChange={(e) => handleFileChange(e, "cover")} accept="image/*" />
                </>
              )}
            </div>

            <div className="absolute -bottom-16 left-8 flex items-end gap-6">
              <div className="relative group">
                <div className="w-32 h-32 rounded-3xl overflow-hidden border-4 border-[#050b14] shadow-2xl bg-gray-800 flex items-center justify-center">
                  {image
                    ? <img src={`${API}${image}`} className="w-full h-full object-cover" loading="lazy" />
                    : <span className="text-3xl font-bold text-gray-400">{username?.charAt(0)?.toUpperCase() || "U"}</span>
                  }
                </div>
                {isOwnProfile && (
                  <>
                    <button onClick={() => profileInputRef.current?.click()}
                      className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity rounded-3xl">
                      <Camera className="text-white" />
                    </button>
                    <input ref={profileInputRef} type="file" className="hidden" onChange={(e) => handleFileChange(e, "profile")} accept="image/*" />
                  </>
                )}
              </div>

              <div className="mb-4">
                <h1 className="text-3xl font-bold text-white mb-2">{username || name || "—"}</h1>
                <div className="inline-flex flex-col gap-2 p-4 rounded-2xl bg-[#0f172a] border border-blue-500/40 shadow-xl">
                  <p className="text-blue-400 font-bold text-sm flex items-center gap-2">
                    <Code size={14} /> {current_role || "Professional"}
                  </p>
                  <div className="flex gap-3 text-[11px] font-bold tracking-wide uppercase">
                    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-green-500/10 text-green-400 border border-green-500/20">
                      <Check size={12} strokeWidth={3} /> Account Verified
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-28 grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* LEFT */}
            <div className="lg:col-span-8 space-y-6">
              <StatsPanel
                projects={user?.projects}
                skills={user?.skills}
                certifications={user?.certifications}
                modulesCompleted={user?.modules_completed}
              />

              <GlassCard>
                <SectionHeader icon={User} title="Personal Information" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
                  <EditableInput label="Full Name" value={name} setValue={setName} icon={User} disabled={!isOwnProfile} />
                  <EditableInput label="Username" value={username} setValue={setUsername} icon={User} disabled={!isOwnProfile} />
                  <EditableInput label="Email Address" value={user?.email ?? ""} icon={Mail} type="email" disabled />
                  <EditableInput label="Phone Number" value={phone} setValue={setPhone} icon={Phone} type="tel" disabled={!isOwnProfile} />
                </div>
                <div className="mt-2">
                  <label className="text-xs font-medium text-gray-400 mb-1.5 block ml-1">Bio / About Me</label>
                  <textarea
                    value={bio}
                    disabled={!isOwnProfile}
                    onChange={(e) => setBio(e.target.value)}
                    className="w-full bg-black/20 border border-white/5 rounded-xl p-3 text-gray-200 min-h-[100px] focus:border-blue-500/40 outline-none transition-colors"
                  />
                </div>
              </GlassCard>

              <GlassCard>
                <SectionHeader icon={Briefcase} title="Career Profile" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 mb-6">
                  <EditableInput label="Current Role" value={current_role} setValue={setCurrentRole} icon={Briefcase} disabled={!isOwnProfile} />
                  <EditableInput label="Target Role" value={target_role} setValue={setTargetRole} icon={Target} disabled={!isOwnProfile} />
                </div>

                <div
                  onClick={() => isOwnProfile && !resume && resumeInputRef.current?.click()}
                  className="p-6 border-2 border-dashed border-white/10 rounded-2xl hover:border-blue-500/30 transition-colors group cursor-pointer text-center"
                >
                  <UploadCloud className="w-8 h-8 mx-auto text-gray-500 group-hover:text-blue-400 mb-3 transition-colors" />
                  {!resume ? (
                    <>
                      <p className="text-sm text-gray-400">Upload your latest Resume</p>
                      <span className="text-blue-400 text-sm">Browse File</span>
                    </>
                  ) : (
                    <div className="flex flex-col items-center gap-2">
                      <p className="text-sm text-green-400 font-semibold">Uploaded: {resume.split("/").pop()}</p>
                      <div className="flex gap-3 mt-2">
                        <a href={`${API}${resume}`} target="_blank" rel="noreferrer"
                          className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded-lg transition">
                          Download
                        </a>
                        <button onClick={(e) => { e.stopPropagation(); setResume(null); resumeInputRef.current.click(); }}
                          className="px-4 py-1.5 bg-white/10 hover:bg-white/20 text-xs rounded-lg transition">
                          Replace
                        </button>
                      </div>
                    </div>
                  )}
                  <input ref={resumeInputRef} type="file" className="hidden" accept=".pdf,.doc,.docx"
                    onChange={(e) => handleFileChange(e, "resume")} />
                </div>
              </GlassCard>
            </div>

            {/* RIGHT */}
            <div className="lg:col-span-4 space-y-6">
              <ProfessionalLinks links={links} setLinks={setLinks} linkedin={linkedin} setLinkedin={setLinkedin} isOwnProfile={isOwnProfile} />

              <GlassCard>
                <SectionHeader icon={Shield} title="Security & Settings" />
                {isOwnProfile && (
                  <button onClick={handleChangePassword}
                    className="w-full flex items-center justify-center gap-2 py-3 bg-white/5 hover:bg-white/10 rounded-xl transition-all border border-white/5 text-sm">
                    <Lock size={16} /> Change Password
                  </button>
                )}
              </GlassCard>
            </div>
          </div>
        </div>
      </main>

      {isOwnProfile && (
        <div className="fixed bottom-8 right-8 z-50">
          <button onClick={saveProfile} disabled={saving}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl text-white font-bold shadow-2xl shadow-blue-500/20 transform hover:scale-105 transition-all active:scale-95 disabled:opacity-60">
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      )}

      <style>{`
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #050b14; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: #334155; }
      `}</style>

      <AnimatePresence>
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 40 }}
            className="fixed bottom-24 right-8 bg-[#0f172a] border border-green-500/30 text-green-400 px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50"
          >
            <Check size={20} className="text-green-400" />
            <div>
              <p className="font-semibold text-sm">Profile Saved</p>
              <p className="text-xs text-gray-400">Your profile has been updated successfully.</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ProfilePage;