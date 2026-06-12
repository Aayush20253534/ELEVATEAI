import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "https://elevateai-h83p.onrender.com",
});

export default api;
