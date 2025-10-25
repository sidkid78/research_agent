'use client';

import React from 'react';
import { EnhancedResearchForm } from '@/components/ResearchForm';

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col items-center bg-background text-foreground pt-12 pb-8 px-4 sm:px-6 lg:px-8">
      <header className="w-full max-w-3xl mx-auto mb-12 text-center">
        <h1 className="text-5xl font-extrabold tracking-tight text-primary sm:text-6xl">
          Research Agent AI
        </h1>
        <p className="mt-6 text-xl text-muted-foreground">
          Uncover insights, faster. Submit your topic, and let our intelligent agent synthesize comprehensive research for you.
        </p>
      </header>
      
      <main className="w-full max-w-2xl">
        <EnhancedResearchForm />
      </main>

      <footer className="mt-auto pt-12 text-center text-sm text-muted-foreground">
        <p>&copy; {new Date().getFullYear()} Advanced Research Systems. All rights reserved.</p>
      </footer>
    </div>
  );
}
