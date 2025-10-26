import { LiveResearchSessionComponent } from '@/components/BatchLiveResearch';

export default function LiveResearchPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Live Research Session</h1>
      <LiveResearchSessionComponent />
    </div>
  );
}