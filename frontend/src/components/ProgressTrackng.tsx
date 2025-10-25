import { Reference, ResearchResult } from "@/lib/types";
import { Progress } from "@radix-ui/react-progress";
import { BarChart3Icon } from "lucide-react";

// Progress tracking component
const ResearchProgress: React.FC<{ resultData: ResearchResult }> = ({ resultData }) => {
    const totalSources = resultData.references?.length || 0;
    const highConfidenceSources = resultData.references?.filter((ref: Reference) => (ref.confidence_score || 0) > 0.8).length || 0;
    const progressPercentage = totalSources > 0 ? (highConfidenceSources / totalSources) * 100 : 0;
  
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3Icon className="h-4 w-4 text-blue-500" />
            <span className="text-sm font-medium">Research Quality</span>
          </div>
          <span className="text-sm text-muted-foreground">{progressPercentage.toFixed(0)}%</span>
        </div>
        <Progress value={progressPercentage} className="h-2" />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{highConfidenceSources} high-confidence sources</span>
          <span>{totalSources} total sources</span>
        </div>
      </div>
    );
};

export default ResearchProgress;