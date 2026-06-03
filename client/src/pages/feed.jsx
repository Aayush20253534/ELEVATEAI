import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { MessageSquare, Heart, Send, Sparkles, TrendingUp } from 'lucide-react';
import Sidebar from '../components/sidebar';
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "https://elevateai-0xxl.onrender.com";

const getPageCache = () => {
  window.__ELEVATEAI_PAGE_CACHE__ = window.__ELEVATEAI_PAGE_CACHE__ || {};
  return window.__ELEVATEAI_PAGE_CACHE__;
};

// Skeleton for loading state
const FeedSkeleton = () => (
  <div className="rounded-2xl p-5 mb-6 bg-white/5 border border-white/10 animate-pulse space-y-3">
    <div className="flex gap-3 items-center">
      <div className="w-10 h-10 rounded-full bg-white/10 flex-shrink-0" />
      <div className="space-y-2 flex-1">
        <div className="h-3 bg-white/10 rounded w-1/4" />
        <div className="h-2 bg-white/10 rounded w-1/6" />
      </div>
    </div>
    <div className="h-3 bg-white/10 rounded w-full" />
    <div className="h-3 bg-white/10 rounded w-4/5" />
    <div className="h-3 bg-white/10 rounded w-2/3" />
  </div>
);

// ─── FeedCard ─────────────────────────────────────────────────────────────────
const FeedCard = React.memo(({ post, setPosts, user }) => {
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments]         = useState([]);
  const [commentText, setCommentText]   = useState("");
  const [showMenu, setShowMenu]         = useState(false);
  const [imgLoaded, setImgLoaded]       = useState(false);

  const handleLike = useCallback(async () => {
    const token = localStorage.getItem("token");
    try {
      const res = await axios.post(`${API}/feed/like/${post.id}`, {}, { headers: { Authorization: `Bearer ${token}` } });
      setPosts(prev => prev.map(p => p.id === post.id ? { ...p, likes: res.data.likes, liked: res.data.liked } : p));
    } catch {}
  }, [post.id, setPosts]);

  const fetchComments = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/feed/comments/${post.id}`);
      setComments(res.data.comments);
    } catch {}
  }, [post.id]);

  const addComment = useCallback(async () => {
    if (!commentText.trim()) return;
    const token = localStorage.getItem("token");
    try {
      await axios.post(`${API}/feed/comment/${post.id}`, { comment: commentText }, { headers: { Authorization: `Bearer ${token}` } });
      setCommentText("");
      fetchComments();
      setPosts(prev => prev.map(p => p.id === post.id ? { ...p, comments: (p.comments || 0) + 1 } : p));
    } catch {}
  }, [commentText, post.id, fetchComments, setPosts]);

  const deletePost = useCallback(async () => {
    if (!window.confirm("Delete this post?")) return;
    setPosts(prev => prev.filter(p => p.id !== post.id));
    setShowMenu(false);
    try {
      await axios.delete(`${API}/feed/post/${post.id}`, { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } });
    } catch {}
  }, [post.id, setPosts]);

  const deleteComment = useCallback(async (commentId) => {
    if (!window.confirm("Delete this comment?")) return;
    try {
      await axios.delete(`${API}/feed/comment/${commentId}`, { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } });
      setComments(prev => prev.filter(c => c.id !== commentId));
      setPosts(prev => prev.map(p => p.id === post.id ? { ...p, comments: Math.max((p.comments || 1) - 1, 0) } : p));
    } catch {}
  }, [post.id, setPosts]);

  useEffect(() => {
    if (showComments) fetchComments();
  }, [showComments, fetchComments]);

  const isOwn = post.author.email === user?.email;

  return (
    <div className={`rounded-2xl p-5 mb-4 border transition-colors ${
      isOwn ? "bg-gradient-to-br from-indigo-600/20 to-cyan-500/10 border-indigo-400/40" : "bg-white/5 border-white/10 hover:border-white/20"
    }`}>
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full overflow-hidden bg-gray-700 flex items-center justify-center text-xl flex-shrink-0">
            {post.author.avatar?.startsWith("/images")
              ? <img src={`${API}${post.author.avatar}`} alt="profile" className="w-full h-full object-cover" loading="lazy" />
              : <span>{post.author.avatar || "👤"}</span>}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h4 className="font-bold text-gray-100">{post.author.name}</h4>
              {post.author.badge && (
                <span className="bg-indigo-500/20 text-indigo-400 text-[10px] px-2 py-0.5 rounded-full border border-indigo-500/30 flex items-center gap-1">
                  <Sparkles size={10} /> {post.author.badge}
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500">{post.author.role || "2h ago"}</p>
          </div>
        </div>

        <div className="relative">
          {isOwn && (
            <button onClick={() => setShowMenu(p => !p)} className="text-gray-500 hover:text-white text-lg leading-none px-1">⋯</button>
          )}
          {showMenu && isOwn && (
            <div className="absolute right-0 mt-2 bg-[#111] border border-white/10 rounded-lg shadow-lg z-10">
              <button onClick={deletePost} className="block w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-white/5">Delete Post</button>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <p className="text-gray-300 mb-4 leading-relaxed">{post.content}</p>

      {post.image && (
        <div className={`rounded-xl overflow-hidden mb-4 border border-white/10 transition-opacity ${imgLoaded ? "opacity-100" : "opacity-0"}`}>
          <img src={`${API}${post.image}`} loading="lazy" className="w-full object-cover" onLoad={() => setImgLoaded(true)} />
        </div>
      )}

      {post.progress && (
        <div className="mb-4 bg-white/5 h-2 rounded-full overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-500 to-cyan-400 h-full" style={{ width: `${post.progress}%` }} />
        </div>
      )}

      {post.insight && (
        <div className="bg-indigo-500/10 border-l-2 border-indigo-500 p-3 rounded-r-lg mb-4 italic text-sm text-indigo-200">"{post.insight}"</div>
      )}

      {post.tags?.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {post.tags.map(tag => <span key={tag} className="text-xs text-indigo-400 font-mono">{tag}</span>)}
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-between items-center pt-4 border-t border-white/5 text-gray-500">
        <div className="flex space-x-6">
          <button onClick={handleLike} className="flex items-center space-x-2 hover:text-rose-400 transition-colors">
            <Heart size={18} fill={post.liked ? "currentColor" : "none"} className={post.liked ? "text-rose-400" : ""} />
            <span className="text-xs">{post.likes || 0}</span>
          </button>
          <button onClick={() => setShowComments(p => !p)} className="flex items-center space-x-2 hover:text-indigo-400 transition-colors">
            <MessageSquare size={18} /> <span className="text-xs">{post.comments || 0}</span>
          </button>
        </div>
      </div>

      {/* Comments */}
      {showComments && (
        <div className="mt-4 space-y-3">
          <div className="flex gap-2">
            <input
              value={commentText} onChange={(e) => setCommentText(e.target.value)}
              placeholder="Write a comment..."
              className="flex-1 bg-white/5 px-3 py-2 rounded-lg text-sm outline-none"
              onKeyDown={(e) => e.key === "Enter" && addComment()}
            />
            <button onClick={addComment} className="text-indigo-400 text-sm px-2">Post</button>
          </div>
          {comments.map(c => (
            <div key={c.id} className="flex justify-between items-center text-sm text-gray-300 bg-white/5 p-2 rounded-lg">
              <div><b>{c.name}</b>: {c.comment}</div>
              {c.user_email === user?.email && (
                <button onClick={() => deleteComment(c.id)} className="text-red-400 text-xs hover:underline ml-2 flex-shrink-0">Delete</button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
});
FeedCard.displayName = "FeedCard";

// ─── Main ─────────────────────────────────────────────────────────────────────
export default function ElevateFeed() {
  const [posts, setPosts]             = useState([]);
  const [loadingFeed, setLoadingFeed] = useState(true);
  const [hasMore, setHasMore]         = useState(true);
  const [offset, setOffset]           = useState(0);
  const [user, setUser]               = useState(null);
  const [newPost, setNewPost]         = useState("");
  const [selectedImage, setSelectedImage] = useState(null);
  const fileInputRef = useRef(null);

  const FEED_LIMIT = 30;

  // Seed user from localStorage immediately
  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem("user") || "null");
      if (stored) setUser(stored);
    } catch {}
  }, []);

  const fetchFeed = useCallback(async (nextOffset = 0, append = false, force = false) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const cache = getPageCache();
    const cacheKey = `feed:${nextOffset}:${FEED_LIMIT}`;

    if (!force && !append && cache[cacheKey]) {
      const cached = cache[cacheKey];
      setPosts(cached.posts || []);
      setHasMore(Boolean(cached.hasMore));
      setOffset(cached.offset || 0);
      setLoadingFeed(false);
      return;
    }

    if (!append) setLoadingFeed(true);
    try {
      const res = await axios.get(`${API}/feed?limit=${FEED_LIMIT}&offset=${nextOffset}`, { headers: { Authorization: `Bearer ${token}` } });
      const newPosts = res.data.posts || [];
      const nextPosts = append ? [...posts, ...newPosts] : newPosts;
      const nextOffsetVal = nextOffset + newPosts.length;

      setPosts(nextPosts);
      setHasMore(Boolean(res.data.hasMore));
      setOffset(nextOffsetVal);

      if (!append) cache[cacheKey] = { posts: nextPosts, hasMore: res.data.hasMore, offset: nextOffsetVal };
    } catch {}
    finally { setLoadingFeed(false); }
  }, [posts]);

  // Fetch user & feed in parallel
  useEffect(() => {
    const token = localStorage.getItem("token");
    const cache = getPageCache();

    // Fetch /me only if not cached
    if (!cache[`feed:user:${token}`]) {
      axios.get(`${API}/me`, { headers: { Authorization: `Bearer ${token}` } })
        .then(res => { cache[`feed:user:${token}`] = res.data; setUser(res.data); })
        .catch(() => {});
    } else {
      setUser(cache[`feed:user:${token}`]);
    }

    fetchFeed(0, false);
  }, []); // eslint-disable-line

  const createPost = useCallback(async () => {
    if (!newPost.trim() && !selectedImage) return;
    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("content", newPost);
    formData.append("tags", JSON.stringify([]));
    if (selectedImage) formData.append("file", selectedImage);

    try {
      await axios.post(`${API}/feed/create`, formData, {
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" }
      });
      setNewPost("");
      setSelectedImage(null);
      // Invalidate cache and refetch
      const cache = getPageCache();
      delete cache[`feed:0:${FEED_LIMIT}`];
      await fetchFeed(0, false, true);
    } catch {}
  }, [newPost, selectedImage, fetchFeed]);

  const loadMore = useCallback(() => {
    if (!hasMore || loadingFeed) return;
    fetchFeed(offset, true);
  }, [hasMore, loadingFeed, offset, fetchFeed]);

  return (
    <div className="min-h-screen bg-[#09090b] text-gray-200 flex font-sans selection:bg-indigo-500/30">
      <Sidebar />
      <main style={{ marginLeft: "var(--sidebar-width)" }} className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto max-w-[1400px] mx-auto w-full px-6 md:px-10 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <section className="lg:col-span-8 lg:col-start-3 space-y-4">

              {/* Create post */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4 backdrop-blur-xl">
                <div className="flex items-center space-x-4 mb-4">
                  <div className="w-10 h-10 rounded-full overflow-hidden bg-gray-700 flex-shrink-0">
                    {user?.profile_image
                      ? <img src={`${API}${user.profile_image}`} alt="profile" className="w-full h-full object-cover" />
                      : <div className="w-full h-full flex items-center justify-center text-sm">👤</div>}
                  </div>
                  <input
                    type="text" value={newPost} onChange={(e) => setNewPost(e.target.value)}
                    placeholder="Share your progress..."
                    className="bg-transparent w-full focus:outline-none text-gray-100"
                    onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && createPost()}
                  />
                  <button onClick={() => fileInputRef.current.click()}
                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition text-gray-300 flex-shrink-0">
                    📎
                  </button>
                  <input ref={fileInputRef} type="file" accept="image/*"
                    onChange={(e) => setSelectedImage(e.target.files[0])} className="hidden" />
                </div>

                {selectedImage && (
                  <div className="relative w-32 mb-2">
                    <img src={URL.createObjectURL(selectedImage)} className="rounded-lg" />
                    <button onClick={() => setSelectedImage(null)} className="absolute top-1 right-1 bg-black/60 rounded-full p-0.5 text-white text-xs">✕</button>
                  </div>
                )}

                <div className="flex justify-between items-center pt-2 border-t border-white/5">
                  <button onClick={createPost}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-sm font-medium flex items-center gap-2 transition-all">
                    <Send size={16} /> Post
                  </button>
                </div>
              </div>

              {/* Feed */}
              {loadingFeed && posts.length === 0
                ? [...Array(3)].map((_, i) => <FeedSkeleton key={i} />)
                : posts.map(post => (
                    <FeedCard key={post.id} post={post} setPosts={setPosts} user={user} />
                  ))
              }

              {hasMore && !loadingFeed && (
                <div className="py-4 text-center">
                  <button onClick={loadMore}
                    className="text-indigo-400 text-sm font-medium hover:underline flex items-center justify-center gap-2 mx-auto">
                    Load more activity <TrendingUp size={14} />
                  </button>
                </div>
              )}
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}