import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, Search, MoreVertical, Paperclip, Smile, 
  ChevronLeft, CheckCheck, Check, SearchIcon, Filter, Plus
} from 'lucide-react';
import Sidebar from '../components/sidebar';

const EMOJIS = [
  "😀","😂","🤣","😍","❤️",
  "🔥","👍","👏","😎","💯",
  "😅","🥲","😭","😢","😡",
  "🤔","🤯","🙏","😴","😇"
];

const formatTime = (ts) => {
  if (!ts) return "";

  const safeTs = ts.endsWith("Z") ? ts : ts + "Z";

  return new Date(safeTs).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });
};
const MessageBubble = ({ message, isMe, onDelete, searchQuery }) => {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={`flex w-full mb-2 group ${
        isMe ? "justify-end" : "justify-start"
      }`}
    >
      <div
  className={`relative max-w-[65%] md:max-w-[55%] lg:max-w-[48%] px-4 py-2.5 shadow-sm transition-all duration-200 ${
          isMe
            ? "bg-indigo-600 text-white rounded-2xl rounded-br-sm"
            : "bg-[#1f2937] text-slate-100 rounded-2xl rounded-bl-sm border border-slate-700/50"
        }`}
      >
        {/* 🔥 TOP RIGHT MENU */}
        <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 rounded hover:bg-black/10"
          >
            <MoreVertical size={14} />
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-1 w-28 bg-[#111827] border border-slate-700 rounded-lg shadow-lg z-50">
              <button
                onClick={() => onDelete(message.id, isMe)}
                className="w-full text-left px-3 py-2 text-xs hover:bg-red-500/10 text-red-400"
              >
                Delete
              </button>
            </div>
          )}
        </div>
        {message.message && (
          <p className="text-[14.5px] leading-relaxed whitespace-pre-wrap">
  {searchQuery
    ? message.message?.split(new RegExp(`(${searchQuery})`, "gi")).map((part, i) =>
        part.toLowerCase() === searchQuery.toLowerCase() ? (
          <span key={i} className="bg-yellow-400/40 rounded px-1">
            {part}
          </span>
        ) : (
          part
        )
      )
    : message.message}
</p>
        )}

        {/* 📁 FILE PREVIEW */}
        {message.file_url && (
          <div className="mt-2">
            {message.file_type?.startsWith("image") && (
              <img
                src={
                  message.file_url.startsWith("blob:")
                    ? message.file_url
                    : `http://localhost:8000${message.file_url}`
                }
                className="rounded-lg max-w-[200px]"
              />
            )}

            {message.file_type?.startsWith("video") && (
              <video
                controls
                className="rounded-lg max-w-[220px]"
                src={
                  message.file_url.startsWith("blob:")
                    ? message.file_url
                    : `http://localhost:8000${message.file_url}`
                }
              />
            )}

            {message.file_type?.startsWith("audio") && (
              <audio
                controls
                src={
                  message.file_url.startsWith("blob:")
                    ? message.file_url
                    : `http://localhost:8000${message.file_url}`
                }
              />
            )}

            {!message.file_type?.startsWith("image") &&
              !message.file_type?.startsWith("video") &&
              !message.file_type?.startsWith("audio") && (
               <a
  href={`http://localhost:8000${message.file_url}`}
  target="_blank"
  rel="noreferrer"
  className="flex items-center gap-2 bg-black/20 hover:bg-black/30 transition px-2 py-1 rounded-md text-xs text-blue-300 w-fit max-w-[200px]"
>
  <Paperclip size={12} />
  <span className="truncate">
    {message.file_name || message.file_url.split("/").pop()}
  </span>
</a>
              )}
          </div>
        )}

        <div
          className={`flex items-center justify-end gap-1 mt-1 text-[10px] ${
            isMe ? "text-indigo-200" : "text-slate-500"
          }`}
        >
          <span>{formatTime(message.timestamp)}</span>

          {/* ✔ ticks */}
          {isMe && (
            <CheckCheck
              size={14}
              className="text-emerald-400 opacity-80"
            />
          )}
        </div>
      </div>
    </motion.div>
  );
};


const ContactItem = ({ chat, isActive, onClick, currentUserId }) => (
  <div 
    onClick={onClick}
    className={`flex items-center gap-3 p-3 cursor-pointer transition-all duration-200 border-b border-slate-800/40
      ${isActive ? 'bg-slate-800/60 border-l-4 border-l-blue-500' : 'hover:bg-slate-800/30'}`}
  >
    <div className="relative">
      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center text-white font-semibold border border-slate-700">
        {chat.name?.charAt(0) || '?'}
      </div>
      {chat.online && <div className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-500 border-2 border-[#050b14] rounded-full" />}
    </div>
    <div className="flex-1 min-w-0">
      <div className="flex justify-between items-baseline">
        <h3 className="text-sm font-semibold text-slate-200 truncate">{chat.name}</h3>
        <span className="text-[10px] text-slate-500">12:45 PM</span>
      </div>
      <p className="text-xs text-slate-500 truncate mt-0.5">
  {chat.last_sender_id === currentUserId ? "You: " : ""}
  {chat.last_message || "No messages yet"}
</p>
    </div>
  </div>
);

// --- Main Component ---

export default function ElevateAIChat() {
  const { receiver_id } = useParams();
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();
  const [showSearch, setShowSearch] = useState(false);
  const [showEmoji, setShowEmoji] = useState(false);
  const [inbox, setInbox] = useState([]);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [receiver, setReceiver] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const scrollRef = useRef(null);
  
  const currentUser = JSON.parse(localStorage.getItem("user"));
  const currentUserId = currentUser?.id;
  const token = localStorage.getItem("token");

  useEffect(() => {
  if (!receiver_id || !currentUserId) return;

  if (String(receiver_id) === String(currentUserId)) {
    alert("You can't message yourself 😅");
    navigate("/messages"); 
  }
}, [receiver_id, currentUserId, navigate]);

useEffect(() => {
  const handleClick = () => setShowEmoji(false);
  if (showEmoji) window.addEventListener("click", handleClick);
  return () => window.removeEventListener("click", handleClick);
}, [showEmoji]);

useEffect(() => {
  return () => {
    messages.forEach(msg => {
      if (msg.file_url?.startsWith("blob:")) {
        URL.revokeObjectURL(msg.file_url);
      }
    });
  };
}, [messages]);

  // Fetch Inbox & Auto-refresh
  useEffect(() => {
    const fetchInbox = async () => {
      try {
        const res = await axios.get("http://localhost:8000/messages/inbox", {
          headers: { Authorization: `Bearer ${token}` }
        });
        setInbox(res.data);
      } catch (err) { console.error("Inbox error", err); }
    };
    fetchInbox();
    const inv = setInterval(fetchInbox, 5000);
    return () => clearInterval(inv);
  }, [token]);

  useEffect(() => {
  if (!receiver_id) return;

  const fetchUser = async () => {
    try {
      const res = await axios.get(`http://localhost:8000/user/${receiver_id}`);
      setReceiver(res.data);
    } catch (err) {
      console.error("User fetch error", err);
    }
  };

  fetchUser();
}, [receiver_id]);

  // Fetch Messages
  useEffect(() => {
    if (!receiver_id) return;
    const fetchChat = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/messages/${receiver_id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
setMessages(
  res.data.map(m => ({
    ...m,
    timestamp: m.created_at
  }))
);
      } catch (err) { console.error("Fetch error", err); }
    };
    fetchChat();
    const interval = setInterval(fetchChat, 3000);
    return () => clearInterval(interval);
  }, [receiver_id, token]);

 useEffect(() => {
  if (messages.length > 0) {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }
}, [messages.length]);
const handleDelete = async (id, isMe) => {
  try {
    await axios.delete(`http://localhost:8000/messages/${id}`, {
      params: {
        delete_for_everyone: isMe === true
      },
      headers: { Authorization: `Bearer ${token}` }
    });

    setMessages(prev => prev.filter(m => m.id !== id));
  } catch (err) {
    console.error(err);
  }
};
  const handleSend = async (e) => {
  e.preventDefault();

  // 🚫 prevent empty send
  if (!inputText.trim() && !selectedFile) return;

  // 🚫 invalid file check
  if (selectedFile && selectedFile.size === 0) {
    alert("Invalid file");
    return;
  }

  // 📦 create temp message (instant UI)
  const tempMsg = {
    id: "temp-" + Date.now(),
    sender_id: currentUserId,
    message: inputText,
    file_url: selectedFile ? URL.createObjectURL(selectedFile) : null,
    file_type: selectedFile?.type,
    timestamp: new Date().toISOString(),
  };

  // ⚡ instant UI update
  setMessages((prev) => [...prev, tempMsg]);
  setInputText("");

  const formData = new FormData();
  formData.append("receiver_id", receiver_id);

  // 🧠 only send message if exists
  if (tempMsg.message) {
    formData.append("message", tempMsg.message);
  }

  // 📎 attach file if present
  if (selectedFile) {
    formData.append("file", selectedFile);
  }

  try {
    // 🚀 send message to backend
    await axios.post(
      "http://localhost:8000/messages/send",
      formData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      }
    );

    // 🧼 reset file
    setSelectedFile(null);

    // 🔥 refresh messages instantly (no delay feeling)
    const resChat = await axios.get(
      `http://localhost:8000/messages/${receiver_id}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    setMessages(
      resChat.data.map((m) => ({
        ...m,
        timestamp: m.created_at,
      }))
    );

    // 🔄 refresh inbox
    const resInbox = await axios.get(
      "http://localhost:8000/messages/inbox",
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    setInbox(resInbox.data);

  } catch (err) {
    console.error("Send error", err);
  }
};

const filteredMessages = messages.filter((msg) => {
  if (!searchQuery.trim()) return true;

  const query = searchQuery.toLowerCase();

  return (
    (msg.message || "").toLowerCase().includes(query) ||
    (msg.file_name || "").toLowerCase().includes(query)
  );
});

  return (
    <div className="flex h-screen bg-[#0b141a] text-slate-300 overflow-hidden font-sans">
      <Sidebar />

      {/* Main Container */}
      <div 
        style={{ marginLeft: "var(--sidebar-width)" }} 
        className="flex-1 flex w-full h-full border-l border-slate-800/50"
      >
        
        {/* LEFT COLUMN: Inbox List (Always visible on desktop) */}
        <aside className={`w-full md:w-[350px] lg:w-[400px] flex flex-col border-r border-slate-800/60 bg-[#050b14] ${receiver_id ? 'hidden md:flex' : 'flex'}`}>
          <header className="p-4 flex flex-col gap-4 bg-[#0b141a]">
            <div className="flex justify-between items-center">
              <h1 className="text-xl font-bold text-white">Chats</h1>
              <div className="flex gap-2">
                <button className="p-2 hover:bg-slate-800 rounded-full text-slate-400"><Plus size={20} /></button>
                <button className="p-2 hover:bg-slate-800 rounded-full text-slate-400"><MoreVertical size={20} /></button>
              </div>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
              <input 
  value={searchQuery}
  onChange={(e) => setSearchQuery(e.target.value)}
  placeholder="Search messages..."
                className="w-full bg-[#1f2937] border-none rounded-lg py-2 pl-10 pr-4 text-sm focus:ring-1 focus:ring-blue-500 placeholder:text-slate-500"
              />
            </div>
          </header>

          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {inbox.map(chat => (
              <ContactItem 
                key={chat.user_id} 
                chat={chat} 
                isActive={receiver_id === String(chat.user_id)}
                onClick={() => navigate(`/chat/${chat.user_id}`)}
                currentUserId={currentUserId}
              />
            ))}
          </div>
        </aside>

        {/* RIGHT COLUMN: Chat Window */}
        <main className={`flex-1 flex flex-col bg-[#0b141a] relative ${!receiver_id ? 'hidden md:flex items-center justify-center' : 'flex'}`}>
          {receiver_id ? (
            <>
              {/* Chat Header */}
              <header className="h-16 flex items-center justify-between px-4 bg-[#1f2937]/50 backdrop-blur-md border-b border-slate-800/50 z-30">
                <div className="flex items-center gap-3">
                  <button onClick={() => navigate('/messages')} className="md:hidden p-1 text-slate-400"><ChevronLeft /></button>
                  <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                    {receiver?.name?.charAt(0) || 'U'}
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-white leading-tight">{receiver?.name || `User ${receiver_id}`}</h2>
                    <span className="text-[11px] text-emerald-500 font-medium">online</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
  {showSearch ? (
    <input
      autoFocus
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
      placeholder="Search in chat..."
      className="bg-[#2a3942] px-3 py-1 rounded-md text-sm outline-none text-white"
    />
  ) : (
    <SearchIcon
      size={18}
      className="cursor-pointer text-slate-400 hover:text-white"
      onClick={() => setShowSearch(true)}
    />
  )}

  {showSearch && (
    <button
      onClick={() => {
        setShowSearch(false);
        setSearchQuery("");
      }}
      className="text-xs text-slate-400 hover:text-white"
    >
      ✕
    </button>
  )}

  <MoreVertical size={18} className="cursor-pointer text-slate-400 hover:text-white" />
</div>
              </header>

              {/* Message Area */}
              <div className="flex-1 overflow-y-auto p-4 space-y-1 bg-[#0b141a] bg-[url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png')] bg-blend-soft-light bg-repeat">
                <AnimatePresence initial={false}>
                  {filteredMessages.map((msg) => (
                   <MessageBubble 
  message={msg}
  isMe={msg.sender_id === currentUserId}
  onDelete={handleDelete}
  searchQuery={searchQuery}
/>
                  ))}
                </AnimatePresence>
                <div ref={scrollRef} className="h-2" />
              </div>

              {/* Input Area */}
              <footer className="p-3 bg-[#1f2937]/30 border-t border-slate-800/50">
                <form onSubmit={handleSend} className="max-w-6xl mx-auto flex items-center gap-2">
                    <input
  id="fileInput"
  type="file"
  hidden
  onChange={(e) => setSelectedFile(e.target.files[0])}
/>
                  <div className="flex gap-1 text-slate-400">
                    <div className="relative">
  <button
    type="button"
    onClick={(e) => {
  e.stopPropagation();
  setShowEmoji(prev => !prev);
}}
    className="p-2 hover:text-white"
  >
    <Smile size={24} />
  </button>

  {showEmoji && (
    <div className="absolute bottom-12 left-0 bg-[#111827] border border-slate-700 rounded-lg p-2 flex gap-2 flex-wrap w-[220px] z-50 shadow-lg">
      {EMOJIS.map((emoji, i) => (
        <button
          key={i}
          onClick={() => {
            setInputText(prev => prev + emoji);
            setShowEmoji(false);
          }}
          className="text-lg hover:scale-125 transition"
        >
          {emoji}
        </button>
      ))}
    </div>
  )}
</div>
                    <button 
  type="button" 
  onClick={() => document.getElementById("fileInput").click()}
  className="p-2 hover:text-white"
>
  <Paperclip size={24} />
</button>
                  </div>
                  {selectedFile && (
  <div className="text-xs text-slate-400 px-2">
    📎 {selectedFile.name} 
<span className="text-[10px] text-slate-500 ml-1">
  ({Math.round(selectedFile.size / 1024)} KB)
</span>
  </div>
)}
                  <input 
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Type a message" 
                    className="flex-1 bg-[#2a3942] border-none rounded-xl py-2.5 px-4 text-sm focus:ring-0 text-white placeholder:text-slate-500"
                  />
                  <button 
                    type="submit"
                    disabled={!inputText.trim() && !selectedFile}
                    className="bg-indigo-600 hover:bg-indigo-500 p-2.5 rounded-full text-white transition-transform active:scale-90 disabled:opacity-50"
                  >
                    <Send size={20} />
                  </button>
                </form>
              </footer>
            </>
          ) : (
            <div className="text-center space-y-4">
              <div className="w-24 h-24 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto">
                <Send size={40} className="text-slate-600 -rotate-12" />
              </div>
              <h2 className="text-xl font-light text-slate-400">Select a conversation to start messaging</h2>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}