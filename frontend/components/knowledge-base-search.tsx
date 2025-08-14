"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, BookOpen, X } from "lucide-react";
import { toast } from "sonner";

interface SearchResult {
  chunk_id: string;
  score: number;
  content: string;
  title: string;
  chunk_index: number;
}

interface KnowledgeBaseSearchProps {
  onResultSelect?: (result: SearchResult) => void;
  placeholder?: string;
  className?: string;
}

export function KnowledgeBaseSearch({ 
  onResultSelect, 
  placeholder = "Search knowledge base...",
  className = "" 
}: KnowledgeBaseSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch("/api/knowledge-base/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
          top_k: 5,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data.results);
        setShowResults(true);
      } else {
        toast.error("Search failed");
      }
    } catch (error) {
      toast.error("Error performing search");
    } finally {
      setIsSearching(false);
    }
  };

  const handleResultClick = (result: SearchResult) => {
    if (onResultSelect) {
      onResultSelect(result);
    }
    setShowResults(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className={`relative ${className}`}>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="pl-10"
          />
        </div>
        <Button 
          onClick={handleSearch} 
          disabled={isSearching}
          size="sm"
        >
          <BookOpen className="w-4 h-4 mr-1" />
          {isSearching ? "Searching..." : "Search"}
        </Button>
      </div>

      {showResults && results.length > 0 && (
        <Card className="absolute top-full left-0 right-0 mt-2 z-50 max-h-96 overflow-y-auto">
          <CardHeader className="pb-2">
            <div className="flex justify-between items-center">
              <CardTitle className="text-sm">Search Results</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowResults(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {results.map((result, index) => (
              <div
                key={index}
                className="p-3 border rounded-lg cursor-pointer hover:bg-muted transition-colors"
                onClick={() => handleResultClick(result)}
              >
                <div className="flex justify-between items-start mb-2">
                  <Badge variant="secondary" className="text-xs">
                    {result.title}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {(result.score * 100).toFixed(1)}%
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-1">
                  Chunk {result.chunk_index + 1}
                </p>
                <p className="text-sm line-clamp-3">{result.content}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {showResults && results.length === 0 && query && !isSearching && (
        <Card className="absolute top-full left-0 right-0 mt-2 z-50">
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground text-center">
              No results found for "{query}"
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 