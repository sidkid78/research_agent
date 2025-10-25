"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { 
  Plus, 
  X, 
  Play, 
  Square, 
  Send, 
  Mic, 
  MicOff, 
  Users, 
  Clock,
  MessageSquare,
  TrendingUp,
  FileText,
  Loader2
} from 'lucide-react';
import { toast } from "sonner";
import {
  submitBatchResearch,
  getBatchResearchStatus,
  getBatchResearchResults,
  startLiveResearchSession,
  endLiveResearchSession,
  createLiveResearchWebSocket
} from '@/lib/api';
import {
  BatchResearchRequest,
  BatchResearchResult,
  LiveResearchStartRequest,
  LiveResearchSummary,
  type LiveResearchSession,
  OutputFormat
} from '@/lib/types';

// Batch Research Component
export function BatchResearchForm() {
  const [topics, setTopics] = useState<string[]>(['']);
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('bullets');
  const [email, setEmail] = useState('');
  const [researchType, setResearchType] = useState<'summary' | 'trends' | 'comparison' | 'deep_dive'>('summary');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [batchStatus, setBatchStatus] = useState<Record<string, unknown> | null>(null);
  const [results, setResults] = useState<BatchResearchResult | null>(null);
  const [selectedResult, setSelectedResult] = useState<string | null>(null);

  const addTopic = () => {
    setTopics([...topics, '']);
  };

  const removeTopic = (index: number) => {
    if (topics.length > 1) {
      setTopics(topics.filter((_, i) => i !== index));
    }
  };

  const updateTopic = (index: number, value: string) => {
    const newTopics = [...topics];
    newTopics[index] = value;
    setTopics(newTopics);
  };

  const submitBatch = async () => {
    const validTopics = topics.filter(topic => topic.trim().length > 0);
    if (validTopics.length === 0) {
      toast.error("No topics provided", { description: "Please add at least one research topic." });
      return;
    }

    setIsSubmitting(true);
    try {
      const request: BatchResearchRequest = {
        topics: validTopics,
        output_format: outputFormat,
        email: email || undefined,
        research_type: researchType
      };

      const response = await submitBatchResearch(request);
      setBatchId(response.batch_id);
      toast.success("Batch research submitted", { 
        description: `Processing ${validTopics.length} topics. Batch ID: ${response.batch_id}` 
      });
    } catch {
      toast.error("Submission failed", { description: "Could not submit batch research" });
    }
    setIsSubmitting(false);
  };

  const stopBatch = () => {
    setBatchId(null);
    setBatchStatus(null);
    setResults(null);
    toast.info("Batch research stopped", { description: "Processing has been cancelled" });
  };

  const exportResults = () => {
    if (!results) return;
    
    const dataStr = JSON.stringify(results, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `batch-research-${batchId}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    toast.success("Results exported", { description: "Research results downloaded as JSON" });
  };

  // Poll for batch status
  useEffect(() => {
    if (!batchId) return;

    const pollStatus = async () => {
      try {
        const status = await getBatchResearchStatus(batchId);
        setBatchStatus(status);

        if (status.status === 'completed') {
          const batchResults = await getBatchResearchResults(batchId);
          setResults(batchResults);
        }
      } catch (err) {
        console.error('Failed to poll batch status:', err);
      }
    };

    const interval = setInterval(pollStatus, 5000);
    pollStatus(); // Initial call

    return () => clearInterval(interval);
  }, [batchId]);

  if (results) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Batch Research Results</span>
              <div className="flex gap-2">
                <Button onClick={exportResults} variant="outline" size="sm">
                  <FileText className="h-4 w-4 mr-1" />
                  Export
                </Button>
                <Button onClick={() => setResults(null)} variant="outline" size="sm">
                  <X className="h-4 w-4 mr-1" />
                  Close
                </Button>
              </div>
            </CardTitle>
            <CardDescription>
              Completed {results.completed_topics} of {results.total_topics} topics in {results.processing_time_seconds}s
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-700">{results.completed_topics}</div>
                <div className="text-sm text-green-600">Completed</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-700">{results.failed_topics}</div>
                <div className="text-sm text-red-600">Failed</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-700">{(results.overall_confidence * 100).toFixed(0)}%</div>
                <div className="text-sm text-blue-600">Avg. Confidence</div>
              </div>
            </div>

            <div className="space-y-4">
              {Object.entries(results.results).map(([topic, result]) => (
                <Card key={topic}>
                  <CardHeader>
                    <CardTitle className="text-lg">{topic}</CardTitle>
                    <div className="flex gap-2">
                      <Badge>{result.output_format}</Badge>
                      <Badge variant="secondary">{(result.confidence_score * 100).toFixed(0)}% confidence</Badge>
                      <Badge variant="outline">{result.word_count} words</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {selectedResult === topic ? (
                      <div className="space-y-4">
                        <div className="prose max-w-none">
                          <pre className="whitespace-pre-wrap text-sm">{result.content}</pre>
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => setSelectedResult(null)}
                        >
                          <X className="h-4 w-4 mr-1" />
                          Collapse
                        </Button>
                      </div>
                    ) : (
                      <div>
                        <p className="text-sm text-muted-foreground line-clamp-3">
                          {result.content.slice(0, 200)}...
                        </p>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="mt-2"
                          onClick={() => setSelectedResult(topic)}
                        >
                          <FileText className="h-4 w-4 mr-1" />
                          View Full Result
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (batchStatus) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Processing Batch Research</span>
            <Button onClick={stopBatch} variant="outline" size="sm">
              <Square className="h-4 w-4 mr-1" />
              Stop
            </Button>
          </CardTitle>
          <CardDescription>Batch ID: {batchId}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progress</span>
              <span>{(batchStatus.progress as number * 100).toFixed(0)}%</span>
            </div>
            <Progress value={(batchStatus.progress as number) * 100} />
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="font-medium">Completed Topics</div>
              <div className="text-muted-foreground">{(batchStatus.completed_topics as string[]).length}</div>
            </div>
            <div>
              <div className="font-medium">Failed Topics</div>
              <div className="text-muted-foreground">{(batchStatus.failed_topics as string[]).length}</div>
            </div>
          </div>

          {(batchStatus.completed_topics as string[]).length > 0 && (
            <div>
              <div className="font-medium text-sm mb-2">Completed:</div>
              <div className="flex flex-wrap gap-1">
                {(batchStatus.completed_topics as string[]).map((topic: string, idx: number) => (
                  <Badge key={idx} variant="secondary" className="text-xs">
                    {topic.slice(0, 30)}...
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Batch Research</CardTitle>
        <CardDescription>
          Research multiple topics simultaneously for efficient comparison and analysis
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Topics */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium">Research Topics</h3>
            <Button onClick={addTopic} size="sm" variant="outline">
              <Plus className="h-4 w-4 mr-1" /> Add Topic
            </Button>
          </div>
          
          {topics.map((topic, index) => (
            <div key={index} className="flex gap-2">
              <Textarea
                placeholder={`Research topic ${index + 1}...`}
                value={topic}
                onChange={(e) => updateTopic(index, e.target.value)}
                className="flex-1"
                rows={2}
              />
              {topics.length > 1 && (
                <Button 
                  onClick={() => removeTopic(index)} 
                  size="sm" 
                  variant="ghost"
                  className="mt-1"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          ))}
        </div>

        <Separator />

        {/* Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Output Format</label>
              <select 
                title="Output Format"
                value={outputFormat} 
                onChange={(e) => setOutputFormat(e.target.value as OutputFormat)}
                className="w-full mt-1 p-2 border rounded"
              >
                <option value="bullets">Bullet Points</option>
                <option value="full_report">Full Report</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium">Research Type</label>
              <select 
                title="Research Type"
                value={researchType} 
                onChange={(e) => setResearchType(e.target.value as "summary" | "trends" | "comparison" | "deep_dive")}
                className="w-full mt-1 p-2 border rounded"
              >
                <option value="summary">Summary</option>
                <option value="trends">Trends Analysis</option>
                <option value="comparison">Comparison</option>
                <option value="deep_dive">Deep Dive</option>
              </select>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Email (for PubMed)</label>
              <Input
                type="email"
                placeholder="your.email@domain.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>
        </div>

        <Button 
          onClick={submitBatch} 
          disabled={isSubmitting || topics.every(t => !t.trim())}
          className="w-full"
          size="lg"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Submitting Batch...
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Start Batch Research ({topics.filter(t => t.trim()).length} topics)
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

// Live Research Session Component
export function LiveResearchSessionComponent() {
  const [session, setSession] = useState<LiveResearchSession | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [messages, setMessages] = useState<Array<Record<string, unknown>>>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [currentTopic, setCurrentTopic] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [summary, setSummary] = useState<LiveResearchSummary | null>(null);
  const [participants, setParticipants] = useState<number>(1);
  const [sessionDuration, setSessionDuration] = useState<number>(0);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startSession = async (topic: string) => {
    setIsStarting(true);
    try {
      const request: LiveResearchStartRequest = {
        topic,
        modalities: ['TEXT', 'AUDIO'],
      };

      const newSession = await startLiveResearchSession(request);
      setSession(newSession);
      setSessionDuration(0);

      // Connect WebSocket
      wsRef.current = createLiveResearchWebSocket(
        newSession.session_id as string,
        (data) => {
          setMessages(prev => [...prev, {
            ...(data as Record<string, unknown>),
            timestamp: new Date().toISOString()
          }]);
        },
        (error) => {
          console.error("Connection error:", error);
          toast.error("Connection error", { description: "Lost connection to research session" });
        },
        () => {
          toast.info("Session ended", { description: "Research session has been closed" });
        }
      );

      toast.success("Live session started", { description: `Session ID: ${newSession.session_id}` });
    } catch (err) {
      console.error("Failed to start session:", err);
      toast.error("Failed to start session", { description: "Could not initialize live research" });
    }
    setIsStarting(false);
  };

  const sendMessage = () => {
    if (!currentMessage.trim() || !wsRef.current || isSending) return;

    setIsSending(true);
    wsRef.current.send(JSON.stringify({
      type: 'message',
      content: currentMessage,
      message_type: 'text'
    }));

    setMessages(prev => [...prev, {
      type: 'user_message',
      content: currentMessage,
      timestamp: new Date().toISOString(),
      sender: 'user'
    }]);

    setCurrentMessage('');
    setIsSending(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        // Send audio to WebSocket
        if (wsRef.current) {
          const reader = new FileReader();
          reader.onload = () => {
            wsRef.current?.send(JSON.stringify({
              type: 'audio',
              content: reader.result,
              message_type: 'audio'
            }));
          };
          reader.readAsDataURL(audioBlob);
        }
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      toast.info("Recording started", { description: "Speak your question or comment" });
    } catch {
      toast.error("Recording failed", { description: "Could not access microphone" });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      toast.success("Recording sent", { description: "Audio message has been sent" });
    }
  };

  const endSession = async () => {
    if (!session) return;

    try {
      const finalSummary = await endLiveResearchSession(session.session_id as string);
      setSummary(finalSummary);
      
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      
      setSession(null);
      toast.success("Session ended", { description: "Research summary generated" });
    } catch {
      toast.error("Failed to end session", { description: "Could not properly close session" });
    }
  };

  const exportSessionData = () => {
    if (!session || messages.length === 0) return;
    
    const sessionData = {
      session_id: session.session_id as string,
      topic: session.topic,
      messages: messages,
      duration: sessionDuration,
      participants: participants
    };
    
    const dataStr = JSON.stringify(sessionData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `live-session-${session.session_id as string}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    toast.success("Session exported", { description: "Session data downloaded as JSON" });
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Session duration timer
  useEffect(() => {
    if (!session) return;

    const timer = setInterval(() => {
      setSessionDuration(prev => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [session]);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (summary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Research Session Summary</span>
            <Button onClick={() => setSummary(null)} variant="outline" size="sm">
              <X className="h-4 w-4 mr-1" />
              Close
            </Button>
          </CardTitle>
          <CardDescription>
            Topic: {summary.topic} • Duration: {summary.duration_minutes.toFixed(1)} minutes
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-700">{summary.total_interactions}</div>
              <div className="text-sm text-blue-600 flex items-center justify-center gap-1">
                <MessageSquare className="h-3 w-3" />
                Total Interactions
              </div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-700">{summary.key_findings.length}</div>
              <div className="text-sm text-green-600">Key Findings</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-700">{summary.questions_explored.length}</div>
              <div className="text-sm text-purple-600">Questions Explored</div>
            </div>
          </div>

          {summary.key_findings.length > 0 && (
            <div>
              <h3 className="font-medium mb-3 flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Key Findings
              </h3>
              <ul className="list-disc pl-5 space-y-2">
                {summary.key_findings.map((finding, index) => (
                  <li key={index}>{finding.finding}</li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  if (session) {
    return (
      <Card className="h-[600px] flex flex-col">
        <CardHeader className="flex-shrink-0">
          <CardTitle className="flex items-center justify-between">
            <span>Live Research Session</span>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="flex items-center gap-1">
                <Users className="h-3 w-3" />
                {participants}
              </Badge>
              <Badge variant="outline" className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatDuration(sessionDuration as number)}
              </Badge>
              <Button onClick={exportSessionData} variant="outline" size="sm">
                <FileText className="h-4 w-4 mr-1" />
                Export
              </Button>
              <Button onClick={endSession} variant="outline" size="sm">
                <Square className="h-4 w-4 mr-1" />
                End Session
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Topic: {(session.topic as string)} • Session ID: {(session.session_id as string)}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col space-y-4">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto border rounded-lg p-4 space-y-3">
            {messages.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>Start the conversation by asking a question about your research topic.</p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-3 rounded-lg ${
                      message.sender === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className="text-sm">{message.content as string}</p>
                    <p className="text-xs opacity-70 mt-1">
                      {new Date(message.timestamp as string).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="flex gap-2">
            <Textarea
              placeholder="Ask a question about your research topic..."
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              className="flex-1"
              rows={2}
              disabled={isSending}
            />
            <div className="flex flex-col gap-2">
              <Button
                onClick={sendMessage}
                disabled={!currentMessage.trim() || isSending}
                size="sm"
              >
                {isSending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
              <Button
                onClick={isRecording ? stopRecording : startRecording}
                variant={isRecording ? "destructive" : "outline"}
                size="sm"
              >
                {isRecording ? (
                  <MicOff className="h-4 w-4" />
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Live Research Session</CardTitle>
        <CardDescription>
          Conduct a live research session with our AI agent
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Topic</label>
              <Input
                type="text"
                placeholder="Enter a research topic"
                value={currentTopic}
                onChange={(e) => setCurrentTopic(e.target.value)}
                className="w-full"
              />
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium flex items-center gap-2">
                <Users className="h-4 w-4" />
                Expected Participants
              </label>
              <Input
                type="number"
                min="1"
                max="10"
                value={participants}
                onChange={(e) => setParticipants(parseInt(e.target.value) || 1)}
                className="w-full"
              />
            </div>
          </div>
        </div>
        <Button 
          onClick={() => startSession(currentTopic)}
          disabled={isStarting || !currentTopic.trim()}
          className="w-full"
          size="lg"
        >
          {isStarting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Starting Session...
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Start Live Research Session
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}