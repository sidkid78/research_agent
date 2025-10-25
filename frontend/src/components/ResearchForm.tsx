"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, useWatch } from "react-hook-form";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import { useState, useEffect } from "react";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { CalendarIcon, FlaskConical, BookOpen, Globe, InfoIcon, CheckCircle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { submitAcademicResearch, validatePubMedAccess, getAcademicSourcesPreview } from "@/lib/api";
import { toast } from "sonner";
import { ResearchRequest } from "@/lib/types";

const formSchema = z.object({
  topic: z.string().min(10, {
    message: "Research topic must be at least 10 characters.",
  }).max(500, {
    message: "Research topic must not exceed 500 characters.",
  }),
  output_format: z.enum(["bullets", "full_report"], {
    required_error: "You need to select an output format.",
  }),
  deadline: z.date().optional(),
  // Enhanced academic options
  email: z.string().email().optional().or(z.literal("")),
  preferred_sources: z.array(z.enum(["arxiv", "pubmed", "grounding"])).min(1, {
    message: "Select at least one source type.",
  }),
  research_depth: z.enum(["quick", "comprehensive", "deep_dive"]),
  date_range: z.object({
    start_year: z.number().min(1900).max(new Date().getFullYear()).optional(),
    end_year: z.number().min(1900).max(new Date().getFullYear()).optional(),
  }).optional(),
  academic_fields: z.array(z.string()).optional(),
});

export type ResearchFormValues = z.infer<typeof formSchema>;

const ACADEMIC_FIELDS = [
  "Computer Science",
  "Biology & Life Sciences",
  "Physics",
  "Mathematics",
  "Medicine & Health",
  "Chemistry",
  "Engineering",
  "Psychology",
  "Economics",
  "Materials Science",
  "Environmental Science",
  "Social Sciences",
  "Education",
  "Business & Management",
];

const SOURCE_INFO = {
  arxiv: {
    name: "arXiv",
    description: "Open-access repository of scientific papers in physics, mathematics, computer science, and related fields",
    icon: FlaskConical,
    fields: ["Computer Science", "Physics", "Mathematics", "Engineering"],
    requiresEmail: false,
    tooltip: "arXiv provides free access to over 2 million scholarly articles in STEM fields. Papers are often pre-prints and may not be peer-reviewed.",
  },
  pubmed: {
    name: "PubMed",
    description: "Biomedical literature database with peer-reviewed medical and life science papers",
    icon: BookOpen,
    fields: ["Biology & Life Sciences", "Medicine & Health", "Psychology"],
    requiresEmail: true,
    tooltip: "PubMed contains over 34 million citations for biomedical literature. Most papers are peer-reviewed and published in established journals.",
  },
  grounding: {
    name: "Google Search",
    description: "Authoritative web sources including news, government data, and industry reports",
    icon: Globe,
    fields: ["All fields"],
    requiresEmail: false,
    tooltip: "Searches authoritative web sources including government databases, news articles, and industry reports for the most current information.",
  },
};

export function EnhancedResearchForm() {
  const router = useRouter();
  const [emailValidation, setEmailValidation] = useState<{ valid?: boolean; message?: string }>({});
  const [sourcePreview, setSourcePreview] = useState<{ arxiv_preview: { title: string; authors: string[]; abstract: string; }[]; pubmed_preview: { title: string; journal: string; abstract: string; }[]; estimated_sources: number; } | null>(null);
  const [isValidatingEmail, setIsValidatingEmail] = useState(false);

  const form = useForm<ResearchFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      topic: "",
      output_format: "bullets",
      preferred_sources: ["pubmed", "grounding"],
      research_depth: "comprehensive",
      academic_fields: [],
      email: "",
    },
  });

  // Watch for changes to automatically suggest sources
  const watchedTopic = useWatch({ control: form.control, name: "topic" });
  const watchedSources = useWatch({ control: form.control, name: "preferred_sources" });
  const watchedEmail = useWatch({ control: form.control, name: "email" });

  // Validate email for PubMed access
  useEffect(() => {
    const validateEmail = async () => {
      if (watchedEmail && watchedSources.includes("pubmed")) {
        setIsValidatingEmail(true);
        try {
          const result = await validatePubMedAccess(watchedEmail);
          setEmailValidation(result);
        } catch (error) {
          console.error("Failed to validate email", error);
          setEmailValidation({ valid: false, message: "Failed to validate email" });
        }
        setIsValidatingEmail(false);
      } else {
        setEmailValidation({});
      }
    };

    const debounceTimer = setTimeout(validateEmail, 1000);
    return () => clearTimeout(debounceTimer);
  }, [watchedEmail, watchedSources]);

  // Preview academic sources
  useEffect(() => {
    const loadPreview = async () => {
      if (watchedTopic && watchedTopic.length > 20) {
        try {
          const preview = await getAcademicSourcesPreview(watchedTopic);
          setSourcePreview(preview);
        } catch (error) {
          console.error("Failed to load source preview:", error);
          setSourcePreview(null);
        }
      } else {
        setSourcePreview(null);
      }
    };

    const debounceTimer = setTimeout(loadPreview, 2000);
    return () => clearTimeout(debounceTimer);
  }, [watchedTopic]);

  // Auto-suggest sources based on topic
  useEffect(() => {
    if (watchedTopic) {
      const topicLower = watchedTopic.toLowerCase();
      const suggestedSources: ("arxiv" | "pubmed" | "grounding")[] = ["grounding"]; // Always include web search
      
      // Suggest arXiv for STEM topics
      if (topicLower.includes("computer") || topicLower.includes("algorithm") || 
          topicLower.includes("machine learning") || topicLower.includes("neural") ||
          topicLower.includes("quantum") || topicLower.includes("physics") ||
          topicLower.includes("mathematics") || topicLower.includes("ai")) {
        suggestedSources.push("arxiv");
      }
      
      // Suggest PubMed for biomedical topics
      if (topicLower.includes("medical") || topicLower.includes("health") ||
          topicLower.includes("disease") || topicLower.includes("drug") ||
          topicLower.includes("clinical") || topicLower.includes("biology") ||
          topicLower.includes("genetics") || topicLower.includes("therapeutic")) {
        suggestedSources.push("pubmed");
      }
      
      // Only update if current selection is default
      const currentSources = form.getValues("preferred_sources");
      if (currentSources.length <= 2) {
        form.setValue("preferred_sources", suggestedSources);
      }
    }
  }, [watchedTopic, form]);

  async function onSubmit(values: ResearchFormValues) {
    console.log('Form submitted with values:', values);
    
    try {
      // Validate PubMed email if needed
      if (values.preferred_sources.includes("pubmed") && !values.email) {
        toast.error("Email Required", {
          description: "PubMed access requires an email address for API compliance.",
        });
        return;
      }

      const requestData: ResearchRequest = {
        ...values,
        deadline: values.deadline ? values.deadline.toISOString() : undefined,
        email: values.email || undefined,
      };
      
      console.log('Prepared request data:', requestData);

      const result = await submitAcademicResearch(requestData);
      console.log('API response:', result);
      
      toast.success("Academic Research Submitted", {
        description: `Job ID: ${result.job_id}. Estimated duration: ${result.estimated_duration_minutes || 5} minutes.`,
      });
      
      router.push(`/research/${result.job_id}`);
    } catch (error) {
      let errorMessage = "Failed to submit research job.";
      if (error instanceof Error) {
        errorMessage = error.message;
      }
      toast.error("Submission Error", {
        description: errorMessage,
      });
      console.error("Submission error:", error);
    }
  }

  const currentYear = new Date().getFullYear();

  return (
    <TooltipProvider>
      <div className="space-y-8">
        {/* Header Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FlaskConical className="h-5 w-5" />
              Academic Research Agent
              <Tooltip>
                <TooltipTrigger asChild>
                  <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>AI-powered research agent that searches academic databases and web sources to provide comprehensive research reports with citations.</p>
                </TooltipContent>
              </Tooltip>
            </CardTitle>
            <CardDescription>
              Enhanced with arXiv, PubMed, and Google Search for comprehensive academic research
            </CardDescription>
          </CardHeader>
        </Card>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            {/* Research Topic */}
            <FormField
              control={form.control}
              name="topic"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-2">
                    Research Topic
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Be specific and include key terms. The AI will use this to search academic databases and identify relevant papers.</p>
                      </TooltipContent>
                    </Tooltip>
                  </FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="e.g., Latest developments in quantum machine learning algorithms for drug discovery"
                      className="min-h-[100px]"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Enter your research question or topic. Be specific for better academic source matching.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Source Preview */}
            {sourcePreview && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Source Preview</CardTitle>
                  <CardDescription>
                    Estimated {sourcePreview.estimated_sources} sources found
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {sourcePreview.arxiv_preview?.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2 flex items-center gap-2">
                        <FlaskConical className="h-4 w-4" />
                        arXiv Papers ({sourcePreview.arxiv_preview.length})
                      </h4>
                      <div className="space-y-2">
                        {sourcePreview.arxiv_preview.slice(0, 2).map((paper: { title: string; authors: string[]; }, idx: number) => (
                          <div key={idx} className="text-sm p-2 bg-gray-50 rounded">
                            <div className="font-medium">{paper.title}</div>
                            <div className="text-gray-600">Authors: {paper.authors.join(", ")}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {sourcePreview.pubmed_preview?.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2 flex items-center gap-2">
                        <BookOpen className="h-4 w-4" />
                        PubMed Papers ({sourcePreview.pubmed_preview.length})
                      </h4>
                      <div className="space-y-2">
                        {sourcePreview.pubmed_preview.slice(0, 2).map((paper: { title: string; journal: string; }, idx: number) => (
                          <div key={idx} className="text-sm p-2 bg-gray-50 rounded">
                            <div className="font-medium">{paper.title}</div>
                            <div className="text-gray-600">Journal: {paper.journal}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Academic Sources */}
            <FormField
              control={form.control}
              name="preferred_sources"
              render={() => (
                <FormItem>
                  <div className="mb-4">
                    <FormLabel className="text-base flex items-center gap-2">
                      Academic Sources
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Choose which databases to search. Different sources are better for different fields. You can select multiple sources.</p>
                        </TooltipContent>
                      </Tooltip>
                    </FormLabel>
                    <FormDescription>
                      Select which academic databases and sources to search
                    </FormDescription>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(SOURCE_INFO).map(([key, info]) => {
                      const Icon = info.icon;
                      return (
                        <FormField
                          key={key}
                          control={form.control}
                          name="preferred_sources"
                          render={({ field }) => {
                            return (
                              <FormItem key={key}>
                                <Card className={cn(
                                  "cursor-pointer transition-colors",
                                  field.value?.includes(key as unknown as "arxiv" | "pubmed" | "grounding") 
                                    ? "ring-2 ring-primary bg-primary/5" 
                                    : "hover:bg-gray-50"
                                )}>
                                  <CardContent className="p-4">
                                    <FormControl>
                                      <Checkbox
                                        checked={field.value?.includes(key as unknown as "arxiv" | "pubmed" | "grounding")}
                                        onCheckedChange={(checked: boolean) => {
                                          return checked
                                            ? field.onChange([...field.value, key as unknown as "arxiv" | "pubmed" | "grounding"])
                                            : field.onChange(
                                                field.value?.filter(
                                                  (value) => value !== key as unknown as "arxiv" | "pubmed" | "grounding"
                                                )
                                              )
                                        }}
                                        className="sr-only"
                                      />
                                    </FormControl>
                                    <div className="flex items-start gap-3">
                                      <Icon className="h-5 w-5 mt-0.5 text-primary" />
                                      <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                          <FormLabel className="text-sm font-medium cursor-pointer">
                                            {info.name}
                                          </FormLabel>
                                          <Tooltip>
                                            <TooltipTrigger asChild>
                                              <InfoIcon className="h-3 w-3 text-muted-foreground cursor-help" />
                                            </TooltipTrigger>
                                            <TooltipContent>
                                              <p className="max-w-xs">{info.tooltip}</p>
                                            </TooltipContent>
                                          </Tooltip>
                                          {info.requiresEmail && ( 
                                            <Badge variant="secondary" className="text-xs">
                                              Email Required
                                            </Badge>
                                          )}
                                        </div>
                                        <p className="text-xs text-gray-600 mb-2">
                                          {info.description}
                                        </p>
                                        <div className="flex flex-wrap gap-1">
                                          {info.fields.slice(0, 2).map((fieldName) => (
                                            <Badge key={fieldName} variant="outline" className="text-xs">
                                              {fieldName}
                                            </Badge>
                                          ))}
                                          {info.fields.length > 2 && (
                                            <Badge variant="outline" className="text-xs">
                                              +{info.fields.length - 2} more
                                            </Badge>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  </CardContent>
                                </Card>
                              </FormItem>
                            );
                          }}
                        />
                      );
                    })}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Email for PubMed */}
            {watchedSources.includes("pubmed") && (
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="flex items-center gap-2">
                      Email Address (Required for PubMed)
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>PubMed requires an email address to comply with their API usage policies. Your email is only used for API access and is not stored.</p>
                        </TooltipContent>
                      </Tooltip>
                    </FormLabel>
                    <FormControl>
                      <div className="flex gap-2">
                        <Input
                          type="email"
                          placeholder="your.email@institution.edu"
                          {...field}
                        />
                        {isValidatingEmail && (
                          <div className="flex items-center">
                            <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                          </div>
                        )}
                        {emailValidation.valid === true && (
                          <CheckCircle className="h-5 w-5 text-green-500 mt-2" />
                        )}
                        {emailValidation.valid === false && (
                          <XCircle className="h-5 w-5 text-red-500 mt-2" />
                        )}
                      </div>
                    </FormControl>
                    <FormDescription>
                      PubMed requires an email for API access compliance. This helps ensure responsible usage.
                    </FormDescription>
                    {emailValidation.message && (
                      <p className={cn(
                        "text-sm",
                        emailValidation.valid ? "text-green-600" : "text-red-600"
                      )}>
                        {emailValidation.message}
                      </p>
                    )}
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <Separator />

            {/* Research Configuration */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Output Format */}
              <FormField
                control={form.control}
                name="output_format"
                render={({ field }) => (
                  <FormItem className="space-y-3">
                    <FormLabel className="flex items-center gap-2">
                      Output Format
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Choose between concise bullet points or a comprehensive academic report with detailed analysis and literature review.</p>
                        </TooltipContent>
                      </Tooltip>
                    </FormLabel>
                    <FormControl>
                      <RadioGroup
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                        className="flex flex-col space-y-1"
                      >
                        <FormItem className="flex items-center space-x-3 space-y-0">
                          <FormControl>
                            <RadioGroupItem value="bullets" />
                          </FormControl>
                          <div className="space-y-1 leading-none">
                            <FormLabel className="font-normal">
                              Bullet Points
                            </FormLabel>
                            <p className="text-xs text-muted-foreground">
                              Concise, structured findings
                            </p>
                          </div>
                        </FormItem>
                        <FormItem className="flex items-center space-x-3 space-y-0">
                          <FormControl>
                            <RadioGroupItem value="full_report" />
                          </FormControl>
                          <div className="space-y-1 leading-none">
                            <FormLabel className="font-normal">
                              Full Academic Report
                            </FormLabel>
                            <p className="text-xs text-muted-foreground">
                              Comprehensive analysis with literature review
                            </p>
                          </div>
                        </FormItem>
                      </RadioGroup>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Research Depth */}
              <FormField
                control={form.control}
                name="research_depth"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="flex items-center gap-2">
                      Research Depth
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Controls how many sources are searched and the depth of analysis. More depth takes longer but provides more comprehensive results.</p>
                        </TooltipContent>
                      </Tooltip>
                    </FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select research depth" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="quick">
                          <div className="flex flex-col">
                            <span>Quick Overview</span>
                            <span className="text-xs text-muted-foreground">~5 sources, 2-3 minutes</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="comprehensive">
                          <div className="flex flex-col">
                            <span>Comprehensive Research</span>
                            <span className="text-xs text-muted-foreground">~15 sources, 5-7 minutes</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="deep_dive">
                          <div className="flex flex-col">
                            <span>Deep Dive Analysis</span>
                            <span className="text-xs text-muted-foreground">~30+ sources, 10-15 minutes</span>
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Controls the number of sources searched and analysis depth
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Date Range */}
            <FormField
              control={form.control}
              name="date_range"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-2">
                    Publication Date Range (Optional)
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Filter papers by publication year. Useful for finding recent research or historical analysis. Leave empty to search all years.</p>
                      </TooltipContent>
                    </Tooltip>
                  </FormLabel>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <FormLabel className="text-sm text-muted-foreground">From Year</FormLabel>
                      <Input
                        type="number"
                        min="1900"
                        max={currentYear}
                        placeholder="2020"
                        value={field.value?.start_year || ""}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => field.onChange({
                          ...field.value,
                          start_year: e.target.value ? parseInt(e.target.value) : undefined
                        })}
                      />
                    </div>
                    <div>
                      <FormLabel className="text-sm text-muted-foreground">To Year</FormLabel>
                      <Input
                        type="number"
                        min="1900"
                        max={currentYear}
                        placeholder={currentYear.toString()}
                        value={field.value?.end_year || ""}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => field.onChange({
                          ...field.value,
                          end_year: e.target.value ? parseInt(e.target.value) : undefined
                        })}
                      />
                    </div>
                  </div>
                  <FormDescription>
                    Filter papers by publication date. Leave empty for all years.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Academic Fields */}
            <FormField
              control={form.control}
              name="academic_fields"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-2">
                    Academic Fields (Optional)
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Select relevant academic disciplines to help focus the search and improve result relevance. Leave empty to search all fields.</p>
                      </TooltipContent>
                    </Tooltip>
                  </FormLabel>
                  <FormDescription>
                    Select relevant academic disciplines to focus the search
                  </FormDescription>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
                    {ACADEMIC_FIELDS.map((fieldName) => (
                      <FormItem
                        key={fieldName}
                        className="flex flex-row items-start space-x-2 space-y-0"
                      >
                        <FormControl>
                          <Checkbox
                            checked={field.value?.includes(fieldName)}
                            onCheckedChange={(checked: boolean) => {
                              return checked
                                ? field.onChange([...(field.value || []), fieldName])
                                : field.onChange(
                                    field.value?.filter((value) => value !== fieldName)
                                  )
                            }}
                          />
                        </FormControl>
                        <FormLabel className="text-sm font-normal cursor-pointer">
                          {fieldName}
                        </FormLabel>
                      </FormItem>
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Deadline */}
            <FormField
              control={form.control}
              name="deadline"
              render={({ field }) => (
                <FormItem className="flex flex-col">
                  <FormLabel className="flex items-center gap-2">
                    Deadline (Optional)
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Set a deadline for priority processing. Research jobs with deadlines are processed with higher priority.</p>
                      </TooltipContent>
                    </Tooltip>
                  </FormLabel>
                  <Popover>
                    <PopoverTrigger asChild>
                      <FormControl>
                        <Button
                          variant={"outline"}
                          className={cn(
                            "w-[240px] pl-3 text-left font-normal",
                            !field.value && "text-muted-foreground"
                          )}
                        >
                          {field.value ? (
                            format(field.value, "PPP")
                          ) : (
                            <span>Pick a date</span>
                          )}
                          <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                        </Button>
                      </FormControl>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={field.value}
                        onSelect={field.onChange}
                        disabled={(date) =>
                          date < new Date(new Date().setDate(new Date().getDate() - 1))
                        }
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                  <FormDescription>
                    Optional: Set a deadline for priority processing
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button 
              type="submit" 
              disabled={form.formState.isSubmitting}
              className="w-full"
              size="lg"
            >
              {form.formState.isSubmitting ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                  Submitting Research...
                </>
              ) : (
                <>
                  <FlaskConical className="mr-2 h-4 w-4" />
                  Start Academic Research
                </>
              )}
            </Button>
          </form>
        </Form>
      </div>
    </TooltipProvider>
  );
}