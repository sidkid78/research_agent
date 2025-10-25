'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { StatusDisplay } from '@/components/StatusDisplay';
import ResultDisplay from '@/components/ResultDisplay';
import { ResearchResult, ResearchRequest, JobStatus } from '@/lib/types';
import { getJobResult, getJobStatus, getJobDetails } from '@/lib/api';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';

export default function JobPage() {
  const params = useParams();
  const jobId = typeof params.jobId === 'string' ? params.jobId : '';

  // State for this page
  const [initialStatus, setInitialStatus] = useState<JobStatus | null>(null);
  const [initialProgress, setInitialProgress] = useState<number | undefined>(undefined);
  const [requestDetails, setRequestDetails] = useState<Pick<ResearchRequest, 'topic' | 'output_format' | 'deadline'> | null>(null);
  const [finalResult, setFinalResult] = useState<ResearchResult | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [isLoadingInitialData, setIsLoadingInitialData] = useState<boolean>(true);

  useEffect(() => {
    if (!jobId) {
      setPageError("No Job ID specified.");
      setIsLoadingInitialData(false);
      return;
    }

    async function fetchInitialData() {
      try {
        // Fetch status and details in parallel
        const [statusRes, detailsRes] = await Promise.all([
          getJobStatus(jobId),
          getJobDetails(jobId) // Fetch job details
        ]);

        setInitialStatus(statusRes.status);
        setInitialProgress(statusRes.progress);
        setRequestDetails({ // Use actual details
          topic: detailsRes.topic,
          output_format: detailsRes.output_format,
          deadline: detailsRes.deadline
        });

        if (statusRes.status === 'completed') {
          handleJobCompletion(jobId);
        } else if (statusRes.status === 'failed') {
          handleJobFailure(jobId, `Job initially found in a failed state.`);
        }
      } catch (err) {
        console.error("Error fetching initial job data:", err);
        setPageError(err instanceof Error ? err.message : 'Error loading job information.');
      }
      setIsLoadingInitialData(false);
    }

    fetchInitialData();
  }, [jobId]);

  const handleJobCompletion = async (completedJobId: string) => {
    console.log(`Job ${completedJobId} completed. Fetching results...`);
    setIsLoadingInitialData(true);
    try {
      const resultRes = await getJobResult(completedJobId);
      setFinalResult(resultRes);
      setPageError(null);
    } catch (err) {
      console.error('Error fetching job result:', err);
      setPageError(err instanceof Error ? err.message : 'Failed to load results.');
      setFinalResult(null);
    }
    setIsLoadingInitialData(false);
  };

  const handleJobFailure = (failedJobId: string, errorMessage: string) => {
    console.log(`Job ${failedJobId} failed: ${errorMessage}`);
    setPageError(errorMessage);
    setInitialStatus('failed');
    setIsLoadingInitialData(false);
  };

  if (!jobId && !isLoadingInitialData) {
    return (
        <div className="container mx-auto px-4 py-8 text-center">
            <p className="text-xl text-red-600">Error: No Job ID specified in the URL.</p>
            <Button asChild className="mt-4">
              <Link href="/research">Create New Research Job</Link>
            </Button>
        </div>
    );
  }
  
  if (isLoadingInitialData) {
    return (
      <div className="container mx-auto px-4 py-8 text-center flex flex-col items-center justify-center min-h-screen">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600 mb-4" />
        <p className="text-xl font-semibold">Loading Job Details for {jobId || '...'} </p>
      </div>
    );
  }

  if (pageError && !finalResult) {
    return (
        <div className="container mx-auto px-4 py-8 text-center flex flex-col items-center">
            <p className="text-xl text-red-600 mb-6">{pageError}</p>
            <Button asChild className="mt-4">
              <Link href="/research">Go to Research Form</Link>
            </Button>
        </div>
    );
  }

  if (finalResult) {
    return (
      <div className="container mx-auto px-4 py-8 flex flex-col items-center space-y-8">
        <ResultDisplay resultData={finalResult} />
        <Button asChild className="mt-4">
            <Link href="/research">Create Another Research Job</Link>
        </Button>
      </div>
    );
  }

  if (initialStatus && requestDetails && initialStatus !== 'completed' && initialStatus !== 'failed') {
    return (
      <div className="container mx-auto px-4 py-8 flex flex-col items-center space-y-8">
        <StatusDisplay 
          jobId={jobId} 
          initialStatus={initialStatus}
          initialProgress={initialProgress}
          requestDetails={requestDetails} 
          onJobCompletion={handleJobCompletion}
          onJobFailure={handleJobFailure}
        />
      </div>
    );
  }
  
  return (
    <div className="container mx-auto px-4 py-8 text-center flex flex-col items-center justify-center min-h-screen">
      <p className="text-xl font-semibold">Preparing job display for {jobId}...</p>
      <Link href="/research" className="mt-4">
        <Button variant="outline">Back to Research Form</Button>
      </Link>
    </div>
  ); 
} 