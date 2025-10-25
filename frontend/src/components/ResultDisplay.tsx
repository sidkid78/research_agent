'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ResearchResult, Reference } from '../lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  ClipboardCopyIcon, 
  CalendarIcon, 
  FlaskConical, 
  BookOpen, 
  Globe, 
  TrendingUp,
  Award,
  Clock,
  ExternalLink,
  Download,
  Filter,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { toast } from "sonner";
import { exportResearchResult } from '@/lib/api';

interface EnhancedResultDisplayProps {
  resultData: ResearchResult;
}

// Research statistics component
const ResearchStats: React.FC<{ resultData: ResearchResult }> = ({ resultData }) => {
  const stats = [
    {
      icon: <Award className="h-4 w-4 text-yellow-500" />,
      label: "Peer Reviewed",
      value: `${(resultData.research_quality_indicators?.peer_reviewed_percentage || 0).toFixed(0)}%`
    },
    {
      icon: <Clock className="h-4 w-4 text-green-500" />,
      label: "Recent Sources",
      value: `${(resultData.research_quality_indicators?.recent_sources_percentage || 0).toFixed(0)}%`
    },
    {
      icon: <TrendingUp className="h-4 w-4 text-blue-500" />,
      label: "Authoritative",
      value: `${(resultData.research_quality_indicators?.authoritative_sources_percentage || 0).toFixed(0)}%`
    }
  ];

  return (
    <div className="grid grid-cols-3 gap-4">
      {stats.map((stat, index) => (
        <div key={index} className="text-center p-3 bg-muted/50 rounded-lg">
          <div className="flex justify-center mb-1">{stat.icon}</div>
          <div className="text-lg font-semibold">{stat.value}</div>
          <div className="text-xs text-muted-foreground">{stat.label}</div>
        </div>
      ))}
    </div>
  );
};

// Filter component for references
const ReferenceFilter: React.FC<{ 
  onFilterChange: (filters: { sourceType: string; minConfidence: number }) => void 
}> = ({ onFilterChange }) => {
  const [sourceType, setSourceType] = useState('all');
  const [minConfidence, setMinConfidence] = useState(0);

  const handleFilterChange = () => {
    onFilterChange({ sourceType, minConfidence });
  };

  return (
    <div className="flex items-center gap-4 p-4 bg-muted/50 rounded-lg">
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4" />
        <span className="text-sm font-medium">Filters:</span>
      </div>
      <select 
        title="Source Type"
        value={sourceType} 
        onChange={(e) => { setSourceType(e.target.value); handleFilterChange(); }}
        className="text-sm border rounded px-2 py-1"
      >
        <option value="all">All Sources</option>
        <option value="arxiv">arXiv</option>
        <option value="pubmed">PubMed</option>
        <option value="web">Web</option>
      </select>
      <div className="flex items-center gap-2">
        <span className="text-sm">Min Confidence:</span>
        <input
          type="range"
          title="Min Confidence"
          min="0"
          max="1"
          step="0.1"
          value={minConfidence}
          onChange={(e) => { setMinConfidence(parseFloat(e.target.value)); handleFilterChange(); }}
          className="w-20"
        />
        <span className="text-sm w-8">{(minConfidence * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
};

// Enhanced reference component with academic metadata
const AcademicReferenceItem: React.FC<{ reference: Reference; index: number }> = ({ reference, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'arxiv': return <FlaskConical className="h-4 w-4 text-orange-500" />;
      case 'pubmed': return <BookOpen className="h-4 w-4 text-blue-500" />;
      case 'web': return <Globe className="h-4 w-4 text-green-500" />;
      default: return <ExternalLink className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSourceBadge = (sourceType: string) => {
    const configs = {
      arxiv: { label: 'arXiv', variant: 'default' as const, color: 'bg-orange-100 text-orange-800' },
      pubmed: { label: 'PubMed', variant: 'default' as const, color: 'bg-blue-100 text-blue-800' },
      web: { label: 'Web', variant: 'secondary' as const, color: 'bg-green-100 text-green-800' },
    };
    
    const config = configs[sourceType as keyof typeof configs] || { label: 'Source', variant: 'outline' as const, color: '' };
    
    return (
      <Badge variant={config.variant} className={config.color}>
        {config.label}
      </Badge>
    );
  };

  const copyReferenceToClipboard = async () => {
    const referenceText = `[${index + 1}] ${reference.title}. ${reference.authors?.join(', ')}. ${reference.journal ? `${reference.journal}. ` : ''}${reference.published_year ? `${reference.published_year}. ` : ''}${reference.url}`;
    
    try {
      await navigator.clipboard.writeText(referenceText);
      toast.success("Reference copied to clipboard");
    } catch (error: unknown) {
      console.error("Failed to copy reference", error);
      toast.error("Failed to copy reference");
    }
  };

  return (
    <li className="border rounded-lg p-4 bg-card hover:bg-accent/50 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {getSourceIcon(reference.source_type || 'unknown')}
          <span className="font-medium text-sm text-muted-foreground">[{index + 1}]</span>
          {getSourceBadge(reference.source_type || 'unknown')}
          {reference.confidence_score && (
            <Badge variant="outline" className="text-xs">
              {(reference.confidence_score * 100).toFixed(0)}% confidence
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={copyReferenceToClipboard}
            className="h-6 w-6 p-0"
            title="Copy reference"
          >
            <ClipboardCopyIcon className="h-3 w-3" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-6 w-6 p-0"
          >
            {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </Button>
        </div>
      </div>
      
      <div className="space-y-2">
        <h4 className="font-semibold text-sm leading-tight">{reference.title}</h4>
        
        {/* Academic metadata */}
        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
          {reference.authors && reference.authors.length > 0 && (
            <span>Authors: {reference.authors.slice(0, 3).join(", ")}{reference.authors.length > 3 ? " et al." : ""}</span>
          )}
          {reference.journal && (
            <span>• Journal: {reference.journal}</span>
          )}
          {reference.published_year && (
            <span>• Year: {reference.published_year}</span>
          )}
        </div>

        {/* DOI and identifiers */}
        <div className="flex flex-wrap gap-2 text-xs">
          {reference.doi && (
            <Badge variant="outline" className="text-xs">
              DOI: {reference.doi}
            </Badge>
          )}
          {reference.pmid && (
            <Badge variant="outline" className="text-xs">
              PMID: {reference.pmid}
            </Badge>
          )}
        </div>

        {/* Categories/Fields */}
        {reference.categories && reference.categories.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {reference.categories.slice(0, 3).map((category, idx) => (
              <Badge key={idx} variant="secondary" className="text-xs">
                {category}
              </Badge>
            ))}
            {reference.categories.length > 3 && (
              <Badge variant="secondary" className="text-xs">
                +{reference.categories.length - 3} more
              </Badge>
            )}    
          </div>
        )}

        {/* Snippet - always visible but truncated */}
        {reference.snippet && (
          <p className="text-sm text-muted-foreground italic leading-relaxed">
            {isExpanded ? reference.snippet : `${reference.snippet.slice(0, 150)}${reference.snippet.length > 150 ? '...' : ''}`}
          </p>
        )}

        {/* Access information */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <CalendarIcon className="h-3 w-3" />
              Accessed: {new Date(reference.accessed_date).toLocaleDateString()}
            </div>
          </div>
          <a 
            href={reference.url} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="inline-flex items-center gap-1 text-xs text-primary hover:text-primary/80 underline"
          >
            View Source <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </li>
  );
};

// Main enhanced result display component
const EnhancedResultDisplay: React.FC<EnhancedResultDisplayProps> = ({ resultData }) => {
  const [filteredReferences, setFilteredReferences] = useState(resultData.references || []);
  const [isExporting, setIsExporting] = useState(false);

  const handleFilterChange = (filters: { sourceType: string; minConfidence: number }) => {
    let filtered = resultData.references || [];
    
    if (filters.sourceType !== 'all') {
      filtered = filtered.filter(ref => ref.source_type === filters.sourceType);
    }
    
    if (filters.minConfidence > 0) {
      filtered = filtered.filter(ref => (ref.confidence_score || 0) >= filters.minConfidence);
    }
    
    setFilteredReferences(filtered);
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await exportResearchResult(resultData.job_id || '');
      toast.success("Research result exported successfully");
      console.log("Research result exported successfully");
    } catch (error: unknown) {
      console.error("Failed to export research result", error);
      toast.error("Failed to export research result");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with export button */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Research Results</h2>
        <Button onClick={handleExport} disabled={isExporting} className="flex items-center gap-2">
          <Download className="h-4 w-4" />
          {isExporting ? "Exporting..." : "Export Results"}
        </Button>
      </div>

      {/* Progress and Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Research Progress</CardTitle>
          </CardHeader>
           <CardContent>
             <div className="space-y-3">
               <div className="flex items-center justify-between">
                 <span className="text-sm font-medium">Research Quality</span>
                 <span className="text-sm text-muted-foreground">
                   {resultData.references?.length || 0} sources
                 </span>
               </div>
               <Progress value={75} className="h-2" />
               <div className="text-xs text-muted-foreground text-center">
                 Analysis complete
               </div>
             </div>
           </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <ResearchStats resultData={resultData} />
          </CardContent>
        </Card>
      </div>

      {/* Main content with tabs */}
      <Tabs defaultValue="summary" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="references">References ({filteredReferences.length})</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
        </TabsList>
        
        <TabsContent value="summary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Research Summary</CardTitle>
              <CardDescription>
                Generated on {new Date(resultData.generated_at).toLocaleDateString()}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {resultData.content}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="references" className="space-y-4">
          <ReferenceFilter onFilterChange={handleFilterChange} />
          
          <Card>
            <CardHeader>
              <CardTitle>References</CardTitle>
              <CardDescription>
                {filteredReferences.length} of {resultData.academic_source_breakdown?.total_sources || resultData.references?.length || 0} references shown
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-4">
                {filteredReferences.map((reference, index) => (
                  <AcademicReferenceItem 
                    key={index} 
                    reference={reference} 
                    index={index} 
                  />
                ))}
              </ul>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="analysis" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Research Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Key Findings</h4>
                  <p className="text-sm text-muted-foreground">
                    Analysis of {resultData.academic_source_breakdown?.total_sources || resultData.references?.length || 0} sources reveals key insights in the research domain.
                  </p>
                </div>
                
                <Separator />
                
                <div>
                  <h4 className="font-semibold mb-2">Source Distribution</h4>
                  <div className="space-y-2">
                    {['arxiv', 'pubmed', 'web'].map(sourceType => {
                      const count = resultData.academic_source_breakdown?.[sourceType as keyof typeof resultData.academic_source_breakdown] || 0;
                      const percentage = resultData.references?.length ? (count / resultData.references.length) * 100 : 0;
                      
                      return (
                        <div key={sourceType} className="flex items-center justify-between">
                          <span className="text-sm capitalize">{sourceType}</span>
                          <div className="flex items-center gap-2">
                            <Progress value={percentage} className="w-20 h-2" />
                            <span className="text-xs text-muted-foreground w-8">{count}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EnhancedResultDisplay;
