"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Search, Plus, Edit, Trash2, Save, X, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { LayoutWrapper } from "@/components/layout-wrapper";
import { apiService, KnowledgeBaseEntry, KnowledgeBaseCreate, SearchResult } from "@/lib/api";

export default function KnowledgeBasePage() {
  const [entries, setEntries] = useState<KnowledgeBaseEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [editingEntry, setEditingEntry] = useState<string | null>(null);
  const [newEntry, setNewEntry] = useState({ title: "", content: "" });
  const [showAddForm, setShowAddForm] = useState(false);
  const [isAddingEntry, setIsAddingEntry] = useState(false);
  const [savingTitle, setSavingTitle] = useState<string | null>(null);
  const [deletingTitle, setDeletingTitle] = useState<string | null>(null);

  // Fetch all knowledge base entries
  const fetchEntries = async () => {
    try {
      const data = await apiService.getKnowledgeBaseEntries();
      setEntries(data);
    } catch (error) {
      toast.error("Error fetching knowledge base entries");
    } finally {
      setIsLoading(false);
    }
  };

  // Search knowledge base
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const data = await apiService.searchKnowledgeBase({
        query: searchQuery,
        top_k: 3,
      });
      setSearchResults(data.results);
    } catch (error) {
      toast.error("Search failed");
    } finally {
      setIsSearching(false);
    }
  };

  // Add new knowledge base entry
  const handleAddEntry = async () => {
    if (!newEntry.title.trim() || !newEntry.content.trim()) {
      toast.error("Please fill in both title and content");
      return;
    }

    setIsAddingEntry(true);
    try {
      const data = await apiService.createKnowledgeBaseEntry(newEntry);
      toast.success("Knowledge base entry added successfully");
      setNewEntry({ title: "", content: "" });
      setShowAddForm(false);
      fetchEntries();
    } catch (error) {
      toast.error("Failed to add knowledge base entry");
    } finally {
      setIsAddingEntry(false);
    }
  };

  // Update existing entry
  const handleUpdateEntry = async (title: string, content: string) => {
    setSavingTitle(title);
    try {
      const data = await apiService.updateKnowledgeBaseEntry(title, content);
      toast.success("Knowledge base entry updated successfully");
      setEditingEntry(null);
      fetchEntries();
    } catch (error) {
      toast.error("Failed to update knowledge base entry");
    } finally {
      setSavingTitle(null);
    }
  };

  // Delete entry
  const handleDeleteEntry = async (title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) {
      return;
    }

    setDeletingTitle(title);
    try {
      console.log("Attempting to delete:", title);
      const encodedTitle = encodeURIComponent(title);
      console.log("Encoded title:", encodedTitle);
      
      await apiService.deleteKnowledgeBaseEntry(title);
      console.log("Delete successful");
      
      toast.success("Knowledge base entry deleted successfully");
      fetchEntries();
    } catch (error) {
      console.error("Delete error:", error);
      toast.error("Error deleting knowledge base entry");
    } finally {
      setDeletingTitle(null);
    }
  };

  // Helper function to format dates safely
  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return "No date";
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return "Invalid date";
      return date.toLocaleDateString();
    } catch (error) {
      return "Invalid date";
    }
  };

  // Get combined content for editing
  const getCombinedContent = (entry: KnowledgeBaseEntry) => {
    return entry.chunks.map(chunk => chunk.content).join("\n\n");
  };

  useEffect(() => {
    fetchEntries();
  }, []);

  useEffect(() => {
    // Intentionally left blank: search now happens only on explicit button click
  }, []);

  if (isLoading) {
    return (
      <LayoutWrapper>
        <div className="container mx-auto p-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-lg">Loading knowledge base...</div>
          </div>
        </div>
      </LayoutWrapper>
    );
  }

  return (
    <LayoutWrapper>
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Knowledge Base</h1>
            <p className="text-muted-foreground">
              Manage your clinic's knowledge base for AI-powered responses
            </p>
          </div>
          <Button onClick={() => setShowAddForm(true)} disabled={isAddingEntry}>
            <Plus className="w-4 h-4 mr-2" />
            Add Entry
          </Button>
        </div>

        {/* Search Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5" />
              Search Knowledge Base
            </CardTitle>
            <CardDescription>
              Search through your knowledge base using semantic search
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                placeholder="Enter your search query..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
              />
              <Button onClick={handleSearch} disabled={isSearching}>
                {isSearching ? "Searching..." : "Search"}
              </Button>
            </div>

            {searchResults.length > 0 && (
              <div className="mt-6">
                <h3 className="text-base font-semibold mb-2">
                  Search Results ({searchResults.length})
                </h3>
                <div className="max-h-72 overflow-y-auto pr-2 space-y-2">
                  {searchResults.map((result, index) => (
                    <div
                      key={index}
                      className="p-2 border rounded-md cursor-default hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex justify-between items-start mb-1">
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0.5">
                          {result.title}
                        </Badge>
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0.5">
                          {(result.score * 100).toFixed(1)}%
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">Chunk {result.chunk_index + 1}</p>
                      <p className="text-sm line-clamp-2 mt-1">{result.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Add New Entry Form */}
        {showAddForm && (
          <Card>
            <CardHeader>
              <CardTitle>Add New Knowledge Base Entry</CardTitle>
              <CardDescription>
                Add new content to your knowledge base
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  value={newEntry.title}
                  onChange={(e) => setNewEntry({ ...newEntry, title: e.target.value })}
                  placeholder="Enter a title for this entry"
                  disabled={isAddingEntry}
                />
              </div>
              <div>
                <Label htmlFor="content">Content</Label>
                <Textarea
                  id="content"
                  value={newEntry.content}
                  onChange={(e) => setNewEntry({ ...newEntry, content: e.target.value })}
                  placeholder="Enter the content for this entry..."
                  rows={8}
                  disabled={isAddingEntry}
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleAddEntry} disabled={isAddingEntry}>
                  {isAddingEntry ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    "Save Entry"
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowAddForm(false);
                    setNewEntry({ title: "", content: "" });
                  }}
                  disabled={isAddingEntry}
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Existing Entries */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">Existing Entries</h2>
          <div className="max-h-[60vh] overflow-y-auto pr-2">
            {entries.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <p className="text-center text-muted-foreground">
                    No knowledge base entries found. Add your first entry to get started.
                  </p>
                </CardContent>
              </Card>
            ) : (
              entries.map((entry, index) => (
                <Card key={index} className="mb-4">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle>{entry.title}</CardTitle>
                        <CardDescription>
                          {entry.chunks.length} chunks • Created:{" "}
                          {formatDate(entry.created_at)}
                        </CardDescription>
                      </div>
                      <div className="flex gap-2">
                        {editingEntry === entry.title ? (
                          <>
                            <Button
                              size="sm"
                              disabled={savingTitle === entry.title}
                              onClick={() => {
                                const content = getCombinedContent(entry);
                                handleUpdateEntry(entry.title, content);
                              }}
                            >
                              {savingTitle === entry.title ? (
                                <>
                                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                                  Saving...
                                </>
                              ) : (
                                <>
                                  <Save className="w-4 h-4 mr-1" />
                                  Save
                                </>
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditingEntry(null)}
                              disabled={savingTitle === entry.title}
                            >
                              <X className="w-4 h-4 mr-1" />
                              Cancel
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditingEntry(entry.title)}
                              disabled={deletingTitle === entry.title}
                            >
                              <Edit className="w-4 h-4 mr-1" />
                              Edit
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteEntry(entry.title)}
                              disabled={deletingTitle === entry.title}
                            >
                              {deletingTitle === entry.title ? (
                                <>
                                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                                  Deleting...
                                </>
                              ) : (
                                <>
                                  <Trash2 className="w-4 h-4 mr-1" />
                                  Delete
                                </>
                              )}
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {editingEntry === entry.title ? (
                      <Textarea
                        defaultValue={getCombinedContent(entry)}
                        rows={8}
                        className="w-full"
                      />
                    ) : (
                      <div className="space-y-2">
                        {entry.chunks.map((chunk, chunkIndex) => (
                          <div key={chunk.id} className="p-3 bg-muted rounded-lg">
                            <div className="flex justify-between items-center mb-2">
                              <Badge variant="outline">Chunk {chunkIndex + 1}</Badge>
                              <span className="text-xs text-muted-foreground">
                                {formatDate(chunk.created_at)}
                              </span>
                            </div>
                            <p className="text-sm">{chunk.content}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>
    </LayoutWrapper>
  );
} 