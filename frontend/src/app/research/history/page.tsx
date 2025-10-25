"use client";

import { useState, useEffect } from 'react';
import { getResearchHistory } from '@/lib/api';
import { ResearchHistoryItem } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function ResearchHistoryPage() {
  const [history, setHistory] = useState<ResearchHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const result = await getResearchHistory();
        setHistory(result.items);
      } catch (error) {
        console.error('Failed to load history:', error);
      }
      setLoading(false);
    };
    loadHistory();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Research History</h1>
      <div className="space-y-4">
        {history.map((item) => (
          <Card key={item.job_id}>
            <CardHeader>
              <CardTitle>{item.topic}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{item.preview}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}