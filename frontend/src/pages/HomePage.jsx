import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Sparkles, TrendingUp, Clock, Eye, ThumbsUp, ExternalLink, Loader2, History, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import axios from "axios";


const API = "http://127.0.0.1:8000/api";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [apiStatus, setApiStatus] = useState({ openai: false, youtube: false });

  useEffect(() => {
    fetchSuggestions();
    checkApiHealth();
  }, []);

  const fetchSuggestions = async () => {
    try {
      const response = await axios.get(`${API}/suggestions`);
      setSuggestions(response.data);
    } catch (error) {
      console.error("Failed to fetch suggestions:", error);
      setSuggestions([
        "What is the number one trending song on YouTube right now?",
        "Justin Bieber's first video uploaded on YouTube",
        "Taylor Swift's latest music video",
        "Which artist is growing fastest on YouTube?"
      ]);
    }
  };

  const checkApiHealth = async () => {
    try {
      const response = await axios.get(`${API}/health`);
      setApiStatus({
        openai: response.data.openai_configured,
        youtube: response.data.youtube_configured
      });
    } catch (error) {
      console.error("Health check failed:", error);
    }
  };

  const handleSearch = async (searchQuery = query) => {
    if (!searchQuery.trim()) {
      toast.error("Please enter a search query");
      return;
    }

    setIsLoading(true);
    setShowResults(true);
    setResult(null);

    try {
      const response = await axios.post(`${API}/search`, { query: searchQuery });
      setResult(response.data);
      
      if (!response.data.success) {
        toast.error(response.data.error || "Search failed");
      }
    } catch (error) {
      console.error("Search error:", error);
      const errorMessage = error.response?.data?.detail || "Failed to process your query";
      toast.error(errorMessage);
      setResult({
        success: false,
        error: errorMessage,
        query: searchQuery
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    handleSearch(suggestion);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !isLoading) {
      handleSearch();
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] mesh-gradient">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-4 flex items-center justify-between">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">TubeSight AI</h1>
              <p className="text-xs text-zinc-500">YouTube Analytics Search</p>
            </div>
          </motion.div>
          
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${apiStatus.youtube && apiStatus.openai ? 'bg-emerald-500' : 'bg-amber-500'}`} />
            <span className="text-xs text-zinc-500">
              {apiStatus.youtube && apiStatus.openai ? 'Connected' : 'API Keys Required'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-24 pb-12 px-4 md:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Hero Section */}
          <AnimatePresence mode="wait">
            {!showResults && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="text-center mb-12 pt-16"
              >
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.1 }}
                  className="mb-6"
                >
                  <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-zinc-400">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    AI-Powered YouTube Intelligence
                  </span>
                </motion.div>
                
                <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
                  Ask anything about{" "}
                  <span className="gradient-text">YouTube</span>
                </h2>
                
                <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
                  Get instant insights about trending videos, channel statistics, and video history using natural language queries.
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Search Box */}
          <motion.div
            layout
            className={`relative ${showResults ? 'mb-8' : 'mb-12'}`}
          >
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-2xl blur-xl opacity-50" />
              <div className="relative glass rounded-2xl p-2">
                <div className="flex items-center gap-3">
                  <div className="pl-4">
                    <Search className="w-6 h-6 text-zinc-500" />
                  </div>
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about YouTube videos, channels, or trends..."
                    className="search-input flex-1 bg-transparent text-white text-lg placeholder:text-zinc-600 py-4 pr-4 focus:outline-none"
                    disabled={isLoading}
                    data-testid="search-input"
                  />
                  <Button
                    onClick={() => handleSearch()}
                    disabled={isLoading || !query.trim()}
                    className="bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-400 hover:to-cyan-500 text-black font-semibold px-6 py-6 rounded-xl transition-all duration-300 hover:shadow-[0_0_20px_rgba(6,182,212,0.5)] disabled:opacity-50"
                    data-testid="search-button"
                  >
                    {isLoading ? (
                      <Loader2 className="w-5 h-5 spinner" />
                    ) : (
                      <span className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5" />
                        Search
                      </span>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Suggestions */}
          <AnimatePresence>
            {!showResults && suggestions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mb-12"
              >
                <p className="text-sm text-zinc-500 mb-4 text-center">Try asking:</p>
                <div className="flex flex-wrap justify-center gap-3">
                  {suggestions.slice(0, 4).map((suggestion, index) => (
                    <motion.button
                      key={index}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.1 }}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="suggestion-chip px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-zinc-300 hover:bg-white/10 hover:border-cyan-500/30"
                      data-testid={`suggestion-${index}`}
                    >
                      {suggestion}
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Results Section */}
          <AnimatePresence>
            {showResults && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Back to Search */}
                <button
                  onClick={() => {
                    setShowResults(false);
                    setResult(null);
                    setQuery("");
                  }}
                  className="text-sm text-zinc-500 hover:text-cyan-400 flex items-center gap-2 transition-colors"
                  data-testid="back-button"
                >
                  <History className="w-4 h-4" />
                  New Search
                </button>

                {/* Loading State */}
                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="space-y-6"
                  >
                    <div className="glass rounded-2xl p-8">
                      <div className="flex items-center gap-4 mb-6">
                        <div className="w-12 h-12 rounded-xl bg-cyan-500/20 flex items-center justify-center">
                          <Loader2 className="w-6 h-6 text-cyan-400 spinner" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-white">Processing your query...</h3>
                          <p className="text-sm text-zinc-500">AI is analyzing your request</p>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div className="h-4 skeleton rounded-lg w-3/4" />
                        <div className="h-4 skeleton rounded-lg w-full" />
                        <div className="h-4 skeleton rounded-lg w-2/3" />
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* Results */}
                {!isLoading && result && (
                  <>
                    {/* AI Insight Card */}
                    {result.insight && (
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="insight-card glass rounded-2xl p-8 border border-cyan-500/30"
                        data-testid="insight-card"
                      >
                        <div className="flex items-start gap-4 mb-6">
                          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                            <Sparkles className="w-6 h-6 text-white" />
                          </div>
                          <div>
                            <h3 className="text-lg font-semibold text-white mb-1">AI Insight</h3>
                            <p className="text-sm text-zinc-500">
                              Query: "{result.query}" | Tool: {result.tool_used || 'search'}
                            </p>
                          </div>
                        </div>
                        <p className="text-zinc-200 leading-relaxed text-lg" data-testid="insight-text">
                          {result.insight}
                        </p>
                      </motion.div>
                    )}

                    {/* Error State */}
                    {!result.success && result.error && (
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="glass rounded-2xl p-8 border border-red-500/30"
                        data-testid="error-card"
                      >
                        <p className="text-red-400">{result.error}</p>
                      </motion.div>
                    )}

                    {/* Video Results */}
                    {result.success && result.data && (
                      <VideoResults data={result.data} />
                    )}
                  </>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 py-4 px-4 text-center">
        <p className="text-xs text-zinc-600">
          Powered by YouTube Data API & OpenAI GPT-4o-mini
        </p>
      </footer>
    </div>
  );
}

// Video Results Component
const VideoResults = ({ data }) => {
  // Handle different data types
  const videos = data.videos || (data.video ? [data.video] : []);
  const channel = data.channel;
  const channels = data.channels;

  return (
    <div className="space-y-6">
      {/* Channel Info */}
      {channel && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-6"
          data-testid="channel-card"
        >
          <div className="flex items-center gap-4">
            {channel.thumbnail_url && (
              <img
                src={channel.thumbnail_url}
                alt={channel.channel_title}
                className="w-16 h-16 rounded-full object-cover"
              />
            )}
            <div>
              <h3 className="text-xl font-bold text-white">{channel.channel_title}</h3>
              <div className="flex items-center gap-4 mt-2">
                <span className="text-sm text-zinc-400">
                  {channel.subscriber_count_formatted} subscribers
                </span>
                <span className="text-sm text-zinc-400">
                  {channel.video_count} videos
                </span>
                <span className="text-sm text-zinc-400">
                  {channel.view_count_formatted} total views
                </span>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Channel Comparison */}
      {channels && channels.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-6"
          data-testid="channels-comparison"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            Top Channels Comparison
          </h3>
          <div className="space-y-3">
            {channels.map((ch, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-xl bg-white/5"
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-cyan-400">#{index + 1}</span>
                  <span className="text-white">{ch.name}</span>
                </div>
                <div className="flex items-center gap-4 text-sm text-zinc-400">
                  <span>{ch.subscribers_formatted} subs</span>
                  <span>{ch.total_views_formatted} views</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Videos Grid */}
      {videos.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            {data.type === 'trending' ? 'Trending Videos' : 
             data.type === 'first_video' ? 'First Video' :
             data.type === 'latest_video' ? 'Latest Video' : 'Search Results'}
            <span className="text-sm text-zinc-500 font-normal">({videos.length} videos)</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {videos.map((video, index) => (
              <VideoCard key={video.video_id || index} video={video} index={index} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Video Card Component
const VideoCard = ({ video, index }) => {
  return (
    <motion.a
      href={video.url}
      target="_blank"
      rel="noopener noreferrer"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="video-card result-card glass rounded-xl overflow-hidden hover:border-cyan-500/50 group block"
      data-testid={`video-card-${index}`}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-zinc-900">
        {video.thumbnail_url ? (
          <img
            src={video.thumbnail_url}
            alt={video.title}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Eye className="w-12 h-12 text-zinc-700" />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
        <div className="absolute bottom-3 left-3 right-3">
          <h4 className="text-white font-semibold text-sm line-clamp-2 group-hover:text-cyan-400 transition-colors">
            {video.title}
          </h4>
        </div>
        <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
          <ExternalLink className="w-5 h-5 text-white" />
        </div>
      </div>

      {/* Stats */}
      <div className="p-4">
        <p className="text-sm text-zinc-400 mb-3">{video.channel_title}</p>
        <div className="flex items-center gap-4 text-xs text-zinc-500">
          <span className="flex items-center gap-1">
            <Eye className="w-3.5 h-3.5" />
            {video.view_count_formatted}
          </span>
          <span className="flex items-center gap-1">
            <ThumbsUp className="w-3.5 h-3.5" />
            {video.like_count_formatted}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {video.formatted_date}
          </span>
        </div>
      </div>
    </motion.a>
  );
};
