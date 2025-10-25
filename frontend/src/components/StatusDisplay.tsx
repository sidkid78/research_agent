'use client';

import React, { useEffect, useState } from 'react';
import { JobStatus, ResearchRequest, JobStatusResponse } from '@/lib/types';
import { getJobStatus } from '@/lib/api';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from 'lucide-react';

interface StatusDisplayProps {
  jobId: string;
  initialStatus: JobStatus;
  initialProgress?: number;
  requestDetails: Pick<ResearchRequest, 'topic' | 'output_format' | 'deadline'>;
  onJobCompletion: (jobId: string) => void;
  onJobFailure: (jobId: string, error: string) => void;
}

export function StatusDisplay({
  jobId,
  initialStatus,
  initialProgress = 0,
  requestDetails,
  onJobCompletion,
  onJobFailure,
}: StatusDisplayProps) {
  const [status, setStatus] = useState<JobStatus>(initialStatus);
  const [progress, setProgress] = useState<number>(initialProgress);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === 'completed' || status === 'failed') {
      return;
    }

    const intervalId = setInterval(async () => {
      try {
        const currentJobStatus: JobStatusResponse = await getJobStatus(jobId);
        setStatus(currentJobStatus.status);
        setProgress(currentJobStatus.progress !== undefined ? currentJobStatus.progress * 100 : (currentJobStatus.status === 'completed' ? 100 : progress));
        setError(null);

        if (currentJobStatus.status === 'completed') {
          onJobCompletion(jobId);
          clearInterval(intervalId);
        } else if (currentJobStatus.status === 'failed') {
          const failureMsg = currentJobStatus.error_message || `Job ${jobId} failed with an unknown error.`;
          setError(failureMsg);
          onJobFailure(jobId, failureMsg);
          clearInterval(intervalId);
        }
      } catch (err) {
        let errorMessage = 'Failed to fetch job status.';
        if (err instanceof Error) {
          errorMessage = err.message;
        }
        setError(errorMessage);
        console.error('Polling error:', err);
      }
    }, 5000);

    return () => clearInterval(intervalId);
  }, [jobId, status, onJobCompletion, onJobFailure, progress]);

  const getStatusBadgeVariant = (): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'queued':
        return 'outline';
      case 'in_progress':
        return 'secondary';
      case 'completed':
        return 'default';
      case 'failed':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Research Job Status</span>
          <Badge variant={getStatusBadgeVariant()} className="capitalize">
            {status.replace('_', ' ')}
          </Badge>
        </CardTitle>
        <CardDescription>Tracking progress for Job ID: {jobId}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h3 className="font-semibold">Request Details:</h3>
          <p><strong>Topic:</strong> {requestDetails.topic}</p>
          <p><strong>Format:</strong> {requestDetails.output_format.replace('_', ' ')}</p>
          {requestDetails.deadline && (
            <p><strong>Deadline:</strong> {new Date(requestDetails.deadline).toLocaleDateString()}</p>
          )}
        </div>

        {status !== 'completed' && status !== 'failed' && (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              {status === 'queued' && 'Your job is waiting to be processed.'}
              {status === 'in_progress' && 'Your research is currently in progress...'}
            </p>
            <Progress value={progress} className="w-full" />
            {status === 'in_progress' && progress < 10 && <Loader2 className="h-5 w-5 animate-spin mr-2 inline-block" />}
          </div>
        )}

        {status === 'completed' && (
          <Alert variant="default">
            <AlertTitle>Job Completed!</AlertTitle>
            <AlertDescription>
              Your research results are ready.
            </AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
      {(status === 'completed' || status === 'failed') && (
        <CardFooter>
            <p className="text-xs text-muted-foreground">
                {status === 'completed' ? 'You can now view your results.' : 'Please try submitting your job again or contact support.'}
            </p>
        </CardFooter>
      )}
    </Card>
  );
} 